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

    # Bucle principal: repetir mientras no se solicite stop
    while not control_events.stop_event.is_set():
        # --- NUEVO: Comprobar si ha pasado el intervalo de 30 minutos para resetear sesión ---
        try:
            elapsed_since_reset = time.monotonic() - last_session_reset_time
            if elapsed_since_reset >= SESSION_RESET_INTERVAL:
                try:
                    status_var.set("Reseteando sesión (30m)...")
                except Exception:
                    pass
                log(f"Tiempo de ejecución >=30min ({int(elapsed_since_reset)}s). Realizando reseteo de sesión.")
                # intentar resetear sesión solo si tenemos el módulo disponible
                reset_ok = False
                try:
                    if SessionReset is not None and hasattr(SessionReset, "restart_dofus_and_click_forge"):
                        # pasar el nombre del item actual si está disponible
                        current_item = shared_state.get("current_item", "") or ""
                        try:
                            reset_ok = bool(SessionReset.restart_dofus_and_click_forge(current_item))
                            log(f"restart_dofus_and_click_forge resultado: {reset_ok}")
                        except Exception as e:
                            reset_ok = False
                            log(f"Excepción al ejecutar restart_dofus_and_click_forge: {e}")
                    else:
                        log("SessionReset no disponible: no se puede resetear sesión automáticamente.")
                except Exception as e:
                    log(f"ERROR durante intento de reseteo: {e}")
                    reset_ok = False

                # --- NUEVO: leer kamas tras el reset y guardar como fallo ---
                try:
                    import Extra_get_kamas as KamasModule
                    try:
                        kamas_finales = KamasModule.get_kamas()
                        log(f"Kamas leídas tras reset: {kamas_finales}")
                    except Exception as e:
                        kamas_finales = None
                        log(f"WARNING: no se pudieron leer kamas tras reset: {e}")
                except Exception as e:
                    kamas_finales = None
                    log(f"DEBUG: Extra_get_kamas no importable: {e}")

                # Guardar en la base como fallo (si se puede) usando Extra_Database.agregar_datos preferentemente
                try:
                    attempts_now = int(shared_state.get("exo_attempts", 0))
                except Exception:
                    attempts_now = 0

                if kamas_finales is not None:
                    try:
                        import Extra_Database as DB
                        try:
                            DB.agregar_datos(
                                objeto_seleccionado=current_item or "Unknown_Item_After_Reset",
                                intentos=attempts_now,
                                kamas_iniciales=None,
                                kamas_finales=kamas_finales,
                                exito=0,
                                tiempo_medio_intento=None,
                                modo_encadenado_activo=True
                            )
                            log("Guardado en DB (Extra_Database) como fallo tras reset con kamas finales.")
                        except Exception as e:
                            log(f"WARNING: Extra_Database.agregar_datos falló: {e}")
                            # intentar fallback a DataSaver.finalize_session si existe
                            if DataSaver is not None and hasattr(DataSaver, "finalize_session"):
                                try:
                                    DataSaver.finalize_session(
                                        objeto=current_item or "Unknown_Item_After_Reset",
                                        intentos=attempts_now,
                                        exito=0,
                                        tiempo_medio_intento=None,
                                        modo_encadenado_activo=True,
                                        precio_objeto_base=None,
                                        precio_venta_objeto_final=None,
                                        tipo_exo=None,
                                        kamas_iniciales_arg=None
                                    )
                                    log("Fallback: DataSaver.finalize_session usado para guardar fallo tras reset.")
                                except Exception as e2:
                                    log(f"ERROR: fallback DataSaver.finalize_session falló: {e2}")
                    except Exception as e:
                        log(f"DEBUG: Extra_Database no importable o fallo al usarlo: {e}")
                        # intentar fallback a DataSaver.finalize_session si existe y kamas leídas
                        if DataSaver is not None and hasattr(DataSaver, "finalize_session"):
                            try:
                                DataSaver.finalize_session(
                                    objeto=current_item or "Unknown_Item_After_Reset",
                                    intentos=attempts_now,
                                    exito=0,
                                    tiempo_medio_intento=None,
                                    modo_encadenado_activo=True,
                                    precio_objeto_base=None,
                                    precio_venta_objeto_final=None,
                                    tipo_exo=None,
                                    kamas_iniciales_arg=None
                                )
                                log("Fallback: DataSaver.finalize_session usado para guardar fallo tras reset.")
                            except Exception as e2:
                                log(f"ERROR: fallback DataSaver.finalize_session falló: {e2}")
                else:
                    log("No se dispone de lectura de kamas; no se guardará fallo con kamas finales.")

                # Resetar contadores y timmer (siempre actualizar el timer para evitar bucle inmediato)
                shared_state["exo_attempts"] = 0
                shared_state["rune_clicks"] = 0
                last_session_reset_time = time.monotonic()
                try:
                    status_var.set("Sesión reseteada. Reintentando Setup...")
                except Exception:
                    pass

                # Llamar a Setup inmediatamente para reiniciar el ciclo (intentamos obtener nuevo item_name/item_stats)
                try:
                    log("Llamando a Setup inmediatamente tras reseteo para reiniciar el ciclo...")
                    try:
                        new_setup = Main_Setup.main()
                        # si Main_Setup devuelve (name, stats) lo mostramos en log
                        if isinstance(new_setup, tuple) and len(new_setup) >= 2:
                            new_name = new_setup[0]
                            log(f"Setup devuelto: {new_name}")
                            shared_state["current_item"] = new_name
                    except Exception as e:
                        log(f"WARNING: Falló llamada a Main_Setup.main() tras reseteo: {e}")
                except Exception as e:
                    log(f"ERROR: excepción al invocar Setup tras reset: {e}")

                # pequeña espera para estabilizar ventanas antes de volver a setup/mage
                time.sleep(1.0)
                # continuar el bucle para entrar en la fase de setup (o usar lo que Setup ya hizo)
                continue
        except Exception as e:
            print("WARNING: fallo comprobando/ejecutando session reset:", e)

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
        start_mage_time = time.time()
        try:
            result = mage_main(
                item_name,
                item_stats,
                control_events={'pause_event': control_events.pause_event, 'stop_event': control_events.stop_event}
            )
        except Exception as e:
            print("ERROR en Mage_Main:", e)
            result = {"success": False, "attempts": 0, "elapsed": 0.0, "time_per_attempt": None, "error": repr(e)}

        # --- NUEVO: Si mage_main indicó que hizo reset de sesión, actualizar temporizador local ---
        try:
            if isinstance(result, dict) and result.get("reset_session"):
                last_session_reset_time = time.monotonic()
                log("RUN: Se ha detectado reset de sesión solicitado por Mage_Main. last_session_reset_time restablecido.")
                # opcional: informar por correo que se hizo reseteo (no bloquear si falla)
                try:
                    current_item = shared_state.get("current_item", "") or ""
                    if Correo is not None:
                        Correo.send_mail(current_item, "Reseteo sesión - OK")
                except Exception as e:
                    log(f"WARNING: fallo enviando correo tras reset de sesión: {e}")
        except Exception:
            pass

        # --- UNIFICACIÓN: obtener valores definitivos para guardado ---
        # 1. elapsed real (medido aquí)
        elapsed_real = time.time() - start_mage_time

        # 2. attempts: SIEMPRE desde shared_state (única fuente de verdad)
        try:
            attempts_to_save = int(shared_state.get("exo_attempts", 0))
        except Exception:
            attempts_to_save = 0

        # 3. time_per_attempt: calculado aquí una sola vez
        if attempts_to_save > 0:
            time_per_attempt = elapsed_real / attempts_to_save
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
    root.title("Forjamagia - Orquestador")
    root.geometry("980x640")
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
        # Editor mejorado: filas editables con botones + / - para min/max y detección de cambios sin guardar
        stats_db = Setup_Item_Stats_Database.load_item_stats_txt()
        if not isinstance(stats_db, dict):
            stats_db = {}

        editor = ctk.CTkToplevel(root)
        editor.title("Editor de Item Stats (TXT) - Futurista")
        editor.geometry("980x600")
        editor.grab_set()

        top = ctk.CTkFrame(editor)
        top.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(top, text="Buscar:", width=60).pack(side="left", padx=(6, 6))
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(top, textvariable=search_var, width=300)
        search_entry.pack(side="left")
        ctk.CTkButton(top, text="Nuevo Item", width=120, command=lambda: create_new_item()).pack(side="right", padx=6)

        body = ctk.CTkFrame(editor)
        body.pack(fill="both", expand=True, padx=12, pady=6)

        # Lista de items (Listbox simple)
        items_frame = ctk.CTkFrame(body, width=260)
        items_frame.grid(row=0, column=0, sticky="ns")
        items_list = tk.Listbox(items_frame, height=24)
        items_list.pack(fill="both", expand=True, padx=6, pady=6)

        # Área editable (scrollable)
        edit_frame = ctk.CTkFrame(body)
        edit_frame.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        body.grid_columnconfigure(1, weight=1)

        scroll = ctk.CTkScrollableFrame(edit_frame, corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=6, pady=6)

        # botones de control abajo
        controls = ctk.CTkFrame(editor)
        controls.pack(fill="x", padx=12, pady=8)
        save_btn = ctk.CTkButton(controls, text="Guardar TXT", width=140)
        save_btn.pack(side="right", padx=8)
        cancel_btn = ctk.CTkButton(controls, text="Cerrar (Salir)", width=140)
        cancel_btn.pack(side="right", padx=8)

        current_item = {"name": None, "rows": []}  # rows = list of [obj, min, max]
        row_widgets = []  # referencias a widgets por fila para actualizacion
        unsaved = {"flag": False}

        def mark_unsaved(v=True):
            unsaved["flag"] = bool(v)
            # customtkinter no permite fg_color=None; usar "transparent" para transparencia por defecto
            try:
                save_btn.configure(fg_color="#007acc" if unsaved["flag"] else "transparent")
            except Exception:
                # fallback seguro: solo cambiar estado visual mínimo
                try:
                    save_btn.configure(state="normal" if unsaved["flag"] else "disabled")
                except Exception:
                    pass

        def refresh_items():
            items_list.delete(0, "end")
            q = search_var.get().strip().lower()
            for name in sorted(stats_db.keys()):
                if not q or q in name.lower():
                    items_list.insert("end", name)

        def build_rows_ui():
            # limpiar
            for w in row_widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
            row_widgets.clear()

            for idx, r in enumerate(current_item["rows"]):
                frame = ctk.CTkFrame(scroll, corner_radius=6)
                frame.pack(fill="x", padx=4, pady=4)
                # stat name
                lbl = ctk.CTkLabel(frame, text=r[0], width=160, anchor="w")
                lbl.grid(row=0, column=0, padx=8, pady=6, sticky="w")
                # min controls
                min_lbl = ctk.CTkLabel(frame, text=f"Min: {r[1]}", width=90)
                min_lbl.grid(row=0, column=1, padx=4)
                def make_min_inc(i):
                    return lambda: change_value(i, 1, kind="min")
                def make_min_dec(i):
                    return lambda: change_value(i, -1, kind="min")
                ctk.CTkButton(frame, text="-", width=28, height=28, command=make_min_dec(idx)).grid(row=0, column=2, padx=2)
                ctk.CTkButton(frame, text="+", width=28, height=28, command=make_min_inc(idx)).grid(row=0, column=3, padx=2)
                # max controls
                max_lbl = ctk.CTkLabel(frame, text=f"Max: {r[2]}", width=90)
                max_lbl.grid(row=0, column=4, padx=8)
                def make_max_inc(i):
                    return lambda: change_value(i, 1, kind="max")
                def make_max_dec(i):
                    return lambda: change_value(i, -1, kind="max")
                ctk.CTkButton(frame, text="-", width=28, height=28, command=make_max_dec(idx)).grid(row=0, column=5, padx=2)
                ctk.CTkButton(frame, text="+", width=28, height=28, command=make_max_inc(idx)).grid(row=0, column=6, padx=2)
                # move / delete
                def make_move(i, d):
                    return lambda: move_row(i, d)
                ctk.CTkButton(frame, text="↑", width=34, command=make_move(idx, -1)).grid(row=0, column=7, padx=6)
                ctk.CTkButton(frame, text="↓", width=34, command=make_move(idx, 1)).grid(row=0, column=8, padx=2)
                def make_del(i):
                    return lambda: delete_row(i)
                ctk.CTkButton(frame, text="Eliminar", width=80, fg_color="#b02a2a", command=make_del(idx)).grid(row=0, column=9, padx=8)

                # almacenar referencias para actualizar etiquetas fácilmente
                row_widgets.append(frame)
                # guardar referencias a labels para refrescar texto al cambiar
                frame._min_lbl = min_lbl
                frame._max_lbl = max_lbl

        def change_value(idx, delta, kind="min"):
            try:
                if idx < 0 or idx >= len(current_item["rows"]):
                    return
                if kind == "min":
                    current_item["rows"][idx][1] = max(0, int(current_item["rows"][idx][1]) + int(delta))
                else:
                    current_item["rows"][idx][2] = max(0, int(current_item["rows"][idx][2]) + int(delta))
                # actualizar labels
                w = row_widgets[idx]
                w._min_lbl.configure(text=f"Min: {current_item['rows'][idx][1]}")
                w._max_lbl.configure(text=f"Max: {current_item['rows'][idx][2]}")
                mark_unsaved(True)
            except Exception as e:
                print("ERROR change_value:", e)

        def move_row(i, delta):
            j = i + delta
            if j < 0 or j >= len(current_item["rows"]):
                return
            current_item["rows"][i], current_item["rows"][j] = current_item["rows"][j], current_item["rows"][i]
            build_rows_ui()
            mark_unsaved(True)

        def delete_row(i):
            if i < 0 or i >= len(current_item["rows"]):
                return
            del current_item["rows"][i]
            build_rows_ui()
            mark_unsaved(True)

        def load_item(name):
            # construir rows desde stats_db
            if not name or name not in stats_db:
                current_item["name"] = None
                current_item["rows"] = []
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
                messagebox.showwarning("Aviso", "Seleccione un item para guardar.")
                return
            rows = current_item["rows"]
            stats_db[name] = {
                "obj": [r[0] for r in rows],
                "min": [int(r[1]) for r in rows],
                "max": [int(r[2]) for r in rows],
            }
            ok = Setup_Item_Stats_Database.save_item_stats_txt(stats_db)
            if ok:
                messagebox.showinfo("Guardado", "DB guardada en TXT.")
                mark_unsaved(False)
                refresh_items()
            else:
                messagebox.showwarning("Error", "No se pudo guardar el TXT.")

        def create_new_item():
            name = messagebox.askstring("Nuevo item", "Nombre del nuevo item:")
            if not name:
                return
            if name in stats_db:
                messagebox.showwarning("Existe", "El item ya existe.")
                return
            stats_db[name] = {"obj": [], "min": [], "max": []}
            refresh_items()
            # seleccionar creado
            try:
                idx = list(sorted(stats_db.keys())).index(name)
                items_list.selection_clear(0, "end")
                items_list.selection_set(idx)
                items_list.see(idx)
                load_item(name)
            except Exception:
                pass
            mark_unsaved(True)

        def add_stat_to_current(obj_name="new_stat", mn=0, mx=0):
            if not current_item["name"]:
                messagebox.showwarning("Aviso", "Seleccione un item primero.")
                return
            current_item["rows"].append([obj_name, int(mn), int(mx)])
            build_rows_ui()
            mark_unsaved(True)

        # Bindings y evento cierre
        items_list.bind("<<ListboxSelect>>", on_item_select)
        search_entry.bind("<KeyRelease>", lambda e: refresh_items())

        # botones auxiliares (añadir stat)
        aux_btns = ctk.CTkFrame(controls)
        aux_btns.pack(side="left")
        ctk.CTkButton(aux_btns, text="Añadir stat", command=lambda: add_stat_to_current()).pack(side="left", padx=6)
        save_btn.configure(command=save_db)

        def on_editor_close():
            if unsaved["flag"]:
                resp = messagebox.askyesnocancel("Cambios sin guardar", "Hay cambios sin guardar. ¿Guardar antes de cerrar?\n\nSi eliges Cancel, permanecerás en el editor.")
                if resp is None:
                    return  # cancel -> no cerrar
                if resp:
                    save_db()
            editor.destroy()

        cancel_btn.configure(command=on_editor_close)
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
