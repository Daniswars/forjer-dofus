import time
import pytesseract
import pyautogui
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'
from tkinter import messagebox
import Correo

def verificar_exito():
    time.sleep(1)

    x1, x2 = 1520, 1709
    y1, y2 = 767, 809

    captura_rectangulo = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    texto_rectangulo = pytesseract.image_to_string(captura_rectangulo, lang='eng', config='--psm 6')

    #print(texto_rectangulo_2)
    print("Leyendo si exito...")
    print(texto_rectangulo)

    if "AP" in texto_rectangulo or "PM" in texto_rectangulo or "PA" in texto_rectangulo or "alcance" in texto_rectangulo or "inv" in texto_rectangulo:
    #if "1PA" in texto_rectangulo or "1PM" in texto_rectangulo or "1PA":
        #print(texto_rectangulo)
        exito = True
        Correo.send_mail("Exito", 1)
    else:
        exito = False

    return exito