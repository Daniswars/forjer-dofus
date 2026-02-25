import os
import time
import re
import pyautogui
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from pytesseract import Output

# Configuración Tesseract (ajusta si hace falta)
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# Anchors solicitados (X,Y) como esquina superior izquierda
ANCHORS = [
    (1995, 758),
    (2246, 1643),
]

# Parámetros de recorte por fila (ajustables según UI)
ROWS = 13
ROW_WIDTH = 110    # ancho del recorte por fila
ROW_HEIGHT = 67    # alto aproximado por fila
GAP = 0            # espacio vertical extra entre filas si existe

# Umbral para considerar "faltan runas"
THRESHOLD = 300

# Carpeta opcional para depuración
DEBUG_SAVE = False
DEBUG_FOLDER = "debug_runas"

def preprocess_crop(img):
    try:
        im = img.convert("L")
        im = ImageOps.autocontrast(im, cutoff=2)
        im = ImageEnhance.Contrast(im).enhance(1.2)
        im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=120, threshold=1))
        return im
    except Exception:
        return img

def parse_number_from_text(text):
    if not text:
        return 0
    t = str(text).replace('\r', '').replace('\n', '').replace('\\n', '')
    # normalizar O/o -> 0 y similares confusiones básicas
    t = t.replace('O', '0').replace('o', '0').replace(' ', '')
    # mantener sólo dígitos y signos (pero preferimos sólo dígitos)
    m = re.findall(r'\d+', t)
    if not m:
        return 0
    try:
        return int(m[-1])
    except Exception:
        return 0

def read_row_number(crop_img):
    proc = preprocess_crop(crop_img)
    # primero intentar psm 7 digits-only
    cfg_digits = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
    try:
        txt = pytesseract.image_to_string(proc, config=cfg_digits)
        n = parse_number_from_text(txt)
        if n != 0:
            return n, txt
    except Exception:
        pass
    # fallback psm 6 general
    try:
        txt2 = pytesseract.image_to_string(proc, config='--oem 3 --psm 6')
        n2 = parse_number_from_text(txt2)
        return n2, txt2
    except Exception:
        return 0, ""

def detectar_runas_faltantes(anchors=ANCHORS, rows=ROWS, row_w=ROW_WIDTH, row_h=ROW_HEIGHT, gap=GAP, threshold=THRESHOLD, debug=DEBUG_SAVE):
    if debug:
        os.makedirs(DEBUG_FOLDER, exist_ok=True)
    all_results = []
    for a_idx, (ax, ay) in enumerate(anchors, start=1):
        print(f"[Anchor {a_idx}] Capturando desde ({ax},{ay})")
        for i in range(rows):
            rx = ax
            ry = ay + i * (row_h + gap)
            try:
                crop = pyautogui.screenshot(region=(rx, ry, row_w, row_h))
            except Exception as e:
                print(f"  Fila {i+1}: error captura: {e}")
                all_results.append(((a_idx, i+1), 0, "ERR"))
                continue

            num, rawtxt = read_row_number(crop)
            if debug:
                try:
                    fname = os.path.join(DEBUG_FOLDER, f"anchor{a_idx}_fila{i+1}_{int(time.time())}.png")
                    crop.save(fname)
                except Exception:
                    pass

            if num <= threshold:
                print(f"[Anchor {a_idx}] Fila {i+1}: {num} -> Faltan runas (<= {threshold}) | OCR='{rawtxt}'")
            else:
                print(f"[Anchor {a_idx}] Fila {i+1}: {num}")
            all_results.append(((a_idx, i+1), num, rawtxt))
    return all_results

if __name__ == "__main__":
    print("Detectando runas faltantes...")
    try:
        detectar_runas_faltantes()
    except KeyboardInterrupt:
        print("Interrumpido por usuario.")
    except Exception as e:
        print("Error:", e)
