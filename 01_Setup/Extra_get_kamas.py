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
    """
    # Remove periods, spaces, and commas, then find all digits
    cleaned_text = text.replace('.', '').replace(' ', '').replace(',', '')
    print(f"DEBUG_OCR: Cleaned text for number extraction: '{cleaned_text}'")
    numbers = re.findall(r'\d+', cleaned_text)
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            print(f"ERROR_OCR: Could not convert '{numbers[0]}' to integer. Returning 0.")
            return 0
    print(f"DEBUG_OCR: No number found in text: '{text}'. Returning 0.")
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
    Includes pre-processing, multiple retries for accuracy, and a sanity check.
    """
    print("\nDEBUG_GET_KAMAS: Starting kamas and rune value retrieval...")

    # Wait for the 'maguear' text to confirm the correct screen state
    if not wait_for_maguear_text():
        print("ERROR_GET_KAMAS: 'maguear' text not found. Aborting kamas retrieval.")
        return 0 # Return 0 or handle error as appropriate

    time.sleep(1) # Give a moment after ensuring 'maguear' text is present

    # Coordinates for Runes and Kamas
    x1_runas, y1_runas = 2785, 1573
    x2_runas, y2_runas = 2909, 1600

    x1_kamas, y1_kamas = 2740, 1625
    x2_kamas, y2_kamas = 2932, 1658

    # Create folder for screenshots if it doesn't exist
    carpeta_capturas = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\capturas kamas"
    os.makedirs(carpeta_capturas, exist_ok=True)

    max_retries_ocr = 5
    for attempt in range(max_retries_ocr):
        print(f"DEBUG_GET_KAMAS: OCR attempt {attempt + 1}/{max_retries_ocr}...")

        # --- Mueve el ratón a la posición especificada antes de la captura ---
        pyautogui.moveTo(2697, 1075)
        time.sleep(0.2)
        # --- Fin de la modificación ---

        # Capture and preprocess image for Kamas
        capture_kamas_img = pyautogui.screenshot(
            region=(x1_kamas, y1_kamas, x2_kamas - x1_kamas, y2_kamas - y1_kamas))
        processed_kamas_img = preprocess_image(capture_kamas_img)
        text_kamas = pytesseract.image_to_string(processed_kamas_img, lang='eng', config='--psm 6').strip()
        ruta_kamas = os.path.join(carpeta_capturas, f"rectangulo_kamas_attempt_{attempt + 1}.png")
        processed_kamas_img.save(ruta_kamas)

        # Capture and preprocess image for Runes
        capture_runas_img = pyautogui.screenshot(
            region=(x1_runas, y1_runas, x2_runas - x1_runas, y2_runas - y1_runas))
        processed_runas_img = preprocess_image(capture_runas_img)
        text_runas = pytesseract.image_to_string(processed_runas_img, lang='eng', config='--psm 6').strip()
        ruta_runas = os.path.join(carpeta_capturas, f"rectangulo_runas_attempt_{attempt + 1}.png")
        processed_runas_img.save(ruta_runas)

        print(f"DEBUG_GET_KAMAS: Raw text from Kamas OCR: '{text_kamas}'")
        print(f"DEBUG_GET_KAMAS: Raw text from Runas OCR: '{text_runas}'")

        valor_kamas = extract_number(text_kamas)
        valor_runas = extract_number(text_runas)
        total_kamas = valor_runas + valor_kamas

        print(f"DEBUG_GET_KAMAS: Extracted Runas: {valor_runas}")
        print(f"DEBUG_GET_KAMAS: Extracted Kamas: {valor_kamas}")
        print(f"DEBUG_GET_KAMAS: Calculated Total: {total_kamas}")

        # Sanity check: if total_kamas is greater than 0 and within a reasonable range
        if total_kamas > 0 and total_kamas <= 150000000:
            print(f"DEBUG_GET_KAMAS: Valid total kamas detected: {total_kamas}. Returning.")
            return total_kamas
        elif total_kamas > 10000000000:
            print(f"WARNING_GET_KAMAS: Total kamas ({total_kamas}) exceeds sanity check of 150,000,000. Assuming OCR error and returning 0.")
            return 0 # Exit immediately if it's an absurdly high number

        time.sleep(1) # Short delay before next OCR attempt

    print("ERROR_GET_KAMAS: Failed to get a valid kamas reading after multiple attempts. Returning 0.")
    return 0

# Example usage (for testing this module directly)
if __name__ == "__main__":
    print("--- Running Extra_get_kamas.py directly for testing ---")
    current_kamas = get_kamas()
    print(f"Final Kamas read: {current_kamas}")
