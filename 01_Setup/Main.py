import threading
import time
import tkinter as tk
from tkinter import messagebox

# Importar módulos locales
try:
    import Main_Setup
    from Mage_Main import mage_main
    import Main_Save_Data as DataSaver
except Exception as e:
    # si hay problemas de path, intentar ajustar
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import Main_Setup
    from Mage_Main import mage_main
    try:
        import Main_Save_Data as DataSaver
    except Exception:
        DataSaver = None
        print("WARNING: Main_Save_Data no importable:", e)

# Control events para pausar / detener
class ControlEvents:
    def __init__(self):
        import threading
        self.pause_event = threading.Event()  # set = running, clear = paused
        self.stop_event = threading.Event()

# --- Nuevo: estado compartido global para contar exo attempts y clicks de runas ---
shared_state = {
    "exo_attempts": 0,
    "rune_clicks": 0,
    # configuración
    "max_clicks_per_stat": 4,   # cuántas veces intentar clicar una stat en una pasada para llevarla >0.3*min
    "min_threshold_factor": 0.3
}

# Monkeypatch helpers (se instalan justo antes de iniciar el hilo)
def install_monkeypatches():
    """
    Intenta importar módulos Mage_Introduce_Runes y Mage_Introduce_Exo y sustituir sus funciones
    por wrappers que implementan:
     - subir primero stats < 30% del min (varias clicks si procede)
     - permitir clicks repetidos por stat para ahorrar lecturas
     - contar intentos de Exo (shared_state['exo_attempts'])
     - evitar movimiento "falso" antes de introducir el exo (temporalmente neutraliza moveTo)
    Si algún módulo no está disponible, se ignora silenciosamente (compatible con entorno de pruebas).
    """
    try:
        import Mage_Introduce_Runes as MIR
        import importlib
        importlib.reload(MIR)
    except Exception as e:
        print("WARNING: No se pudo importar Mage_Introduce_Runes para parchear:", e)
        MIR = None

    try:
        import Mage_Introduce_Exo as MIE
        import importlib
        importlib.reload(MIE)
    except Exception as e:
        print("WARNING: No se pudo importar Mage_Introduce_Exo para parchear:", e)
        MIE = None

    # Wrap mage_introduce_runes: varias invocaciones dirigidas para subir stats muy bajas primero
    if MIR is not None and hasattr(MIR, "mage_introduce_runes"):
        orig_mage_introduce_runes = MIR.mage_introduce_runes

        def wrapped_mage_introduce_runes(stats_actuales, stats_min, stats_obj=None, stats_max=None):
            try:
                n = min(len(stats_min), len(stats_actuales))
                threshold_factor = shared_state.get("min_threshold_factor", 0.3)
                max_clicks = shared_state.get("max_clicks_per_stat", 4)
                # Primero: intentar subir aquellas stats que estén por debajo del 30% del mínimo
                for idx in range(n):
                    try:
                        min_val = float(stats_min[idx]) if stats_min and idx < len(stats_min) else 0
                    except Exception:
                        min_val = 0
                    if min_val > 0:
                        current = stats_actuales[idx] if idx < len(stats_actuales) else 0
                        if current < threshold_factor * min_val:
                            # Hacer hasta max_clicks invocaciones donde solo esa stat es objetivo
                            for click_round in range(max_clicks):
                                # construir min temporal: sólo esa stat mantiene su min objetivo, las demás se ponen muy altas
                                temp_min = [10**9] * n
                                temp_min[idx] = int(min_val * threshold_factor) if min_val * threshold_factor > 0 else int(min_val)
                                try:
                                    orig_mage_introduce_runes(stats_actuales, temp_min, stats_obj or [], stats_max or [])
                                    shared_state["rune_clicks"] += 1
                                except Exception as e:
                                    print("WARNING: error calling original mage_introduce_runes during pre-up:", e)
                                # si el módulo expone alguna pequeña espera interna no la duplicamos; dejamos que Mage_Main recapture si necesita
                            # terminado el bloque para esta stat, seguimos con siguientes
                # Finalmente invocar la lógica original con los valores reales para que haga la pasada normal
                orig_mage_introduce_runes(stats_actuales, stats_min, stats_obj or [], stats_max or [])
                shared_state["rune_clicks"] += 1
            except Exception as e:
                print("ERROR en wrapped_mage_introduce_runes:", e)
                # fallback a original si hay problema
                try:
                    orig_mage_introduce_runes(stats_actuales, stats_min, stats_obj or [], stats_max or [])
                except Exception:
                    pass

        MIR.mage_introduce_runes = wrapped_mage_introduce_runes
        print("DEBUG: Parche instalado en Mage_Introduce_Runes.mage_introduce_runes")

     # Nota: no parcheamos introducir_exo aquí para evitar doble conteo de intentos.
    # Contador de EXO se incrementa dentro de Mage_Introduce_Exo.introducir_exo (si puede acceder a Main.shared_state).
    # MIE.introducir_exo = wrapped_introducir_exo
    # print("DEBUG: Parche instalado en Mage_Introduce_Exo.introducir_exo")

def run_process(control_events, status_var, start_btn, stop_btn):
    """
    Orquesta en bucle: Main_Setup -> Mage_Main -> guardar con Main_Save_Data.finalize_session.
    Repite automáticamente hasta que se active stop_event.
    """
    def ui_set_start_disabled():
        try:
            start_btn.config(state="disabled")
            stop_btn.config(state="normal")
        except Exception:
            pass

    def ui_set_final_state():
        try:
            status_var.set("Idle")
            start_btn.config(state="normal")
            stop_btn.config(state="disabled")
        except Exception:
            pass

    try:
        start_btn.after(0, ui_set_start_disabled)
    except Exception:
        pass

    # Instalar parches antes de empezar bucle
    try:
        install_monkeypatches()
    except Exception as e:
        print("WARNING: install_monkeypatches falló:", e)

    # Bucle principal: repetir mientras no se solicite stop
    while not control_events.stop_event.is_set():
        status_var.set("Preparando Setup...")
        try:
            # 1) Setup: obtener item_name y stats
            status_var.set("Ejecutando Setup...")
            item_info = Main_Setup.main()
            if isinstance(item_info, tuple) and len(item_info) >= 2:
                item_name, item_stats = item_info[0], item_info[1]
            else:
                item_stats = item_info
                item_name = getattr(item_stats, "get", lambda k, d=None: d)("name", "Item_NoName")
        except Exception as e:
            print("ERROR en Setup:", e)
            status_var.set("Error en Setup")
            break

        # reset counters al inicio de cada ciclo
        shared_state["exo_attempts"] = 0
        shared_state["rune_clicks"] = 0

        # 2) Guardar kamas iniciales
        if DataSaver is not None:
            try:
                status_var.set("Guardando kamas iniciales...")
                DataSaver.save_initial_kamas(item_name)
            except Exception as e:
                print("WARNING: save_initial_kamas falló:", e)

        # 3) Ejecutar mage_main (pasa control_events)
        status_var.set("Ejecutando Mage_Main...")
        try:
            result = mage_main(
                item_name,
                item_stats,
                control_events={'pause_event': control_events.pause_event, 'stop_event': control_events.stop_event}
            )
        except Exception as e:
            print("ERROR en Mage_Main:", e)
            result = {"success": False, "attempts": 0, "elapsed": 0.0, "time_per_attempt": None, "error": repr(e)}

        # Interpretar resultado
        success_flag = result.get("success", False) if isinstance(result, dict) else False
        error_code = result.get("error", None) if isinstance(result, dict) else None
        time_per_attempt = result.get("time_per_attempt", None) if isinstance(result, dict) else None

        # Intentos a guardar: SOLO desde contador de exo (introducir_exo)
        attempts_to_save = shared_state.get("exo_attempts", 0)
        # Nota: si no ha habido ningún intento de exo, attempts_to_save puede ser 0 (se respeta)

        # 4) Comportamiento específico: si no_progress -> guardar fallo, popup y TERMINAR el bucle
        if error_code == "no_progress":
            print("DEBUG: No progress detectado (sin runas). Guardando como fallo y deteniendo.")
            if DataSaver is not None:
                try:
                    status_var.set("Guardando fallo (sin runas)...")
                    saved = DataSaver.finalize_session(
                        objeto=item_name,
                        intentos=attempts_to_save,
                        exito=0,
                        tiempo_medio_intento=time_per_attempt,
                        modo_encadenado_activo=True,
                        precio_objeto_base=None,
                        precio_venta_objeto_final=None,
                        tipo_exo=None,
                        kamas_iniciales_arg=None
                    )
                    print(f"DEBUG_SAVEFLOW: guardado fallo no_progress saved={saved} attempts_saved={attempts_to_save}")
                except Exception as e:
                    print("ERROR al guardar fallo (no_progress):", e)
                    status_var.set("Error al guardar fallo")
            # Mostrar ventana emergente informando y terminar (usar start_btn.after para UI-thread)
            try:
                start_btn.after(0, lambda: messagebox.askyesno("Sin runas", "No quedan runas. ¿Continuar (guardar fallo) o Detener?"))
            except Exception:
                print("Aviso: no se pudo mostrar popup 'Sin runas' (posible entorno no gráfico).")
            # No continuar con setup: salir del bucle principal
            break

        # 5) Si éxito: guardar éxito (sin popups) y continuar con siguiente ciclo (setup)
        if success_flag:
            print("DEBUG: Éxito PA detectado. Guardando éxito y continuando con siguiente ciclo de setup.")
            if DataSaver is not None:
                try:
                    status_var.set("Guardando éxito...")
                    saved = DataSaver.finalize_session(
                        objeto=item_name,
                        intentos=attempts_to_save,
                        exito="PA",
                        tiempo_medio_intento=time_per_attempt,
                        modo_encadenado_activo=True,
                        precio_objeto_base=None,
                        precio_venta_objeto_final=None,
                        tipo_exo="PA",
                        kamas_iniciales_arg=None
                    )
                    print(f"DEBUG_SAVEFLOW: guardado éxito saved={saved} attempts_saved={attempts_to_save}")
                except Exception as e:
                    print("ERROR al guardar éxito:", e)
                    status_var.set("Error al guardar éxito")
            # No mostrar ventanas; continuar a la siguiente iteración (nuevo setup)
            if control_events.stop_event.is_set():
                print("Stop solicitado tras éxito: saliendo.")
                break
            # pequeña espera antes de reiniciar
            time.sleep(0.5)
            continue

        # 6) Otros casos (error distinto o simple fallo): guardar como fallo pero continuar el bucle
        print("DEBUG: Resultado intermedio/no-exito sin 'no_progress'. Guardando como fallo y continuando.")
        if DataSaver is not None:
            try:
                status_var.set("Guardando fallo...")
                saved = DataSaver.finalize_session(
                    objeto=item_name,
                    intentos=attempts_to_save,
                    exito=0,
                    tiempo_medio_intento=time_per_attempt,
                    modo_encadenado_activo=True,
                    precio_objeto_base=None,
                    precio_venta_objeto_final=None,
                    tipo_exo=None,
                    kamas_iniciales_arg=None
                )
                print(f"DEBUG_SAVEFLOW: guardado fallback saved={saved} attempts_saved={attempts_to_save}")
            except Exception as e:
                print("ERROR al guardar fallback:", e)
                status_var.set("Error al guardar")
        else:
            status_var.set("DataSaver no disponible - no guardado.")

        # Si stop fue solicitado durante la ejecución de mage_main o guardado, salir del bucle
        if control_events.stop_event.is_set():
            print("Stop solicitado: saliendo del bucle principal.")
            break

        # Pequeña pausa antes de reiniciar para permitir estabilizar UI/ventana
        time.sleep(0.5)
        # continua el bucle -> nuevo setup y magueo

    # Finalizar y restaurar UI
    try:
        start_btn.after(0, ui_set_final_state)
    except Exception:
        pass

    # Reset eventos y contadores por si se reinicia manualmente después
    control_events.stop_event.clear()
    control_events.pause_event.set()
    shared_state["exo_attempts"] = 0
    shared_state["rune_clicks"] = 0

# ---------------------- UI mejorada oscura ----------------------
def build_ui():
    import tkinter.ttk as ttk

    root = tk.Tk()
    root.title("Forjamagia - Orquestador")
    root.geometry("540x300")
    root.resizable(False, False)

    style = ttk.Style(root)
    # Intentar tema moderno; si no está, usar default y ajustar colores
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Paleta oscura
    BG = "#1f1f1f"
    FG = "#e6e6e6"
    ACCENT = "#4a90e2"
    BTN_BG = "#2b2b2b"
    root.configure(bg=BG)

    frame_top = ttk.Frame(root, padding=(12, 10))
    frame_top.pack(fill="x")
    frame_top.configure(style="My.TFrame")

    title = ttk.Label(frame_top, text="Forjamagia - Orquestador", font=("Segoe UI", 14, "bold"), foreground=FG, background=BG)
    title.pack(anchor="w")

    status_var = tk.StringVar(value="Idle")
    status_lbl = ttk.Label(frame_top, textvariable=status_var, font=("Segoe UI", 11), foreground=FG, background=BG)
    status_lbl.pack(anchor="w", pady=(6, 0))

    frame_controls = ttk.Frame(root, padding=(12, 8))
    frame_controls.pack(fill="x")

    control_events = ControlEvents()
    control_events.pause_event.set()  # empezar en estado running

    # Log area
    frame_log = ttk.LabelFrame(root, text="Log", padding=(8, 8))
    frame_log.pack(fill="both", expand=True, padx=12, pady=(6,12))
    # aplicar estilos oscuros al Text
    log_text = tk.Text(frame_log, height=8, wrap="word", bg="#0f0f0f", fg=FG, insertbackground=FG)
    log_text.pack(fill="both", expand=True)

    def log(msg):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}\n"
        log_text.config(state="normal")
        log_text.insert("end", entry)
        log_text.see("end")
        log_text.config(state="disabled")

    # Buttons (crearlos primero sin comando y luego asignar)
    start_btn = ttk.Button(frame_controls, text="Iniciar", width=14)
    pause_btn = ttk.Button(frame_controls, text="Pausar (F9)", width=16)
    stop_btn = ttk.Button(frame_controls, text="Parar y Guardar (F10)", width=18, state="disabled")

    start_btn.grid(row=0, column=0, padx=8, pady=6)
    pause_btn.grid(row=0, column=1, padx=8, pady=6)
    stop_btn.grid(row=0, column=2, padx=8, pady=6)

    worker_thread = {"thread": None}

    def start_clicked():
        if worker_thread["thread"] and worker_thread["thread"].is_alive():
            messagebox.showinfo("Info", "Proceso ya en ejecución.")
            return
        control_events.stop_event.clear()
        control_events.pause_event.set()
        status_var.set("Preparando...")
        log("Pulsado Iniciar")
        t = threading.Thread(target=run_process, args=(control_events, status_var, start_btn, stop_btn), daemon=True)
        worker_thread["thread"] = t
        t.start()
        start_btn.state(["disabled"])
        stop_btn.state(["!disabled"])
        pause_btn.state(["!disabled"])
        pause_btn.config(text="Pausar (F9)")
        log("Hilo iniciado")

    def pause_toggle(event=None):
        if control_events.pause_event.is_set():
            control_events.pause_event.clear()
            status_var.set("Pausado")
            pause_btn.config(text="Reanudar (F9)")
            log("Pausado")
        else:
            control_events.pause_event.set()
            status_var.set("Reanudando...")
            pause_btn.config(text="Pausar (F9)")
            log("Reanudado")

    def stop_clicked(event=None):
        control_events.stop_event.set()
        control_events.pause_event.set()  # asegurar que no esté pausado para permitir salida
        status_var.set("Parando y guardando...")
        log("Solicitada parada (F10 / Parar)")
        stop_btn.state(["disabled"])
        pause_btn.state(["disabled"])

    # Asignar comandos a botones
    start_btn.config(command=start_clicked)
    pause_btn.config(command=pause_toggle)
    stop_btn.config(command=stop_clicked)

    # Bind global keys (captura aunque el foco esté en widgets)
    root.bind_all('<F9>', lambda e: pause_toggle())
    root.bind_all('<F10>', lambda e: stop_clicked())

    # Manejo de cierre de ventana
    def on_close():
        if worker_thread["thread"] and worker_thread["thread"].is_alive():
            if messagebox.askyesno("Confirmar", "Hay un proceso en ejecución. ¿Parar y salir (se guardarán datos)?"):
                stop_clicked()
                # dar tiempo a que el hilo termine/guarde (no bloqueante)
                root.after(2000, root.destroy)
            else:
                return
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Center window on screen
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()

if __name__ == "__main__":
    build_ui()
