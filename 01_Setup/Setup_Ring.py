import time
import sys

try:
    import pyautogui
except Exception:
    print("pyautogui no está instalado. Instálalo con: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True  # mover ratón a esquina superior izquierda aborta

PREP_COUNTDOWN = 1  # segundos para preparar la pantalla
DELAY_BETWEEN = 0.3

def main():
    print(f"Comienza en {PREP_COUNTDOWN} segundos. Muévete a la ventana objetivo o aborta (esquina superior izquierda).")
    for i in range(PREP_COUNTDOWN, 0, -1):
        print(i)
        time.sleep(1)

    try:

        pyautogui.moveTo(x=2468, y=714)
        time.sleep(0.2)
        pyautogui.click(clicks=2, interval=0.1)
        time.sleep(1)

        print("Secuencia completada.")
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    except pyautogui.FailSafeException:
        print("Abortado por FailSafe (ratón en esquina superior izquierda).")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    main()
