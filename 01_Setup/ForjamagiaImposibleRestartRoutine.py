import pyautogui
import time

def run_routine():
    """
    Ejecuta una secuencia específica de clics con retraso para reanudar
    el estado cuando ocurre el bloqueo de forjamagia imposible.
    """
    points = [
        (1916, 1148),
        (2937, 515),
        (1813, 1291),
        (2360, 664),
        (2469, 738)
    ]
    
    for idx, (x, y) in enumerate(points, start=1):
        pyautogui.click(x, y)
        time.sleep(1)
    
    # El clic 6 (punto final) es en verdad un doble click
    pyautogui.moveTo(2469, 738, duration=0.1)
    time.sleep(0.2)
    pyautogui.click(clicks=2, interval=0.1)
    time.sleep(1)

if __name__ == "__main__":
    print("Iniciando prueba de la rutina de reinicio en 3 segundos...")
    print("Por favor, enfoca la pantalla del juego...")
    time.sleep(3)
    print("Ejecutando clics...")
    run_routine()
    print("Rutina de prueba completada exitosamente.")
