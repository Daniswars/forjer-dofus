import pyautogui
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import re
import time
import os
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# Coordenadas de las filas (stats)
STAT_COORDS = [
    (1550, 756, 1750, 823),
    (1550, 823, 1750, 891),
    (1550, 891, 1750, 958),
    (1550, 958, 1750, 1026),
    (1550, 1026, 1750, 1097),
    (1550, 1097, 1750, 1161),
    (1550, 1161, 1750, 1235),
    (1550, 1235, 1750, 1302),
    (1550, 1302, 1750, 1367),
    (1550, 1367, 1750, 1437),
    (1550, 1437, 1750, 1506),
    (1550, 1506, 1750, 1574),
    (1550, 1574, 1750, 1644),
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

def preprocess_for_ocr(img, upscale=1.3):
    """
    Preprocesado más ligero para acelerar OCR:
     - grayscale, contraste moderado, ligera nitidez
     - upscale moderado (1.3) para ayudar a tesseract sin costar tanto
     - umbral binario rápido
    """
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(1.6)
    # sharpening leve (menos costoso)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
    if upscale != 1:
        new_w = max(1, int(img.width * upscale))
        new_h = max(1, int(img.height * upscale))
        img = img.resize((new_w, new_h), Image.BILINEAR)
    img = img.point(lambda p: 255 if p > 140 else 0)
    return img

def ocr_stat_image(img, lang='spa', digits_only=True):
    """
    Usa config específica para dígitos cuando sea posible (más rápido y fiable).
    """
    if digits_only:
        config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=config)
        except Exception:
            text = pytesseract.image_to_string(img, lang='eng', config=config)
    else:
        try:
            text = pytesseract.image_to_string(img, lang=lang, config='--oem 3 --psm 6')
        except Exception:
            text = pytesseract.image_to_string(img, lang='eng', config='--oem 3 --psm 6')
    return text

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

def capture_and_read_stats(save_folder=None, lang='spa'):
    """
    Single screenshot + crop per stat. OCR digits-only por defecto,
    fallback laxo SOLO para filas que quedaron en 0.
    """
    start_time = time.time()
    numbers = []
    raw_texts = []

    # bounding box
    min_x = min(x1 for (x1, y1, x2, y2) in STAT_COORDS)
    min_y = min(y1 for (x1, y1, x2, y2) in STAT_COORDS)
    max_x = max(x2 for (x1, y1, x2, y2) in STAT_COORDS)
    max_y = max(y2 for (x1, y1, x2, y2) in STAT_COORDS)
    total_w = max_x - min_x
    total_h = max_y - min_y

    full_img = pyautogui.screenshot(region=(min_x, min_y, total_w, total_h))
    if full_img.mode != "RGB":
        full_img = full_img.convert("RGB")

    # process each stat crop (faster)
    crops = []
    for (x1, y1, x2, y2) in STAT_COORDS:
        rel_box = (x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y)
        crops.append(full_img.crop(rel_box))

    # first pass: digits-only OCR
    for crop in crops:
        proc = preprocess_for_ocr(crop, upscale=1.3)
        text = ocr_stat_image(proc, lang=lang, digits_only=True)
        num = extract_number_from_text(text)
        raw_texts.append(text)
        numbers.append(num)

    # fallback laxo SOLO para filas que quedaron en 0 (reduce trabajo)
    nonzeros = sum(1 for v in numbers if v != 0)
    if nonzeros < max(1, len(STAT_COORDS)//6):
        for idx, val in enumerate(numbers):
            if val == 0:
                crop = crops[idx]
                proc = preprocess_for_ocr(crop, upscale=1.3)
                text_loose = ocr_stat_image(proc, lang=lang, digits_only=False)
                n2 = extract_number_from_text(text_loose)
                if n2 != 0:
                    raw_texts[idx] = text_loose
                    numbers[idx] = n2

    elapsed = time.time() - start_time
    print(f"Tiempo captura+OCR: {elapsed:.2f}s - nonzeros: {sum(1 for v in numbers if v!=0)}")
    return numbers, raw_texts

if __name__ == "__main__":
    print("Preparando captura de stats individuales...")
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = os.path.join(desktop, "capturas_mage_stats")
        nums, raws = capture_and_read_stats(save_folder=folder, lang='spa')
    except KeyboardInterrupt:
        print("Interrupción por usuario.")
    except Exception as exc:
        print("Error:", exc)