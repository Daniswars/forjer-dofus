import time
import sys
import pyautogui
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'
pyautogui.FAILSAFE = True

def test_basic_scroll():
    """Prueba 1: scroll básico repetido"""
    print("\n=== TEST 1: SCROLL BÁSICO (7 repeticiones) ===")
    print("En 3 segundos comenzará el test. Asegúrate que la ventana está en foco.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    print("Click realizado en (2540, 623)")
    time.sleep(1)

    for i in range(7):
        print(f"  Scroll {i+1}/7 (valor: -600)")
        pyautogui.scroll(-600)
        time.sleep(0.1)

    print("✓ Test 1 completado.\n")

def test_scroll_with_moveto():
    """Prueba 2: scroll con moveTo previo"""
    print("\n=== TEST 2: SCROLL CON MOVETO ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    print("Moviendo ratón a (2499, 722)...")
    pyautogui.moveTo(2499, 722, duration=0.3)
    time.sleep(0.5)

    for i in range(7):
        print(f"  Scroll {i+1}/7 desde (2499, 722)")
        pyautogui.scroll(-600)
        time.sleep(0.15)

    print("✓ Test 2 completado.\n")

def test_scroll_with_different_values():
    """Prueba 3: scroll con diferentes valores"""
    print("\n=== TEST 3: SCROLL CON VALORES VARIADOS ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    time.sleep(1)

    scroll_values = [-300, -300, -300, -300, -400, -400, -400]

    for i, val in enumerate(scroll_values):
        print(f"  Scroll {i+1}/7 (valor: {val})")
        pyautogui.scroll(val)
        time.sleep(0.12)

    print("✓ Test 3 completado.\n")

def test_scroll_with_longer_delays():
    """Prueba 4: scroll con delays más largos"""
    print("\n=== TEST 4: SCROLL CON DELAYS MÁS LARGOS ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    time.sleep(1)

    for i in range(7):
        print(f"  Scroll {i+1}/7 (valor: -600) - delay 0.25s")
        pyautogui.scroll(-600)
        time.sleep(0.25)

    print("✓ Test 4 completado.\n")

def test_scroll_aggressive():
    """Prueba 5: scroll más agresivo (valores mayores)"""
    print("\n=== TEST 5: SCROLL AGRESIVO (valores -1000) ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    time.sleep(1)

    for i in range(5):
        print(f"  Scroll {i+1}/5 (valor: -1000)")
        pyautogui.scroll(-1000)
        time.sleep(0.2)

    print("✓ Test 5 completado.\n")

def test_scroll_with_keyboard():
    """Prueba 6: scroll usando keyboard (Page Down)"""
    print("\n=== TEST 6: SCROLL CON KEYBOARD (Page Down) ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    time.sleep(1)

    for i in range(7):
        print(f"  Presionando Page Down {i+1}/7")
        pyautogui.press('pagedown')
        time.sleep(0.15)

    print("✓ Test 6 completado.\n")

def test_scroll_combined():
    """Prueba 7: combinación de scroll + keyboard"""
    print("\n=== TEST 7: SCROLL COMBINADO (mixto) ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    pyautogui.click(2540, 623)
    time.sleep(1)

    for i in range(4):
        print(f"  Scroll {i+1}/4 (valor: -600)")
        pyautogui.scroll(-600)
        time.sleep(0.12)

    print("  Presionando Page Down 3 veces...")
    for i in range(3):
        pyautogui.press('pagedown')
        time.sleep(0.15)

    print("✓ Test 7 completado.\n")

def test_scroll_with_ocr_detection():
    """Prueba 8: scroll con detección OCR de 'Ordenar por nivel'"""
    print("\n=== TEST 8: SCROLL CON DETECCIÓN OCR ===")
    print("En 3 segundos comenzará el test. Asegúrate que la ventana está en foco.")
    time.sleep(3)

    # Coordenadas de lectura
    read_x1, read_y1 = 2438, 614
    read_x2, read_y2 = 2643, 650

    # Coordenadas para scroll
    scroll_x, scroll_y = 2540, 623

    # Coordenada neutral para leer sin interferencias
    neutral_x, neutral_y = 100, 100

    max_attempts = 3
    attempt = 0
    found = False

    while attempt < max_attempts and not found:
        attempt += 1
        print(f"\n--- Intento {attempt}/{max_attempts} ---")

        # Volver a clickar en posición de scroll
        print(f"Click en ({scroll_x}, {scroll_y}) para scroll...")
        pyautogui.click(scroll_x, scroll_y)
        time.sleep(0.3)

        # Hacer 7 scrolls abajo
        print("Haciendo 7 scrolls abajo...")
        for i in range(7):
            print(f"  Scroll abajo {i+1}/7")
            pyautogui.scroll(-600)
            time.sleep(0.15)

        print("Esperando 0.5s antes de leer...")
        time.sleep(0.5)

        # Click en zona neutral para leer sin interferencias
        print(f"Click en zona neutral ({neutral_x}, {neutral_y}) para leer OCR...")
        pyautogui.click(neutral_x, neutral_y)
        time.sleep(0.3)

        # Capturar región y leer con OCR
        print(f"Leyendo región OCR: ({read_x1}, {read_y1}) a ({read_x2}, {read_y2})...")
        try:
            screenshot = pyautogui.screenshot(region=(read_x1, read_y1, read_x2 - read_x1, read_y2 - read_y1))

            # Mejorar imagen para OCR
            screenshot = screenshot.convert('L')
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(screenshot)
            screenshot = enhancer.enhance(2)

            text = pytesseract.image_to_string(screenshot, lang='spa')
            print(f"Texto detectado: '{text}'")

            # Buscar "Ordenar por nivel" (flexible)
            if 'ordenar' in text.lower() and 'nivel' in text.lower():
                print("✓ ¡ENCONTRADO! 'Ordenar por nivel' detectado.")
                found = True
            else:
                print("✗ No detectado 'Ordenar por nivel'")

                if attempt < max_attempts:
                    print(f"\nHaciendo 10 scrolls arriba antes de reintentar...")
                    # Click en posición de scroll antes de scrollear
                    print(f"Click en ({scroll_x}, {scroll_y}) para scroll arriba...")
                    pyautogui.click(scroll_x, scroll_y)
                    time.sleep(0.3)

                    for i in range(10):
                        print(f"  Scroll arriba {i+1}/10")
                        pyautogui.scroll(600)
                        time.sleep(0.12)
                    print("Esperando 1s antes de siguiente intento...")
                    time.sleep(1)

        except Exception as e:
            print(f"✗ Error en OCR: {e}")
            if attempt < max_attempts:
                print(f"Haciendo 10 scrolls arriba antes de reintentar...")
                # Click en posición de scroll antes de scrollear
                print(f"Click en ({scroll_x}, {scroll_y}) para scroll arriba...")
                pyautogui.click(scroll_x, scroll_y)
                time.sleep(0.3)

                for i in range(10):
                    pyautogui.scroll(600)
                    time.sleep(0.12)
                time.sleep(1)

    if found:
        print("\n✓ Test 8 completado exitosamente.")
    else:
        print(f"\n✗ No se encontró 'Ordenar por nivel' después de {max_attempts} intentos.")

def test_scroll_debug_visual():
    """Prueba 9: debug visual - captura antes/después del scroll"""
    print("\n=== TEST 9: DEBUG VISUAL (antes/después) ===")
    print("En 3 segundos comenzará el test.")
    time.sleep(3)

    read_x1, read_y1 = 2438, 614
    read_x2, read_y2 = 2643, 650

    # Coordenadas para scroll
    scroll_x, scroll_y = 2540, 623

    # Coordenada neutral para leer
    neutral_x, neutral_y = 100, 100

    print("Click en zona neutral para capturar ANTES...")
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)

    print("Capturando ANTES del scroll...")
    before = pyautogui.screenshot(region=(read_x1, read_y1, read_x2 - read_x1, read_y2 - read_y1))
    before_text = pytesseract.image_to_string(before, lang='spa')
    print(f"Texto ANTES: '{before_text}'")

    print(f"\nClick en ({scroll_x}, {scroll_y}) para scroll...")
    pyautogui.click(scroll_x, scroll_y)
    time.sleep(0.3)

    print("Haciendo 7 scrolls abajo...")
    for i in range(7):
        pyautogui.scroll(-600)
        time.sleep(0.15)

    time.sleep(0.5)

    print(f"Click en zona neutral ({neutral_x}, {neutral_y}) para capturar DESPUÉS...")
    pyautogui.click(neutral_x, neutral_y)
    time.sleep(0.3)

    print("Capturando DESPUÉS del scroll...")
    after = pyautogui.screenshot(region=(read_x1, read_y1, read_x2 - read_x1, read_y2 - read_y1))
    after_text = pytesseract.image_to_string(after, lang='spa')
    print(f"Texto DESPUÉS: '{after_text}'")

    if before_text != after_text:
        print("\n✓ El scroll SÍ cambió el contenido visible.")
    else:
        print("\n✗ El scroll NO cambió el contenido (posible problema).")

def menu():
    """Menú interactivo"""
    print("\n" + "="*60)
    print("PROGRAMA DE PRUEBA: SCROLL Y NAVEGACIÓN")
    print("="*60)
    print("\nSelecciona un test para ejecutar:")
    print("  1) Test básico (scroll -600 x7)")
    print("  2) Test con moveTo previo")
    print("  3) Test con valores variados")
    print("  4) Test con delays largos (0.25s)")
    print("  5) Test agresivo (scroll -1000 x5)")
    print("  6) Test con keyboard (Page Down)")
    print("  7) Test combinado (scroll + keyboard)")
    print("  8) Test con detección OCR (NUEVO)")
    print("  9) Test debug visual (NUEVO)")
    print("  10) Ejecutar TODOS los tests")
    print("  0) Salir")
    print("="*60)

def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    tests = [
        test_basic_scroll,
        test_scroll_with_moveto,
        test_scroll_with_different_values,
        test_scroll_with_longer_delays,
        test_scroll_aggressive,
        test_scroll_with_keyboard,
        test_scroll_combined,
        test_scroll_with_ocr_detection,
        test_scroll_debug_visual,
    ]

    for test_func in tests:
        try:
            test_func()
            print(f"Esperando 2 segundos antes del siguiente test...")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n✗ Tests interrumpidos por el usuario.")
            break
        except Exception as e:
            print(f"\n✗ Error en {test_func.__name__}: {e}")

    print("\n✓ Todos los tests completados.")

if __name__ == "__main__":
    try:
        while True:
            menu()
            choice = input("\nOpción: ").strip()

            if choice == "0":
                print("Saliendo...")
                break
            elif choice == "1":
                test_basic_scroll()
            elif choice == "2":
                test_scroll_with_moveto()
            elif choice == "3":
                test_scroll_with_different_values()
            elif choice == "4":
                test_scroll_with_longer_delays()
            elif choice == "5":
                test_scroll_aggressive()
            elif choice == "6":
                test_scroll_with_keyboard()
            elif choice == "7":
                test_scroll_combined()
            elif choice == "8":
                test_scroll_with_ocr_detection()
            elif choice == "9":
                test_scroll_debug_visual()
            elif choice == "10":
                run_all_tests()
            else:
                print("Opción no válida. Intenta de nuevo.")

            input("\nPresiona Enter para volver al menú...")

    except KeyboardInterrupt:
        print("\n\nAbortado por el usuario (Ctrl+C).")
    except pyautogui.FailSafeException:
        print("\n\nAbortado por FailSafe (ratón en esquina superior izquierda).")
    except Exception as e:
        print(f"\n\nError: {e}")
