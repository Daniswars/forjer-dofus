import pyautogui
from PIL import Image
import re
import time
import os

# Coordenadas de las filas (stats)
STAT_COORDS = [
    (1550, 756, 1863, 823),
    (1550, 823, 1863, 891),
    (1550, 891, 1863, 958),
    (1550, 958, 1863, 1026),
    (1550, 1026, 1863, 1097),
    (1550, 1097, 1863, 1161),
    (1550, 1161, 1863, 1235),
    (1550, 1235, 1863, 1302),
    (1550, 1302, 1863, 1367),
    (1550, 1367, 1863, 1437),
    (1550, 1437, 1863, 1506),
    (1550, 1506, 1863, 1574),
    (1550, 1574, 1863, 1644),
]

ONE_EQUIVALENTS = [
    "1", "l", "I", "L", "|", "!", "lalcance", "lalcanze", "lalcanse"
]

def normalize_number(text):
    t = text.strip().lower().replace('O', '0')
    if t in [s.lower() for s in ONE_EQUIVALENTS]:
        return 1
    if t.isdigit():
        return int(t)
    if re.fullmatch(r'[lI|!]+', text):
        return 1
    return None

def is_noise_line(line):
    return bool(re.search(r'(.)\1{4,}', line))

def extract_number_from_text(text):
    line = text.replace('O', '0').strip()
    if is_noise_line(line):
        return 0
    digit_groups = re.findall(r'\d+', line)
    if digit_groups:
        try:
            return int(digit_groups[-1])
        except ValueError:
            pass
    tokens = re.findall(r"[A-Za-z¡!|lI]+", line)
    for tok in tokens:
        n = normalize_number(tok)
        if n is not None:
            return n
    return 0

def capture_and_read_stats_easyocr(save_folder=None, lang='es', use_gpu=True):
    import easyocr
    import numpy as np
    start_time = time.time()
    reader = easyocr.Reader([lang], gpu=use_gpu)
    numbers = []
    raw_texts = []
    for idx, (x1, y1, x2, y2) in enumerate(STAT_COORDS):
        w, h = x2 - x1, y2 - y1
        img = pyautogui.screenshot(region=(x1, y1, w, h))
        if img.mode != "RGB":
            img = img.convert("RGB")
        if save_folder:
            os.makedirs(save_folder, exist_ok=True)
            img.save(os.path.join(save_folder, f"stat_{idx+1}.png"))
        img_np = np.array(img)
        result = reader.readtext(img_np, detail=0)
        text = " ".join(result)
        raw_texts.append(text)
        num = extract_number_from_text(text)
        numbers.append(num)
    elapsed = time.time() - start_time
    print(f"Tiempo transcurrido en captura y OCR (easyocr): {elapsed:.2f} segundos")
    print("Texto OCR bruto por stat:")
    for i, t in enumerate(raw_texts):
        print(f"Stat {i+1}: {t.strip()}")
    print("Números extraídos:", numbers)
    return numbers, raw_texts

if __name__ == "__main__":
    print("Preparando captura de stats individuales...")
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = os.path.join(desktop, "capturas_mage_stats")
        nums, raws = capture_and_read_stats_easyocr(save_folder=folder, lang='es', use_gpu=True)
    except KeyboardInterrupt:
        print("Interrupción por usuario.")
    except Exception as exc:
        print("Error:", exc)