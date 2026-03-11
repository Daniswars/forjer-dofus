import time
import pytesseract
import pyautogui
import re
from PIL import Image, ImageEnhance, ImageOps
import os

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

def preprocess_image(image):
    """
    Preprocesses an image for better OCR accuracy.
    Converts to grayscale, enhances contrast and sharpness.
    """
    # Convert image to grayscale
    image = ImageOps.grayscale(image)
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2) # Increased contrast
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2) # Increased sharpness
    return image

def extract_number(text):
    """
    Extracts an integer number from a string, removing common non-numeric characters.
    Returns 0 if no number is found.
    MEJORADO: maneja separadores de miles mixtos (puntos, comas, espacios).
    """
    raw = text.strip()
    print(f"DEBUG_OCR: Raw text recibido: '{raw}'")

    # Eliminar caracteres no numéricos excepto punto y coma (posibles separadores)
    # Detectar si hay coma decimal (ej: 1.234,56) o punto decimal (ej: 1,234.56)
    # En Dofus los kamas nunca tienen decimales -> eliminar TODOS los separadores y quedarse con dígitos
    cleaned = re.sub(r'[^\d]', '', raw)
    print(f"DEBUG_OCR: Cleaned text (solo dígitos): '{cleaned}'")

    if cleaned:
        try:
            return int(cleaned)
        except ValueError:
            print(f"ERROR_OCR: No se pudo convertir '{cleaned}' a int. Devolviendo 0.")
            return 0
    print(f"DEBUG_OCR: No se encontró número en: '{raw}'. Devolviendo 0.")
    return 0

def wait_for_maguear_text():
    """
    Waits until the text 'maguear' is detected within the specified rectangle.
    This ensures the 'maguear' window is active and ready.
    """
    # Specific coordinates for the 'maguear' text region: X=1446 Y 487 / X=1601 Y =534
    MAGUEAR_TEXT_REGION = (1446, 487, 1601 - 1446, 534 - 487) # (x, y, width, height)
    # Calculate width and height for clarity
    region_x, region_y, region_width, region_height = MAGUEAR_TEXT_REGION

    print(f"DEBUG_WAIT: Waiting for 'maguear' text to appear in region: ({region_x}, {region_y}, {region_width}, {region_height})...")
    max_retries = 30 # Try for up to 30 * 0.5 = 15 seconds
    retry_interval = 0.5 # seconds

    for i in range(max_retries):
        # Capture and preprocess the region
        img = pyautogui.screenshot(region=MAGUEAR_TEXT_REGION)
        img = preprocess_image(img)
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 7').strip().lower() # psm 7 for single text line

        print(f"DEBUG_WAIT: Retry {i+1}/{max_retries} - Text detected: '{text}'")

        if "maguear" in text:
            print("DEBUG_WAIT: 'maguear' text detected. Continuing.")
            return True
        time.sleep(retry_interval)

    print("ERROR_WAIT: 'maguear' text not detected after multiple retries. Program may not proceed as expected.")
    return False

def get_kamas():
    """
    Reads the current kamas and rune count from the Dofus interface.
    MEJORADO: validación por consistencia entre reintentos consecutivos.
    """
    print("\nDEBUG_GET_KAMAS: Starting kamas and rune value retrieval...")
    print(f"DEBUG_GET_KAMAS: Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if not wait_for_maguear_text():
        print("ERROR_GET_KAMAS: 'maguear' text not found. Aborting kamas retrieval.")
        return 0

    time.sleep(1)

    x1_runas, y1_runas = 2785, 1573
    x2_runas, y2_runas = 2909, 1600
    x1_kamas, y1_kamas = 2740, 1625
    x2_kamas, y2_kamas = 2932, 1658

    carpeta_capturas = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\capturas kamas"
    os.makedirs(carpeta_capturas, exist_ok=True)

    UPPER_LIMIT = 100_000_000_000
    # Mínimo razonable: 1000 kamas (evitar lecturas basura como 1, 0, 123...)
    LOWER_LIMIT = 1_000

    max_retries_ocr = 6
    historial = []  # guardar lecturas para consistencia

    for attempt in range(max_retries_ocr):
        print(f"DEBUG_GET_KAMAS: OCR attempt {attempt + 1}/{max_retries_ocr}...")

        pyautogui.click(2697, 1075)
        time.sleep(0.3)

        # Capturar kamas
        capture_kamas_img = pyautogui.screenshot(
            region=(x1_kamas, y1_kamas, x2_kamas - x1_kamas, y2_kamas - y1_kamas))
        processed_kamas_img = preprocess_image(capture_kamas_img)
        text_kamas = pytesseract.image_to_string(processed_kamas_img, lang='eng', config='--psm 6').strip()
        ruta_kamas = os.path.join(carpeta_capturas, f"rectangulo_kamas_attempt_{attempt + 1}.png")
        processed_kamas_img.save(ruta_kamas)

        # Capturar runas
        capture_runas_img = pyautogui.screenshot(
            region=(x1_runas, y1_runas, x2_runas - x1_runas, y2_runas - y1_runas))
        processed_runas_img = preprocess_image(capture_runas_img)
        text_runas = pytesseract.image_to_string(processed_runas_img, lang='eng', config='--psm 6').strip()
        ruta_runas = os.path.join(carpeta_capturas, f"rectangulo_runas_attempt_{attempt + 1}.png")
        processed_runas_img.save(ruta_runas)

        print(f"DEBUG_GET_KAMAS: Texto crudo Kamas: '{text_kamas}'")
        print(f"DEBUG_GET_KAMAS: Texto crudo Runas: '{text_runas}'")

        valor_kamas = extract_number(text_kamas)
        valor_runas = extract_number(text_runas)
        total_kamas = valor_runas + valor_kamas

        print(f"DEBUG_GET_KAMAS: Runas={valor_runas} | Kamas={valor_kamas} | Total={total_kamas}")

        # Descartar lecturas basura (ambos 0 o total fuera de rango)
        if total_kamas < LOWER_LIMIT or total_kamas > UPPER_LIMIT:
            print(f"WARNING_GET_KAMAS: Total {total_kamas} fuera de rango [{LOWER_LIMIT}, {UPPER_LIMIT}]. Descartando.")
            time.sleep(1)
            continue

        historial.append(total_kamas)
        print(f"DEBUG_GET_KAMAS: Historial de lecturas válidas: {historial}")

        # Aceptar si dos lecturas consecutivas son iguales o muy similares (±1% de diferencia)
        if len(historial) >= 2:
            a, b = historial[-2], historial[-1]
            diff_pct = abs(a - b) / max(a, b) * 100
            print(f"DEBUG_GET_KAMAS: Diferencia entre últimas 2 lecturas: {diff_pct:.2f}%")
            if diff_pct <= 1.0:
                # Usar el valor más bajo de los dos como lectura conservadora
                resultado = min(a, b)
                print(f"DEBUG_GET_KAMAS: Lecturas consistentes. Devolviendo: {resultado}")
                return resultado

        # Si es el último intento y hay al menos una lectura válida, devolver la mediana
        if attempt == max_retries_ocr - 1 and historial:
            historial_sorted = sorted(historial)
            mediana = historial_sorted[len(historial_sorted) // 2]
            print(f"WARNING_GET_KAMAS: No se obtuvo consistencia. Devolviendo mediana del historial: {mediana}")
            return mediana

        time.sleep(1)

    print("ERROR_GET_KAMAS: No se pudo obtener lectura válida. Devolviendo 0.")
    return 0

# Example usage (for testing this module directly)
if __name__ == "__main__":
    print("--- Running Extra_get_kamas.py directly for testing ---")
    current_kamas = get_kamas()
    print(f"Final Kamas read: {current_kamas}")
