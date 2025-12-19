import time
import sys
import Setup_Read_First_Rune_Name

try:
    import pyautogui
except Exception:
    print("pyautogui no está instalado. Instálalo con: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True  # mover ratón a esquina superior izquierda aborta

# Configuración de delays (segundos)
PREP_COUNTDOWN = 1      # tiempo para posicionar ventana antes de empezar
DELAY_BETWEEN = 0.8       # delay entre acciones principales
TYPE_INTERVAL = 0.12      # intervalo entre letras al escribir

def step(msg):
    print(msg)
    time.sleep(DELAY_BETWEEN)

def main():
    print(f"Comienzo en {PREP_COUNTDOWN} segundos. Muévete a la ventana objetivo o aborta (esquina superior izquierda).")
    for i in range(PREP_COUNTDOWN, 0, -1):
        print(i)
        time.sleep(1)

    try:
        # 1: X=2352, Y=790 haga click aqui
        pyautogui.click(2352, 790)
        step("1) Click en (2352, 790) realizado.")

        # 2: X=2555, Y=572 haga click aqui y escriba "runa"
        pyautogui.click(2555, 572)
        time.sleep(0.2)
        pyautogui.write("runa", interval=TYPE_INTERVAL)
        step('2) Click en (2555, 572) y escrito "runa".')

        if Setup_Read_First_Rune_Name.read_new_item_name() == "Runa Ga PA":
            print("Texto 'Runa Ga PA' detectado correctamente.")
        else:

            # 3: X=2540, Y=623 haga click aqui
            pyautogui.click(2540, 623)
            step("3) Click en (2540, 623) realizado.")

            # 4: X=2499, Y=722 mueva aqui el raton y haga scroll down
            pyautogui.moveTo(2499, 722, duration=0.5)
            time.sleep(0.2)
            # scroll down (valor negativo)
            pyautogui.scroll(-600)
            step("4) Movido a (2499, 722) y scroll down realizado.")

        # 8: X=1144, Y=1362 haga click aqui
        pyautogui.click(2494, 898)
        step("8) Click en (1144, 1362) realizado.")

        print("Secuencia completada.")
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    except pyautogui.FailSafeException:
        print("Abortado por FailSafe (ratón en esquina superior izquierda).")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    main()
