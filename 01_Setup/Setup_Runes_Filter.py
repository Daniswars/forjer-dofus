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

def _normalize_text(t: str) -> str:
    return " ".join((t or "").strip().lower().split())

def _is_target_rune(t: str) -> bool:
    normalized = _normalize_text(t)
    return normalized in {"runa ga pa", "runa ga pm"}

def _correction_scrolls():
    # 3: X=2540, Y=623 haga click aqui (ANTES de scrolls)
    pyautogui.click(2540, 623)
    step("3) Click en (2540, 623) realizado.")

    print("Corrección: 10 scrolls arriba y 7 scrolls abajo...")
    for i in range(10):
        print(f"  Scroll arriba {i+1}/10")
        pyautogui.scroll(600)
        time.sleep(0.25)
    for i in range(7):
        print(f"  Scroll abajo {i+1}/7")
        pyautogui.scroll(-600)
        time.sleep(0.25)
    print("✓ Corrección de scrolls completada.")

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

        max_retries = 30
        for intento in range(1, max_retries + 1):
            detected = Setup_Read_First_Rune_Name.read_new_item_name()
            print(f"Verificación OCR intento {intento}: '{detected}'")

            if _is_target_rune(detected):
                print("Texto objetivo detectado correctamente ('Runa Ga PA' o 'Runa Ga PM').")
                break

            print("No es 'Runa Ga PA' ni 'Runa Ga PM'. Reaplicando corrección...")
            _correction_scrolls()
        else:
            raise RuntimeError("No se pudo detectar 'Runa Ga PA' ni 'Runa Ga PM' tras múltiples intentos.")

        # 8: X=2494, Y=898 haga click aqui
        pyautogui.click(2494, 898)
        step("8) Click en (2494, 898) realizado.")

        print("Secuencia completada.")
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    except pyautogui.FailSafeException:
        print("Abortado por FailSafe (ratón en esquina superior izquierda).")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    main()
