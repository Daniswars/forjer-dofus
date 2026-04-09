import os

def suspender_pc():
    # El comando de Windows para suspender (requiere que la hibernación esté desactivada)
    # o usar rundll32.
    print("Tarea finalizada. Suspendiendo el equipo...")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

# Al final de tu proceso principal:
if __name__ == "__main__":
    # ... tu código actual ...
    suspender_pc()
