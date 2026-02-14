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

def run_process(control_events, status_var, start_btn, stop_btn):
    """
    Orquesta: Main_Setup -> Mage_Main -> guardar con Main_Save_Data.finalize_session
    """
    start_btn.config(state="disabled")
    stop_btn.config(state="normal")
    status_var.set("Preparando Setup...")
    try:
        # 1) Setup: obtener item_name y stats
        status_var.set("Ejecutando Setup...")
        item_info = Main_Setup.main()
        # Main_Setup.main debe devolver (item_name, item_stats) o item_stats si no
        if isinstance(item_info, tuple) and len(item_info) >= 2:
            item_name, item_stats = item_info[0], item_info[1]
        else:
            # compat: si solo devuelve stats, pedir nombre en fallback
            item_stats = item_info
            item_name = getattr(item_stats, "get", lambda k, d=None: d)("name", "Item_NoName")

        # 2) Guardar kamas iniciales (opcional) usando Main_Save_Data.save_initial_kamas
        initial_kamas = None
        if DataSaver is not None:
            try:
                status_var.set("Guardando kamas iniciales...")
                initial_kamas = DataSaver.save_initial_kamas(item_name)
            except Exception as e:
                print("WARNING: save_initial_kamas falló:", e)
        else:
            print("INFO: DataSaver no disponible, no se guardarán kamas iniciales automáticamente.")

        # 3) Llamar a mage_main (pasa control_events para pausar/parar)
        status_var.set("Ejecutando Mage_Main...")
        result = mage_main(item_name, item_stats, control_events=vars(control_events))
        status_var.set("Mage finalizado, guardando...")
        # result expected dict with keys: success, attempts, elapsed, time_per_attempt, error
        success_flag = result.get("success", False) if isinstance(result, dict) else False
        attempts = result.get("attempts", 0) if isinstance(result, dict) else 0
        time_per_attempt = result.get("time_per_attempt", None) if isinstance(result, dict) else None

        # 4) Guardado final (Aux_Guardar_Exito): usar Main_Save_Data.finalize_session
        if DataSaver is not None:
            try:
                exito_flag = "PA" if success_flag else 0
                status_var.set("Guardando en Excel...")
                saved = DataSaver.finalize_session(
                    objeto=item_name,
                    intentos=attempts or 1,
                    exito=exito_flag,
                    tiempo_medio_intento=time_per_attempt,
                    modo_encadenado_activo=True,
                    precio_objeto_base=None,
                    precio_venta_objeto_final=None,
                    tipo_exo="PA" if success_flag else None,
                    kamas_iniciales_arg=None
                )
                status_var.set("Guardado completado." if saved == 0 or saved is True else "Guardado fallido.")
            except Exception as e:
                print("ERROR al guardar desde Main:", e)
                status_var.set("Error al guardar")
        else:
            status_var.set("DataSaver no disponible - no guardado.")

        message = f"Proceso finalizado. Éxito: {success_flag}, intentos: {attempts}, error: {result.get('error') if isinstance(result, dict) else 'N/A'}"
        messagebox.showinfo("Resultado", message)
    except Exception as e:
        print("ERROR en run_process:", e)
        messagebox.showerror("Error", f"Error en proceso: {e}")
    finally:
        status_var.set("Idle")
        start_btn.config(state="normal")
        stop_btn.config(state="disabled")
        # Reset stop event for next run
        control_events.stop_event.clear()
        control_events.pause_event.set()

def build_ui():
    root = tk.Tk()
    root.title("Forjamagia - Control")
    root.geometry("400x180")

    status_var = tk.StringVar(value="Idle")
    lbl = tk.Label(root, textvariable=status_var, font=("Segoe UI", 12))
    lbl.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    control_events = ControlEvents()
    control_events.pause_event.set()  # empezar en estado running

    start_btn = tk.Button(btn_frame, text="Iniciar", width=12,
                          command=lambda: threading.Thread(target=run_process, args=(control_events, status_var, start_btn, stop_btn), daemon=True).start())
    start_btn.grid(row=0, column=0, padx=10)

    def stop_clicked():
        # señal de parada: Mage_Main debe leer stop_event y terminar
        control_events.stop_event.set()
        control_events.pause_event.set()  # levantar pausa si estaba pausado para permitir salida
        status_var.set("Parando y guardando...")

    stop_btn = tk.Button(btn_frame, text="Parar (guardar)", width=12, command=stop_clicked, state="disabled")
    stop_btn.grid(row=0, column=1, padx=10)

    # Pausar/Resumir con F9
    def toggle_pause(event=None):
        if control_events.pause_event.is_set():
            control_events.pause_event.clear()
            status_var.set("Pausado")
        else:
            control_events.pause_event.set()
            status_var.set("Reanudando...")

    # Parar y guardar con F10
    def f10_stop(event=None):
        stop_clicked()

    root.bind('<F9>', toggle_pause)
    root.bind('<F10>', f10_stop)

    tip = tk.Label(root, text="Atajos: F9 Pausa/Resume, F10 Parar y Guardar", font=("Segoe UI", 9))
    tip.pack(pady=8)

    root.mainloop()

if __name__ == "__main__":
    build_ui()
