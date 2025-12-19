import time
import sys

try:
    import pyautogui
except Exception:
    print("pyautogui no está instalado. Instálalo con: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True  # mover ratón a esquina superior izquierda aborta

PREP_COUNTDOWN = 4  # segundos para preparar la pantalla
SHORT_DELAY = 0.2

def main():
    print(f"Comienza en {PREP_COUNTDOWN} segundos. Muévete a la ventana objetivo o aborta (esquina superior izquierda).")
    for i in range(PREP_COUNTDOWN, 0, -1):
        print(i)
        time.sleep(1)

    try:
        # 1) Click en X=2946, Y=512 (en vez de Escape), esperar 1 segundo
        pyautogui.click(2946, 512)
        time.sleep(1)

        # 2) Click en X=3812, Y=337 (en vez de 'h'), esperar 2 segundos
        pyautogui.click(3812, 337)
        time.sleep(2)

        # 3) Click en X=1591, Y=1040; esperar 3 segundos
        pyautogui.click(1591, 1040)
        time.sleep(3)

        # 4) Click en X=2043, Y=654
        pyautogui.click(2043, 654)
        time.sleep(1)

        # 5) Doble click en X=2145, Y=745
        pyautogui.moveTo(x=2145, y=745)
        time.sleep(0.2)
        pyautogui.click(clicks=2, interval=0.1)
        time.sleep(1)

        # 6) Click en X=2946, Y=512 y luego en X=3812, Y=337 (en vez de Escape y 'h')
        pyautogui.click(2638, 512)
        time.sleep(1)
        pyautogui.click(3812, 337)

        print("Secuencia completada.")
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    except pyautogui.FailSafeException:
        print("Abortado por FailSafe (ratón en esquina superior izquierda).")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    main()
