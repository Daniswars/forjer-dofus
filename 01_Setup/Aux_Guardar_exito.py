import pyautogui
import time
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# Factor global para ralentizar/ajustar todos los sleeps de este script.
# Cambia este valor a 1.0 para comportamiento original, >1.0 para más lento.
SLOW_FACTOR = 2

def wait_for_text_in_regions(target_text, regions, max_tries=30, pause=0.5):
    """
    Toma screenshots de las regiones (x,y,w,h) y busca target_text usando pytesseract.
    Devuelve True si lo encuentra (en cualquier región) dentro de max_tries intentos.
    """
    target_l = target_text.lower()
    for intento in range(1, max_tries + 1):
        for (x, y, w, h) in regions:
            try:
                img = pyautogui.screenshot(region=(x, y, w, h))
                txt = pytesseract.image_to_string(img).lower()
                # debug mínimo
                print(f"DEBUG_OCR intento {intento} region ({x},{y},{w},{h}) -> '{txt.strip()[:60]}'")
                if target_l in txt:
                    print(f"DEBUG_OCR: Encontrado '{target_text}' en intento {intento} en region ({x},{y})")
                    return True
            except Exception as e:
                print("WARNING: fallo OCR/región:", e)
        time.sleep(pause * SLOW_FACTOR)
    return False

def perform_dofus_sequence():
    """
    Executes a specific sequence of actions in Dofus:
    Presses Escape, clicks a precise location (replacing 'H' press),
    waits to detect 'Merkasako' in small on-screen regions (hasta 30 intentos),
    then continues the sequence.
    """
    print("Starting Dofus action sequence...")

    # Press Escape
    print("Pressing Escape...")
    pyautogui.click(x = 2947, y = 517)
    time.sleep(0.7 * SLOW_FACTOR) # Short delay to ensure the game registers the input

    # Click at X=3813, Y=331 (replaces 'H' press)
    print("Clicking at X=3813, Y=331 (replacing 'H' key)...")
    pyautogui.click(x=3813, y=331)
    time.sleep(0.6 * SLOW_FACTOR) # breve pausa antes de empezar a comprobar texto

    # Esperar a leer "Merkasako" en una de las dos regiones (hasta 30 intentos)
    regions_to_check = [
        (4, 62, 220, 36),    # X=4,Y=62, ancho/alto aproximado para la región
        (192, 101, 220, 36)  # X=192,Y=101
    ]
    found = wait_for_text_in_regions("merkasako", regions_to_check, max_tries=30, pause=0.5)
    if not found:
        pyautogui.alert("No se detectó 'Merkasako' tras 30 intentos. Abortando secuencia.")
        print("Abortando perform_dofus_sequence: 'Merkasako' no detectado.")
        return

    # Click at the first position (from original script)
    print("Clicking at X=1590, Y=1021...")
    pyautogui.click(x=1590, y=1021)
    time.sleep(2 * SLOW_FACTOR) # Delay after the click

    pyautogui.click(x=1370, y=650)
    time.sleep(1 * SLOW_FACTOR)  # Delay after the click

    # Double click at the second position
    print("Double clicking at X=1490, Y=732...")
    pyautogui.moveTo(x=2150, y=722)
    time.sleep(1 * SLOW_FACTOR)
    pyautogui.click(clicks=2, interval=0.1 * SLOW_FACTOR)
    time.sleep(1 * SLOW_FACTOR)
    pyautogui.click(x=2630, y=513)
    time.sleep(2 * SLOW_FACTOR)  # Delay after the click

    # Click at X=3813, Y=331 again (replaces 'H' press)
    print("Clicking at X=3813, Y=331 again (replacing 'H' key)...")
    pyautogui.click(x=3813, y=331)
    time.sleep(1.2 * SLOW_FACTOR)

    print("Dofus action sequence completed.")

# --- How to Run the Script ---
if __name__ == "__main__":
    # IMPORTANT: Ensure your Dofus window is active and in focus BEFORE this countdown ends.
    print("Script will start in 5 seconds. Please switch to your Dofus window NOW!")
    time.sleep(5 * SLOW_FACTOR) # Gives you time to switch to the Dofus window

    perform_dofus_sequence()