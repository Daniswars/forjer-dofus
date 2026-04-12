import os
import time

def suspender_pc(segundos=300, cancel_event=None):
    print(f"Tarea finalizada. El equipo se suspenderá en {segundos} segundos...")

    for restante in range(segundos, 0, -1):
        if cancel_event is not None and cancel_event.is_set():
            print("Suspensión cancelada por el usuario.")
            return False
        print(f"Suspendiendo en {restante}...")
        time.sleep(1)

    if cancel_event is not None and cancel_event.is_set():
        print("Suspensión cancelada justo antes de ejecutar.")
        return False

    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return True

# Al final de tu proceso principal:
if __name__ == "__main__":
    # ...existing code...
    suspender_pc(10)
