import time
import pytesseract
import pyautogui
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'
from tkinter import messagebox
import Correo

def verify_success():
    """
    Checks if the exo was successful by reading the specified screen area.
    Returns True if found keywords ("AP", "PM", "PA", "range", "invocation"), otherwise False.
    """
    time.sleep(1)

    x1, x2 = 1520, 1709
    y1, y2 = 767, 809

    screenshot_area = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    text_area = pytesseract.image_to_string(screenshot_area, lang='eng', config='--psm 6')

    print("Reading for success...")
    print(text_area)

    # Keywords for success
    if ("AP" in text_area or "PM" in text_area or "PA" in text_area or
        "range" in text_area or "invocation" in text_area):
        success = True
        Correo.send_mail("Success", 1)
    else:
        success = False

    return success

if __name__ == "__main__":
    result = verify_success()
    print(f"Exo success: {result}")
