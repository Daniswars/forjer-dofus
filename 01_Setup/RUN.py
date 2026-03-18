import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog  # <-- NUEVO: para diálogos de entrada
import customtkinter as ctk

# Importar módulos locales
try:
    import Main_Setup
    import Setup_Item_Stats_Database
    from Mage_Main import mage_main
    import Main_Save_Data as DataSaver
    # NUEVO: importar helper de reseteo de sesión
    try:
        import Aux_Resetear_sesion as SessionReset
    except Exception:
        SessionReset = None
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
    # NUEVO: intentar importar el helper de reseteo también en el fallback
    try:
        import Aux_Resetear_sesion as SessionReset
    except Exception:
        SessionReset = None

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
    "max_clicks_per_stat": 4,
    "min_threshold_factor": 0.3,
    "current_item": None,
    # NUEVO: reset diferido al siguiente intento de EXO
    "pending_session_reset": False,
    # NUEVO: inicio de sesión magueando (persistente entre éxitos/ciclos)
    "session_started_at": None,
    # NUEVO: métricas reales entre intentos EXO
    "last_exo_attempt_at": None,
    "exo_attempt_elapsed_sum": 0.0
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
                # NUEVO: medir tiempo real entre intentos de introducir EXO
                now = time.monotonic()
                prev = shared_state.get("last_exo_attempt_at")
                if isinstance(prev, (int, float)):
                    dt = now - prev
                    if dt > 0:
                        shared_state["exo_attempt_elapsed_sum"] = float(shared_state.get("exo_attempt_elapsed_sum", 0.0)) + dt
                shared_state["last_exo_attempt_at"] = now

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
    Repite automáticamente hasta que se activa stop_event.
    """

    def ui_set_start_disabled():
        try:
            start_btn.configure(state="disabled")
            stop_btn.configure(state="normal")
        except Exception:
            pass

    def ui_set_final_state():
        try:
            status_var.set("v3.20")
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

    # --- Añadido: logger local accesible dentro de run_process ---
    def log(msg):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        try:
            # intentar actualizar status_var si está disponible
            status_var.set(msg)
        except Exception:
            pass
        # imprimir siempre a stdout para debug en consola/hilos
        try:
            print(entry)
        except Exception:
            pass

    # INICIALIZAR temporizador de reseteo de sesión (30 minutos) usando monotonic
    last_session_reset_time = time.monotonic()
    SESSION_RESET_INTERVAL = 30 * 60  # 30 minutos

    # NUEVO: inicializar reloj de sesión SOLO una vez
    if not isinstance(shared_state.get("session_started_at"), (int, float)):
        shared_state["session_started_at"] = time.monotonic()

    # Bucle principal: repetir mientras no se solicite stop
    while not control_events.stop_event.is_set():
        # NUEVO: solo marcar reset pendiente por tiempo, NO ejecutarlo aquí
        try:
            elapsed_since_reset = time.monotonic() - last_session_reset_time
            if elapsed_since_reset >= SESSION_RESET_INTERVAL:
                shared_state["pending_session_reset"] = True
                log(f"Se marca reset pendiente ({int(elapsed_since_reset)}s). Se ejecutará en el siguiente intento de EXO.")
                # evitar spam de logs/re-marcado continuo
                last_session_reset_time = time.monotonic()
        except Exception as e:
            print("WARNING: fallo marcando pending_session_reset:", e)

        # --- Resto del bucle existente (Setup, Mage_Main, etc.) ---
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
        # NUEVO: reset métricas de tiempo entre intentos EXO por ciclo/item
        shared_state["last_exo_attempt_at"] = None
        shared_state["exo_attempt_elapsed_sum"] = 0.0
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
        # ...eliminar start_mage_time por ciclo...
        try:
            result = mage_main(
                item_name,
                item_stats,
                control_events={'pause_event': control_events.pause_event, 'stop_event': control_events.stop_event}
            )
        except Exception as e:
            print("ERROR en Mage_Main:", e)
            result = {"success": False, "attempts": 0, "elapsed": 0.0, "time_per_attempt": None, "error": repr(e)}

        # NUEVO: manejo centralizado cuando Mage_Main pide reset al siguiente EXO
        try:
            if isinstance(result, dict) and result.get("error") == "session_reset_pending_exo":
                log("Mage_Main solicita reset en intento de EXO: leyendo/guardando kamas finales y reseteando sesión.")
                current_item = shared_state.get("current_item", "") or item_name

                # click estratégico previo
                try:
                    import pyautogui as _pag
                    _pag.moveTo(2697, 1075, duration=0.06)
                    _pag.click()
                    time.sleep(0.25)
                    _pag.click()
                    time.sleep(0.25)
                except Exception as e_click:
                    log(f"WARNING: click estratégico falló: {e_click}")

                kamas_finales = None
                try:
                    import Extra_get_kamas as KamasModule
                    for k_attempt in range(3):
                        val = KamasModule.get_kamas()
                        log(f"Lectura kamas (reset diferido) intento {k_attempt+1}: {val}")
                        if isinstance(val, int) and val > 0:
                            kamas_finales = val
                            break
                        time.sleep(0.6)
                except Exception as e_k:
                    log(f"WARNING: no se pudieron leer kamas finales: {e_k}")

                attempts_now = int(shared_state.get("exo_attempts", 0))

                if kamas_finales is not None:
                    try:
                        import Extra_Database as DB
                        DB.agregar_datos(
                            objeto_seleccionado=current_item or "Unknown_Item_Before_Reset",
                            intentos=attempts_now,
                            kamas_iniciales=None,
                            kamas_finales=kamas_finales,
                            exito=0,
                            tiempo_medio_intento=None,
                            modo_encadenado_activo=True
                        )
                        log(f"Kamas finales guardadas antes de reset: {kamas_finales}")
                    except Exception as e_db:
                        log(f"WARNING: guardado DB falló: {e_db}")

                log("Esperando 5s antes del reset...")
                time.sleep(5.0)

                reset_ok = False
                try:
                    if SessionReset is not None and hasattr(SessionReset, "restart_dofus_and_click_forge"):
                        reset_ok = bool(SessionReset.restart_dofus_and_click_forge(current_item))
                        log(f"restart_dofus_and_click_forge -> {reset_ok}")
                    else:
                        log("SessionReset no disponible.")
                except Exception as e_rs:
                    log(f"ERROR reset sesión: {e_rs}")

                # limpiar estado y forzar setup post-reset para banco/workbench
                shared_state["pending_session_reset"] = False
                shared_state["exo_attempts"] = 0
                shared_state["rune_clicks"] = 0
                last_session_reset_time = time.monotonic()
                # CLAVE: reiniciar reloj de sesión SOLO cuando hay reset real/intento de reset
                shared_state["session_started_at"] = time.monotonic()

                try:
                    log("Ejecutando Setup post-reset (banco/workbench)...")
                    new_setup = Main_Setup.main()
                    if isinstance(new_setup, tuple) and len(new_setup) >= 2:
                        shared_state["current_item"] = new_setup[0]
                        log(f"Setup post-reset OK: {new_setup[0]}")
                except Exception as e_setup:
                    log(f"WARNING: Setup post-reset falló: {e_setup}")

                time.sleep(1.0)
                continue
        except Exception as e:
            log(f"WARNING: manejo reset diferido falló: {e}")

        # --- UNIFICACIÓN: obtener valores definitivos para guardado ---
        # 1. elapsed real de sesión (persistente; NO se reinicia por éxito PA)
        try:
            session_started_at = shared_state.get("session_started_at")
            if not isinstance(session_started_at, (int, float)):
                session_started_at = time.monotonic()
                shared_state["session_started_at"] = session_started_at
            elapsed_real = time.monotonic() - session_started_at
        except Exception:
            elapsed_real = 0.0

        # 2. attempts: SIEMPRE desde shared_state (única fuente de verdad)
        try:
            attempts_to_save = int(shared_state.get("exo_attempts", 0))
        except Exception:
            attempts_to_save = 0

        # 3. time_per_attempt: calculado aquí una sola vez
        # ANTES: elapsed_real / attempts_to_save (mezclaba tiempo de sesión/reset)
        # AHORA: promedio real entre llamadas a introducir_exo
        try:
            exo_elapsed_sum = float(shared_state.get("exo_attempt_elapsed_sum", 0.0))
        except Exception:
            exo_elapsed_sum = 0.0

        if attempts_to_save > 1 and exo_elapsed_sum > 0:
            # n intentos generan n-1 intervalos entre intentos
            time_per_attempt = exo_elapsed_sum / (attempts_to_save - 1)
        elif attempts_to_save == 1:
            time_per_attempt = None
        else:
            time_per_attempt = None

        # 4. Flags de resultado
        error_code = result.get("error")
        success_flag = bool(result.get("success", False))

        print(f"DEBUG_SAVEFLOW: elapsed={elapsed_real:.2f}s attempts={attempts_to_save} time_per_attempt={time_per_attempt}")

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
                    print(f"DEBUG_SAVEFLOW: guardado fallo no_progress saved={saved}")
                except Exception as e:
                    print("ERROR al guardar fallo (no_progress):", e)
                    status_var.set("Error al guardar fallo")

            # Mostrar ventana emergente y esperar respuesta
            import threading
            response = {"val": None}
            response_event = threading.Event()

            def ask_continue_dialog():
                try:
                    ans = messagebox.askyesno("Sin runas", "No quedan runas PA. ¿Continuar (omitir este objeto)?\n\nSi eliges 'No' se detendrá la ejecución.")
                    response["val"] = bool(ans)
                except Exception:
                    response["val"] = False
                finally:
                    response_event.set()

            try:
                start_btn.after(0, ask_continue_dialog)
                response_event.wait()
            except Exception as e:
                print("Aviso: no se pudo mostrar diálogo de 'Sin runas':", e)
                response["val"] = False

            user_chose_continue = bool(response.get("val", False))
            if user_chose_continue:
                print("Usuario eligió continuar tras 'Sin runas'.")
                status_var.set("Continuando (sin runas).")
                time.sleep(0.3)
                continue
            else:
                print("Usuario eligió detener tras 'Sin runas'.")
                status_var.set("Detenido por usuario.")
                break

        # 5) Si éxito: guardar éxito y continuar automáticamente
        if success_flag:
            print("DEBUG: Éxito PA detectado. Guardando éxito.")
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
                    print(f"DEBUG_SAVEFLOW: guardado éxito saved={saved}")

                    # Ejecutar Aux_Guardar_exito solo si guardado fue exitoso
                    if saved in (0, True):
                        try:
                            import Aux_Guardar_exito as Aux
                            log("Ejecutando secuencia de guardado de éxito...")
                            Aux.perform_dofus_sequence()
                            log("Secuencia de guardado completada.")
                        except Exception as e:
                            print("ERROR al ejecutar Aux_Guardar_exito:", e)
                            log(f"Error en secuencia de guardado: {e}")

                except Exception as e:
                    print("ERROR al guardar éxito:", e)
                    status_var.set("Error al guardar éxito")

            # Continuar automáticamente al siguiente setup
            if control_events.stop_event.is_set():
                print("Stop solicitado tras éxito: saliendo.")
                break
            time.sleep(0.5)
            continue

        # 6) Otros casos: guardar como fallo y continuar
        print("DEBUG: Resultado no-éxito sin 'no_progress'. Guardando como fallo.")
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
                print(f"DEBUG_SAVEFLOW: guardado fallback saved={saved}")
            except Exception as e:
                print("ERROR al guardar fallback:", e)
                status_var.set("Error al guardar")

        if control_events.stop_event.is_set():
            print("Stop solicitado: saliendo.")
            break

        time.sleep(0.5)
        # Continuar bucle -> nuevo setup

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
    # aspecto más "futurista" (usar tema oscuro y acento azul oscuro)
    try:
        ctk.set_default_color_theme("dark-blue")
    except Exception:
        ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Forjamagia")
    root.geometry("785x485")
    root.resizable(True, True)

    FG = "#e6e6e6"

    frame_top = ctk.CTkFrame(root, corner_radius=8)
    frame_top.pack(fill="x", padx=12, pady=10)

    title = ctk.CTkLabel(frame_top, text="Forjamagia", font=("Segoe UI", 18, "bold"))
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
        # Editor mejorado: filas editables con botones + / - para min/max y detección de cambios sin guardar
        stats_db = Setup_Item_Stats_Database.load_item_stats_txt()
        if not isinstance(stats_db, dict):
            stats_db = {}

        editor = ctk.CTkToplevel(root)
        editor.title("Editor de Item Stats - Forjamagia")
        editor.geometry("1120x680")
        editor.grab_set()

        # ========== HEADER CON BÚSQUEDA MEJORADA ==========
        top = ctk.CTkFrame(editor)
        top.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(top, text="🔍 Buscar Item:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(6, 6))
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(top, textvariable=search_var, placeholder_text="Nombre del item...", width=320, height=32)
        search_entry.pack(side="left", padx=6)

        sort_var = tk.StringVar(value="alfabético")
        sort_menu = ctk.CTkOptionMenu(top, values=["alfabético", "recientes"], variable=sort_var, width=140, height=32)
        sort_menu.pack(side="left", padx=6)

        ctk.CTkButton(top, text="➕ Nuevo Item", width=140, height=32, command=lambda: create_new_item()).pack(side="right", padx=6)

        # ========== CUERPO: LISTA + EDITOR ==========
        body = ctk.CTkFrame(editor)
        body.pack(fill="both", expand=True, padx=12, pady=6)

        # Columna izq: items
        items_frame = ctk.CTkFrame(body, width=280, corner_radius=8)
        items_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        items_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(items_frame, text="📦 Items", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 4))
        items_list = tk.Listbox(items_frame, height=26, font=("Consolas", 10), relief="flat", bg="#2b2b2b", fg="#e6e6e6")
        items_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Columna der: editor
        edit_frame = ctk.CTkFrame(body, corner_radius=8)
        edit_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        body.grid_columnconfigure(1, weight=1)

        # Header del editor
        edit_top = ctk.CTkFrame(edit_frame)
        edit_top.pack(fill="x", padx=8, pady=(8, 4))

        item_name_var = tk.StringVar(value="(ningún item seleccionado)")
        item_name_label = ctk.CTkLabel(edit_top, textvariable=item_name_var, font=("Segoe UI", 12, "bold"), text_color="#00d4ff")
        item_name_label.pack(anchor="w", side="left")

        unsaved_label = ctk.CTkLabel(edit_top, text="", font=("Segoe UI", 10), text_color="#ff6b6b")
        unsaved_label.pack(anchor="e", side="right")

        # Área scrollable para stats
        scroll = ctk.CTkScrollableFrame(edit_frame, corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # ========== CONTROLES INFERIORES ==========
        controls = ctk.CTkFrame(editor)
        controls.pack(fill="x", padx=12, pady=8)

        ctk.CTkButton(controls, text="Añadir Stat", width=130, height=32, command=lambda: add_stat_to_current()).pack(side="left", padx=4)

        save_btn = ctk.CTkButton(controls, text="💾 Guardar", width=130, height=32, fg_color="#007acc")
        save_btn.pack(side="right", padx=4)

        ctk.CTkButton(controls, text="✕ Cerrar", width=130, height=32, fg_color="#555555", command=lambda: on_editor_close()).pack(side="right", padx=4)

        # ========== ESTADO INTERNO ==========
        current_item = {"name": None, "rows": []}
        row_widgets = []
        unsaved = {"flag": False}

        def mark_unsaved(v=True):
            unsaved["flag"] = bool(v)
            if unsaved["flag"]:
                unsaved_label.configure(text="● Cambios sin guardar", text_color="#ff6b6b")
                save_btn.configure(fg_color="#007acc")
            else:
                unsaved_label.configure(text="")
                save_btn.configure(fg_color="#005a9e")

        def refresh_items():
            items_list.delete(0, "end")
            q = search_var.get().strip().lower()
            order = sort_var.get()

            items_sorted = sorted(stats_db.keys())

            for name in items_sorted:
                if not q or q in name.lower():
                    items_list.insert("end", name)

        def build_rows_ui():
            """Reconstruye la interfaz de stats con nombres legibles."""
            for w in row_widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
            row_widgets.clear()

            if not current_item["rows"]:
                empty_lbl = ctk.CTkLabel(scroll, text="Sin stats aún. Usa 'Añadir Stat'.", text_color="#888888")
                empty_lbl.pack(pady=20)
                row_widgets.append(empty_lbl)
                return

            for idx, r in enumerate(current_item["rows"]):
                stat_code, min_val, max_val = r[0], r[1], r[2]
                stat_name = Setup_Item_Stats_Database.get_stat_display_name(stat_code)
                stat_cat = Setup_Item_Stats_Database.get_stat_category(stat_code)

                frame = ctk.CTkFrame(scroll, corner_radius=6, fg_color="#1a1a1a")
                frame.pack(fill="x", padx=4, pady=3)

                # Stat name + category
                name_frame = ctk.CTkFrame(frame, fg_color="transparent")
                name_frame.pack(fill="x", padx=8, pady=(6, 2))

                ctk.CTkLabel(name_frame, text=stat_name, font=("Segoe UI", 10, "bold")).pack(anchor="w", side="left")
                ctk.CTkLabel(name_frame, text=f"[{stat_cat}]", font=("Segoe UI", 9), text_color="#888888").pack(anchor="w", side="left", padx=(6, 0))
                ctk.CTkLabel(name_frame, text=stat_code, font=("Segoe UI", 8, "italic"), text_color="#666666").pack(anchor="e", side="right")

                # Controles min/max
                vals_frame = ctk.CTkFrame(frame, fg_color="transparent")
                vals_frame.pack(fill="x", padx=8, pady=(2, 6))

                # Min
                ctk.CTkLabel(vals_frame, text="Min:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0, 6))
                min_var = tk.StringVar(value=str(int(min_val)))
                min_entry = ctk.CTkEntry(vals_frame, textvariable=min_var, width=60, height=28, font=("Segoe UI", 9))
                min_entry.grid(row=0, column=1, padx=2)

                def make_min_change(i, entry_var):
                    def cb(*args):
                        try:
                            current_item["rows"][i][1] = int(entry_var.get() or 0)
                            mark_unsaved(True)
                        except ValueError:
                            pass
                    return cb
                min_var.trace("w", make_min_change(idx, min_var))

                # Max
                ctk.CTkLabel(vals_frame, text="Max:", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(12, 6))
                max_var = tk.StringVar(value=str(int(max_val)))
                max_entry = ctk.CTkEntry(vals_frame, textvariable=max_var, width=60, height=28, font=("Segoe UI", 9))
                max_entry.grid(row=0, column=3, padx=2)

                def make_max_change(i, entry_var):
                    def cb(*args):
                        try:
                            current_item["rows"][i][2] = int(entry_var.get() or 0)
                            mark_unsaved(True)
                        except ValueError:
                            pass
                    return cb
                max_var.trace("w", make_max_change(idx, max_var))

                # Botones
                btns_frame = ctk.CTkFrame(vals_frame, fg_color="transparent")
                btns_frame.grid(row=0, column=4, sticky="e", padx=(12, 0))

                def make_move(i, d):
                    return lambda: (
                        current_item["rows"].__setitem__(i, current_item["rows"][i + d]) or
                        current_item["rows"].__setitem__(i + d, current_item["rows"][i]) if 0 <= i + d < len(current_item["rows"]) else None,
                        build_rows_ui(),
                        mark_unsaved(True)
                    )[-1]

                if idx > 0:
                    ctk.CTkButton(btns_frame, text="↑", width=28, height=28, font=("Segoe UI", 10), command=make_move(idx, -1)).pack(side="left", padx=1)
                if idx < len(current_item["rows"]) - 1:
                    ctk.CTkButton(btns_frame, text="↓", width=28, height=28, font=("Segoe UI", 10), command=make_move(idx, 1)).pack(side="left", padx=1)

                def make_del(i):
                    def _del():
                        del current_item["rows"][i]
                        build_rows_ui()
                        mark_unsaved(True)
                    return _del

                ctk.CTkButton(btns_frame, text="✕", width=28, height=28, font=("Segoe UI", 10), fg_color="#b02a2a", command=make_del(idx)).pack(side="left", padx=1)

                row_widgets.append(frame)

        def load_item(name):
            if not name or name not in stats_db:
                current_item["name"] = None
                current_item["rows"] = []
                item_name_var.set("(ningún item)")
                build_rows_ui()
                return

            s = stats_db[name]
            rows = []
            for i, obj in enumerate(s.get("obj", [])):
                mn = s.get("min", [])[i] if i < len(s.get("min", [])) else 0
                mx = s.get("max", [])[i] if i < len(s.get("max", [])) else 0
                rows.append([obj, int(mn), int(mx)])

            current_item["name"] = name
            current_item["rows"] = rows
            item_name_var.set(f"📦 {name}")
            build_rows_ui()
            mark_unsaved(False)

        def on_item_select(evt=None):
            sel = items_list.curselection()
            if not sel:
                return
            name = items_list.get(sel[0])
            load_item(name)

        def save_db():
            name = current_item["name"]
            if not name:
                messagebox.showwarning("Aviso", "Selecciona un item para guardar.")
                return

            rows = current_item["rows"]
            # Validar que no hay stats vacías
            if any(not r[0].strip() for r in rows):
                messagebox.showwarning("Error", "Hay stats sin código.")
                return

            stats_db[name] = {
                "obj": [r[0] for r in rows],
                "min": [int(r[1]) for r in rows],
                "max": [int(r[2]) for r in rows],
            }

            ok = Setup_Item_Stats_Database.save_item_stats_txt(stats_db)
            if ok:
                messagebox.showinfo("✓ Éxito", f"DB guardada. Item '{name}' actualizado.")
                mark_unsaved(False)
                refresh_items()
            else:
                messagebox.showerror("Error", "No se pudo guardar el archivo.")

        def create_new_item():
            name = simpledialog.askstring("Nuevo Item", "Nombre del nuevo item:")
            if not name:
                return
            if name in stats_db:
                messagebox.showwarning("Existe", "El item ya existe.")
                return

            stats_db[name] = {"obj": [], "min": [], "max": []}
            refresh_items()

            try:
                idx = list(sorted(stats_db.keys())).index(name)
                items_list.selection_clear(0, "end")
                items_list.selection_set(idx)
                items_list.see(idx)
                load_item(name)
            except Exception:
                pass

            mark_unsaved(True)

        def add_stat_to_current():
            """Diálogo mejorado para añadir stat con selector de categoría."""
            if not current_item["name"]:
                messagebox.showwarning("Aviso", "Selecciona un item primero.")
                return

            dlg = ctk.CTkToplevel(editor)
            dlg.title("Añadir Stat")
            dlg.geometry("520x320")
            dlg.transient(editor)
            dlg.grab_set()

            # Categorías
            ctk.CTkLabel(dlg, text="📂 Categoría:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

            cat_var = tk.StringVar(value="Combate")
            categories = Setup_Item_Stats_Database.get_all_categories()
            cat_menu = ctk.CTkOptionMenu(dlg, values=categories, variable=cat_var, width=400, height=32)
            cat_menu.pack(fill="x", padx=12, pady=4)

            # Stat (actualizar cuando cambia categoría)
            ctk.CTkLabel(dlg, text="⚡ Stat:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

            stat_var = tk.StringVar()
            stat_menu = ctk.CTkOptionMenu(dlg, values=[], variable=stat_var, width=400, height=32)
            stat_menu.pack(fill="x", padx=12, pady=4)

            def update_stats(*args):
                cat = cat_var.get()
                stats = Setup_Item_Stats_Database.get_stats_by_category(cat)
                display = [f"{Setup_Item_Stats_Database.get_stat_display_name(s)} ({s})" for s in stats]
                stat_menu.configure(values=display)
                if display:
                    stat_var.set(display[0])

            cat_var.trace("w", update_stats)
            update_stats()

            # Min/Max
            vals_frame = ctk.CTkFrame(dlg)
            vals_frame.pack(fill="x", padx=12, pady=(8, 6))

            ctk.CTkLabel(vals_frame, text="Min:", font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 6))
            mn_var = tk.StringVar(value="0")
            ctk.CTkEntry(vals_frame, textvariable=mn_var, width=100, height=32).grid(row=0, column=1, padx=(0, 12))

            ctk.CTkLabel(vals_frame, text="Max:", font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 6))
            mx_var = tk.StringVar(value="0")
            ctk.CTkEntry(vals_frame, textvariable=mx_var, width=100, height=32).grid(row=0, column=3)

            def do_add():
                stat_display = stat_var.get()
                stat_code = stat_display.split("(")[-1].rstrip(")")

                try:
                    mn = int(mn_var.get() or 0)
                    mx = int(mx_var.get() or 0)
                except ValueError:
                    messagebox.showwarning("Aviso", "Min/Max deben ser números.")
                    return

                current_item["rows"].append([stat_code, mn, mx])
                build_rows_ui()
                mark_unsaved(True)
                dlg.destroy()

            btns = ctk.CTkFrame(dlg)
            btns.pack(fill="x", padx=12, pady=(6, 10))
            ctk.CTkButton(btns, text="Añadir", width=100, height=32, command=do_add).pack(side="right", padx=4)
            ctk.CTkButton(btns, text="Cancelar", width=100, height=32, fg_color="#555555", command=dlg.destroy).pack(side="right", padx=4)

            dlg.wait_window()

        def on_editor_close():
            if unsaved["flag"]:
                resp = messagebox.askyesnocancel("⚠ Cambios sin guardar", "¿Guardar antes de cerrar?")
                if resp is None:
                    return
                if resp:
                    save_db()
            editor.destroy()

        items_list.bind("<<ListboxSelect>>", on_item_select)
        search_entry.bind("<KeyRelease>", lambda e: refresh_items())
        sort_var.trace("w", lambda *_: refresh_items())

        save_btn.configure(command=save_db)
        editor.protocol("WM_DELETE_WINDOW", on_editor_close)

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
