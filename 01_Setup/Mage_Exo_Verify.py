import time
import pytesseract
import pyautogui
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'
import Extra_Correo

# NUEVO: último tipo detectado por OCR (para consumo externo)
LAST_EXO_TYPE = None

def _detect_exo_type(text: str):
    t = (text or "").upper()
    # prioridad de detección
    if "PA" in t or "AP" in t:
        return "PA"
    if "PM" in t:
        return "PM"
    return None

def verify_success():
    """
    Checks if the exo was successful by reading the specified screen area.
    Returns True if found keywords ("AP", "PM", "PA", "range", "invocation"), otherwise False.
    """
    global LAST_EXO_TYPE
    time.sleep(1)

    x1, x2 = 1520, 1709
    y1, y2 = 767, 809

    screenshot_area = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    text_area = pytesseract.image_to_string(screenshot_area, lang='eng', config='--psm 6')

    print("Reading for success...")
    print(text_area)

    exo_type = _detect_exo_type(text_area)
    LAST_EXO_TYPE = exo_type

    if exo_type is not None:
        success = True
        # opcional: avisar con tipo detectado
        try:
            Extra_Correo.send_mail("Success", f"Exito {exo_type}")
        except Exception:
            pass
    else:
        success = False

    return success

if __name__ == "__main__":
    result = verify_success()
    print(f"Exo success: {result} | tipo={LAST_EXO_TYPE}")
