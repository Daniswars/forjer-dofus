import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Importar módulos locales
try:
    import Main_Setup
    import Setup_Item_Stats_Database
    from Mage_Main import mage_main
    import Main_Save_Data as DataSaver
except Exception as e:
    # si hay problemas de path, intentar ajustar
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import Main_Setup
    import Setup_Item_Stats_Database
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
    "min_threshold_factor": 0.3,
    "current_item": None        # nombre del item actualmente en proceso (para notificaciones)
}

# Importar correo para notificaciones desde aquí (opcional)
try:
    import Extra_Correo as Correo
except Exception:
    Correo = None

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

    # --- NUEVO: wrap introducir_exo para contar intentos EXO una sola vez por ejecución ---
    if MIE is not None and hasattr(MIE, "introducir_exo"):
        orig_introducir_exo = MIE.introducir_exo

        def wrapped_introducir_exo(*args, **kwargs):
            """
            Incrementa shared_state['exo_attempts'] en el momento de la llamada (cuenta invocaciones),
            y luego llama a la función original introducir_exo.
            Esto asegura que se contabilice la llamada aunque devuelva False o lance excepción.
            """
            # Incrementar al entrar (contar la invocación)
            try:
                shared_state["exo_attempts"] = int(shared_state.get("exo_attempts", 0)) + 1
                print(f"DEBUG: exo_attempts incrementado (on call) -> {shared_state['exo_attempts']}")
            except Exception as e:
                print("WARNING: no se pudo incrementar shared_state['exo_attempts'] al iniciar la llamada:", e)

            # Si se alcanza un múltiplo de 10, enviar notificación (no bloquear si falla)
            try:
                if shared_state.get("exo_attempts", 0) % 10 == 0:
                    current_item = shared_state.get("current_item", "") or ""
                    if Correo is not None:
                        try:
                            Correo.send_mail(current_item, "10 intentos exo PA")
                            print(f"DEBUG: enviado correo por 10 intentos para '{current_item}' (contador={shared_state['exo_attempts']})")
                        except Exception as e_mail:
                            print("WARNING: fallo al enviar correo de 10 intentos:", e_mail)
                    else:
                        print("DEBUG: Extra_Correo no disponible, no se envió correo de 10 intentos.")
            except Exception as e:
                print("WARNING: error al comprobar/enviar notificación cada 10 intentos:", e)

            # Llamar a la función original y propagar excepciones si ocurren
            try:
                result = orig_introducir_exo(*args, **kwargs)
            except Exception as e:
                print("WARNING: introducir_exo lanzó excepción:", e)
                # ya hemos contado la llamada; reenviamos la excepción para que el flujo superior la gestione
                raise
            return result

        MIE.introducir_exo = wrapped_introducir_exo
        print("DEBUG: Parche instalado en Mage_Introduce_Exo.introducir_exo (conteo EXO)")

def run_process(control_events, status_var, start_btn, stop_btn):
    """
    Orquesta en bucle: Main_Setup -> Mage_Main -> guardar con Main_Save_Data.finalize_session.
    Repite automáticamente hasta que se active stop_event.
    """
    def ui_set_start_disabled():
        try:
            start_btn.configure(state="disabled")
            stop_btn.configure(state="normal")
        except Exception:
            pass

    def ui_set_final_state():
        try:
            status_var.set("Idle")
            start_btn.configure(state="normal")
            stop_btn.configure(state="disabled")
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
        # asignar current item para que el wrapper lo use en notificaciones
        shared_state["current_item"] = item_name

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

        # --- NUEVA LÓGICA: normalizar result y obtener elapsed/attempts/time_per_attempt ---
        if not isinstance(result, dict):
            result = {"success": False, "attempts": 0, "elapsed": 0.0, "time_per_attempt": None, "error": None}

        elapsed = result.get("elapsed", 0.0)
        time_per_attempt = result.get("time_per_attempt", None)

        # attempts: preferimos shared_state (actualizado por el wrapper) si está disponible y es entero >=0
        try:
            attempts_to_save = int(shared_state.get("exo_attempts", 0))
        except Exception:
            attempts_to_save = int(result.get("attempts", 0) or 0)

        # si no tenemos time_per_attempt calculado y hay attempts, calcularlo aquí
        if time_per_attempt is None and attempts_to_save > 0:
            try:
                time_per_attempt = float(elapsed) / attempts_to_save
            except Exception:
                time_per_attempt = None

        # Flags para las ramas siguientes
        error_code = result.get("error")
        success_flag = bool(result.get("success", False))

        # 4) Comportamiento específico: si no_progress -> guardar fallo, popup y decidir continuar o terminar
        if error_code == "no_progress":
            print("DEBUG: No progress detectado (sin runas). Guardando como fallo.")
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
                    print(f"DEBUG_SAVEFLOW: guardado fallo no_progress saved={saved} attempts_saved={attempts_to_save} time_per_attempt={time_per_attempt}")
                except Exception as e:
                    print("ERROR al guardar fallo (no_progress):", e)
                    status_var.set("Error al guardar fallo")

            # Mostrar ventana emergente en el hilo de la UI y esperar la respuesta del usuario.
            # Usamos start_btn.after para lanzar el dialog en el hilo principal y threading.Event para sincronizar.
            import threading
            response = {"val": None}
            response_event = threading.Event()

            def ask_continue_dialog():
                try:
                    ans = messagebox.askyesno("Sin runas", "No quedan runas PA. ¿Continuar (omitir este objeto) ?\n\nSi eliges 'No' se detendrá la ejecución.")
                    response["val"] = bool(ans)
                except Exception:
                    response["val"] = False
                finally:
                    response_event.set()

            try:
                # lanzar diálogo en UI thread
                start_btn.after(0, ask_continue_dialog)
                # esperar respuesta (esto bloquea el hilo worker pero no la UI)
                response_event.wait()
            except Exception as e:
                print("Aviso: no se pudo mostrar diálogo de 'Sin runas' (entorno no gráfico?):", e)
                response["val"] = False

            user_chose_continue = bool(response.get("val", False))
            if user_chose_continue:
                print("Usuario eligió continuar tras 'Sin runas'. Se reanuda el bucle principal.")
                status_var.set("Usuario eligió continuar (sin runas).")
                # continuar con el bucle principal (no ejecutar setup-stop)
                # pequeña pausa para estabilizar UI
                time.sleep(0.3)
                continue
            else:
                print("Usuario eligió detener tras 'Sin runas'. Terminando bucle.")
                status_var.set("Detenido por usuario tras 'Sin runas'.")
                # salir del bucle principal
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
                    print(f"DEBUG_SAVEFLOW: guardado éxito saved={saved} attempts_saved={attempts_to_save} time_per_attempt={time_per_attempt}")
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

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Forjamagia - Orquestador")
    root.geometry("760x480")
    root.resizable(True, True)

    FG = "#e6e6e6"

    frame_top = ctk.CTkFrame(root, corner_radius=8)
    frame_top.pack(fill="x", padx=12, pady=10)

    title = ctk.CTkLabel(frame_top, text="Forjamagia - Orquestador", font=("Segoe UI", 18, "bold"))
    title.pack(anchor="w", padx=10, pady=(8, 0))

    status_var = tk.StringVar(value="Idle")
    status_lbl = ctk.CTkLabel(frame_top, textvariable=status_var, font=("Segoe UI", 13))
    status_lbl.pack(anchor="w", padx=10, pady=(6, 8))

    frame_controls = ctk.CTkFrame(root, corner_radius=8)
    frame_controls.pack(fill="x", padx=12)

    control_events = ControlEvents()
    control_events.pause_event.set()

    # Log area
    frame_log = ctk.CTkFrame(root, corner_radius=8)
    frame_log.pack(fill="both", expand=True, padx=12, pady=(8, 12))
    log_text = ctk.CTkTextbox(frame_log, height=200)
    log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def log(msg):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}\n"
        log_text.configure(state="normal")
        log_text.insert("end", entry)
        log_text.see("end")
        log_text.configure(state="disabled")

    start_btn = ctk.CTkButton(frame_controls, text="Iniciar", width=160, height=36, font=("Segoe UI", 12))
    pause_btn = ctk.CTkButton(frame_controls, text="Pausar (F9)", width=170, height=36, font=("Segoe UI", 12))
    stop_btn = ctk.CTkButton(frame_controls, text="Parar y Guardar (F10)", width=210, height=36, font=("Segoe UI", 12))
    stop_btn.configure(state="disabled")

    start_btn.grid(row=0, column=0, padx=10, pady=14)
    pause_btn.grid(row=0, column=1, padx=10, pady=14)
    stop_btn.grid(row=0, column=2, padx=10, pady=14)

    def open_db_editor():
        # Editor sencillo: búsqueda + lista de items + subir/bajar stats + guardar
        stats_db = Setup_Item_Stats_Database.load_item_stats_txt()
        if not isinstance(stats_db, dict):
            stats_db = {}

        editor = ctk.CTkToplevel(root)
        editor.title("Editor de Item Stats (TXT)")
        editor.geometry("760x420")
        editor.grab_set()

        top = ctk.CTkFrame(editor)
        top.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(top, text="Buscar:").pack(side="left", padx=(6, 6))
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(top, textvariable=search_var, width=200)
        search_entry.pack(side="left")

        body = ctk.CTkFrame(editor)
        body.pack(fill="both", expand=True, padx=12, pady=6)

        # Lista de items
        items_list = tk.Listbox(body, height=14)
        items_list.grid(row=0, column=0, rowspan=3, padx=(8, 6), pady=8, sticky="ns")

        # Lista de stats
        stats_list = tk.Listbox(body, height=14, width=40)
        stats_list.grid(row=0, column=1, rowspan=3, padx=6, pady=8, sticky="nsew")

        body.grid_columnconfigure(1, weight=1)

        form = ctk.CTkFrame(body)
        form.grid(row=0, column=2, padx=8, pady=8, sticky="n")
        ctk.CTkLabel(form, text="obj").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(form, text="min").grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(form, text="max").grid(row=2, column=0, sticky="w")
        obj_var = tk.StringVar()
        min_var = tk.StringVar()
        max_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=obj_var, width=120).grid(row=0, column=1, pady=2)
        ctk.CTkEntry(form, textvariable=min_var, width=120).grid(row=1, column=1, pady=2)
        ctk.CTkEntry(form, textvariable=max_var, width=120).grid(row=2, column=1, pady=2)

        current_item = {"name": None, "rows": []}

        def refresh_items():
            items_list.delete(0, "end")
            q = search_var.get().strip().lower()
            for name in sorted(stats_db.keys()):
                if not q or q in name.lower():
                    items_list.insert("end", name)

        def load_item(name):
            stats_list.delete(0, "end")
            if not name or name not in stats_db:
                return
            s = stats_db[name]
            rows = []
            for i, obj in enumerate(s.get("obj", [])):
                mn = s.get("min", [])[i] if i < len(s.get("min", [])) else 0
                mx = s.get("max", [])[i] if i < len(s.get("max", [])) else 0
                rows.append([obj, mn, mx])
            current_item["name"] = name
            current_item["rows"] = rows
            for r in rows:
                stats_list.insert("end", f"{r[0]} | {r[1]} | {r[2]}")

        def on_item_select(evt=None):
            sel = items_list.curselection()
            if not sel:
                return
            name = items_list.get(sel[0])
            load_item(name)

        def on_stat_select(evt=None):
            sel = stats_list.curselection()
            if not sel:
                return
            idx = sel[0]
            try:
                obj_var.set(current_item["rows"][idx][0])
                min_var.set(str(current_item["rows"][idx][1]))
                max_var.set(str(current_item["rows"][idx][2]))
            except Exception:
                pass

        def update_row():
            sel = stats_list.curselection()
            if not sel:
                return
            idx = sel[0]
            try:
                obj = obj_var.get().strip()
                mn = int(min_var.get().strip() or "0")
                mx = int(max_var.get().strip() or "0")
                current_item["rows"][idx] = [obj, mn, mx]
                stats_list.delete(idx)
                stats_list.insert(idx, f"{obj} | {mn} | {mx}")
            except Exception:
                messagebox.showwarning("Error", "Valores inválidos.")

        def move_row(delta):
            sel = stats_list.curselection()
            if not sel:
                return
            i = sel[0]
            j = i + delta
            if j < 0 or j >= len(current_item["rows"]):
                return
            rows = current_item["rows"]
            rows[i], rows[j] = rows[j], rows[i]
            load_item(current_item["name"])
            stats_list.selection_set(j)
            on_stat_select()

        def save_db():
            name = current_item["name"]
            if not name:
                return
            rows = current_item["rows"]
            stats_db[name] = {
                "obj": [r[0] for r in rows],
                "min": [r[1] for r in rows],
                "max": [r[2] for r in rows],
            }
            Setup_Item_Stats_Database.save_item_stats_txt(stats_db)
            messagebox.showinfo("Guardado", "DB guardada en TXT.")
            refresh_items()

        items_list.bind("<<ListboxSelect>>", on_item_select)
        stats_list.bind("<<ListboxSelect>>", on_stat_select)
        search_entry.bind("<KeyRelease>", lambda e: refresh_items())

        btns = ctk.CTkFrame(editor)
        btns.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(btns, text="Actualizar fila", command=update_row).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Subir", command=lambda: move_row(-1)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Bajar", command=lambda: move_row(1)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Guardar TXT", command=save_db).pack(side="right", padx=6)

        refresh_items()

    edit_btn = ctk.CTkButton(frame_controls, text="Editar DB", width=140, height=36, font=("Segoe UI", 12), command=open_db_editor)
    edit_btn.grid(row=0, column=3, padx=10, pady=14)

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
        start_btn.configure(state="disabled")
        stop_btn.configure(state="normal")
        pause_btn.configure(state="normal")
        pause_btn.configure(text="Pausar (F9)")
        log("Hilo iniciado")

    def pause_toggle(event=None):
        if control_events.pause_event.is_set():
            control_events.pause_event.clear()
            status_var.set("Pausado")
            pause_btn.configure(text="Reanudar (F9)")
            log("Pausado")
        else:
            control_events.pause_event.set()
            status_var.set("Reanudando...")
            pause_btn.configure(text="Pausar (F9)")
            log("Reanudado")

    def stop_clicked(event=None):
        control_events.stop_event.set()
        control_events.pause_event.set()
        status_var.set("Parando y guardando...")
        log("Solicitada parada (F10 / Parar)")
        stop_btn.configure(state="disabled")
        pause_btn.configure(state="disabled")

    # Asignar comandos a botones
    start_btn.configure(command=start_clicked)
    pause_btn.configure(command=pause_toggle)
    stop_btn.configure(command=stop_clicked)

    # Bind global keys (captura aunque el foco esté en widgets)
    root.bind_all('<F9>', lambda e: pause_toggle())
    root.bind_all('<F10>', lambda e: stop_clicked())

    # Intentar registrar hotkeys globales con la librería `keyboard` (mejor para teclados que no envían F9 a la ventana)
    try:
        import keyboard  # pip install keyboard (requiere permisos en Windows)
        try:
            keyboard.add_hotkey('f9', pause_toggle)
            keyboard.add_hotkey('f10', stop_clicked)
            log("Hotkeys globales registrados: F9 (pausa), F10 (parar).")
        except Exception as e:
            log(f"Imposible registrar hotkeys globales (keyboard.add_hotkey): {e}")
    except Exception as e:
        # Si keyboard no está instalado, seguir con bind_all (funciona cuando la ventana tiene foco)
        log("Módulo 'keyboard' no disponible: F9/F10 sólo funcionarán con la ventana activa.")

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
