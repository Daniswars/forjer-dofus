import os
import time
import pytesseract
import pyautogui
from PIL import Image
# Reutiliza funciones desde get_kamas.py
from get_kamas import preprocess_image, wait_for_maguear_text

# Asegura la ruta al ejecutable de Tesseract (requerido por el usuario)
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# Región solicitada: X1=3005,Y1=506  X2=3383,Y2=538
REGION_ITEM = (3005, 506, 3383 - 3005, 538 - 506)  # (x, y, width, height)


def clean_text(text: str) -> str:
    """Limpia el texto OCR básico (quita saltos y espacios extremos)."""
    return text.replace('\n', ' ').strip()

def read_new_item_name(wait_for_maguear: bool = True, save_screenshot: bool = True,
                       click_before: bool = True, click_pos=(2470, 729)) -> str:
    """
    Captura el rectángulo definido y devuelve el texto dentro.
    Si wait_for_maguear es True intentará usar wait_for_maguear_text() antes de capturar.
    Si click_before es True hará click en click_pos antes de la captura (por defecto (2470,729)).
    """
    if click_before:
        try:
            pyautogui.click(2346, 662)
            time.sleep(1)
            pyautogui.click(2470, 729)
            # pequeña pausa para que la UI responda al click
            time.sleep(0.15)
        except Exception as e:
            print(f"WARNING: Error haciendo click en {click_pos}: {e}")

    if wait_for_maguear:
        # Intentar asegurarse del estado correcto de la UI (reutiliza la función del otro módulo)
        try:
            ok = wait_for_maguear_text()
            if not ok:
                # continúa igual pero avisa
                print("WARNING: wait_for_maguear_text() no confirmó el estado; procediendo de todas formas.")
        except Exception as e:
            print(f"WARNING: Error llamando wait_for_maguear_text(): {e}. Procediendo de todas formas.")

    # Pequeña pausa para estabilidad
    time.sleep(0.3)

    # Captura de pantalla de la región
    img = pyautogui.screenshot(region=REGION_ITEM)
    processed = preprocess_image(img)

    # OCR: psm 7 para línea única
    raw_text = pytesseract.image_to_string(processed, lang='eng', config='--psm 7')
    result_text = clean_text(raw_text)

    # Guardar captura si se solicita
    if save_screenshot:
        carpeta = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\capturas item_name"
        os.makedirs(carpeta, exist_ok=True)
        timestamp = int(time.time() * 1000)
        ruta = os.path.join(carpeta, f"item_name_{timestamp}.png")
        processed.save(ruta)
        print(f"DEBUG: Captura guardada en: {ruta}")

    print(f"DEBUG_OCR: Texto bruto: '{raw_text}' -> Limpio: '{result_text}'")

    time.sleep(1)
    pyautogui.click(2355, 792)
    return result_text

# Prueba rápida si se ejecuta directamente
if __name__ == "__main__":
    # Hace click en (2470,729) antes de leer y guarda la captura
    texto = read_new_item_name(wait_for_maguear=True, save_screenshot=True, click_before=True)
    print(f"Texto detectado en rectángulo: '{texto}'")

    # --- NUEVO: Captura directa de REGION_ITEM para inspección manual ---
    carpeta_debug = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\capturas item_name"
    os.makedirs(carpeta_debug, exist_ok=True)
    timestamp_debug = int(time.time() * 1000)
    ruta_debug = os.path.join(carpeta_debug, f"REGION_ITEM_raw_{timestamp_debug}.png")
    img_raw = pyautogui.screenshot(region=REGION_ITEM)
    img_raw.save(ruta_debug)
    print(f"DEBUG: Captura RAW de REGION_ITEM guardada en: {ruta_debug}")
