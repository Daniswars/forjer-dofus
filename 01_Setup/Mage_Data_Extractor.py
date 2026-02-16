import pyautogui
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import re
import time
import os
import pytesseract
import concurrent.futures

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
    t = (text or "").strip().lower().replace('O', '0')
    if t in [s.lower() for s in ONE_EQUIVALENTS]:
        return 1
    if t.isdigit():
        return int(t)
    if re.fullmatch(r'[lI|!]+', text or ""):
        return 1
    return None

def is_noise_line(line):
    return bool(re.search(r'(.)\1{4,}', (line or "")))

def preprocess_full_image(img, upscale=1.05):
    """
    Preprocesado ligero aplicado a la imagen completa:
    - convertir a L, autocontrast y contraste moderado
    - ligero sharpen y pequeño upscale para mejorar OCR
    - NO binarizamos (mejora precisión)
    """
    try:
        im = img.convert("L")
        im = ImageOps.autocontrast(im, cutoff=1)
        im = ImageEnhance.Contrast(im).enhance(1.2)
        im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=100, threshold=1))
        if upscale and (abs(upscale - 1.0) > 0.01):
            new_w = max(1, int(im.width * upscale))
            new_h = max(1, int(im.height * upscale))
            im = im.resize((new_w, new_h), Image.BILINEAR)
        return im
    except Exception:
        try:
            return img.convert("L")
        except Exception:
            return img

def ocr_stat_image_config(img, lang='spa', config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'):
    try:
        return pytesseract.image_to_string(img, lang=lang, config=config)
    except Exception:
        return pytesseract.image_to_string(img, lang='eng', config=config)

def extract_number_from_text(text):
    line = (text or "").replace('O', '0').strip()
    if is_noise_line(line):
        return 0
    line_clean = re.sub(r'[.,\s]', '', line)
    digit_groups = re.findall(r'\d+', line_clean)
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

def capture_and_read_stats(save_folder=None, lang='spa', num_stats=None, workers=8):
    """
    Captura única de pantalla + OCR por crop usando paralelismo.
    - Si num_stats se proporciona, solo procesa las primeras num_stats filas de STAT_COORDS.
    - workers: número de hilos para ThreadPoolExecutor.
    - Preprocesado aplicado a imagen completa (una vez).
    - OCR escalonado por crop: 1) digits-only psm7, 2) digits-only psm6, 3) general psm6.
    Devuelve (numbers:list[int], raw_texts:list[str]) y hace print con los valores leídos.
    """
    start_time = time.time()
    numbers = []
    raw_texts = []

    coords = STAT_COORDS if num_stats is None else STAT_COORDS[:max(0, int(num_stats))]
    if not coords:
        return [], []

    # bounding box sobre coords usados
    min_x = min(x1 for (x1, y1, x2, y2) in coords)
    min_y = min(y1 for (x1, y1, x2, y2) in coords)
    max_x = max(x2 for (x1, y1, x2, y2) in coords)
    max_y = max(y2 for (x1, y1, x2, y2) in coords)
    total_w = max_x - min_x
    total_h = max_y - min_y

    # UNA sola captura (rápida) y un único preprocesado
    full_img = pyautogui.screenshot(region=(min_x, min_y, total_w, total_h))
    if full_img.mode != "RGB":
        full_img = full_img.convert("RGB")

    processed_full = preprocess_full_image(full_img, upscale=1.05)

    # preparar cajas relativas
    rel_boxes = [(x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y) for (x1, y1, x2, y2) in coords]

    def _process_crop(rel_box):
        try:
            crop = processed_full.crop(rel_box)
        except Exception:
            crop = full_img.crop((rel_box[0] + min_x, rel_box[1] + min_y, rel_box[2] + min_x, rel_box[3] + min_y))
            try:
                crop = crop.convert("L")
            except Exception:
                pass

        # 1) digits-only psm7
        text = ocr_stat_image_config(crop, lang=lang, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789')
        num = extract_number_from_text(text)
        if num != 0:
            return num, text

        # 2) digits-only psm6
        text2 = ocr_stat_image_config(crop, lang=lang, config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789')
        num2 = extract_number_from_text(text2)
        if num2 != 0:
            return num2, text2

        # 3) fallback general psm6
        text3 = ocr_stat_image_config(crop, lang=lang, config='--oem 3 --psm 6')
        num3 = extract_number_from_text(text3)
        return num3, text3

    # ejecutar OCR en paralelo manteniendo orden con executor.map
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_process_crop, rel_boxes))

    for num, text in results:
        numbers.append(num)
        raw_texts.append(text)

    elapsed = time.time() - start_time
    # prints de depuración: valores y textos leídos
    print(f"Tiempo captura+OCR: {elapsed:.2f}s - nonzeros: {sum(1 for v in numbers if v!=0)}")
    print("Valores extraídos:", numbers)
    print("Textos OCR brutos por fila:")
    for idx, txt in enumerate(raw_texts, start=1):
        print(f"  Stat {idx}: {repr(txt)}")
    return numbers, raw_texts

if __name__ == "__main__":
    print("Preparando captura de stats individuales...")
    try:
        nums, raws = capture_and_read_stats(save_folder=None, lang='spa', num_stats=None, workers=8)
        print("Resultado final:", nums)
    except KeyboardInterrupt:
        print("Interrupción por usuario.")
    except Exception as exc:
        print("Error:", exc)