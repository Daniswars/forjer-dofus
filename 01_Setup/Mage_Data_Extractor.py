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

def preprocess_for_ocr(img, upscale=2):
    # grayscale
    img = img.convert("L")
    # increase contrast
    img = ImageEnhance.Contrast(img).enhance(1.8)
    # slight sharpening
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    # upscale to help tesseract on small fonts
    if upscale != 1:
        img = img.resize((img.width * upscale, img.height * upscale), Image.BILINEAR)
    # simple binary threshold to reduce noise
    img = img.point(lambda p: 255 if p > 150 else 0)
    return img

def ocr_stat_image(img, lang='spa', digits_only=True):
    """
    Usa config específica para dígitos cuando sea posible (más rápido y fiable).
    """
    if digits_only:
        config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=config)
        except Exception:
            text = pytesseract.image_to_string(img, lang='eng', config=config)
    else:
        try:
            text = pytesseract.image_to_string(img, lang=lang, config='--psm 6')
        except Exception:
            text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
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
    Optimized: take a single screenshot covering all STAT_COORDS, then crop per stat.
    """
    start_time = time.time()
    numbers = []
    raw_texts = []

    # compute bounding box covering all STAT_COORDS
    min_x = min(x1 for (x1, y1, x2, y2) in STAT_COORDS)
    min_y = min(y1 for (x1, y1, x2, y2) in STAT_COORDS)
    max_x = max(x2 for (x1, y1, x2, y2) in STAT_COORDS)
    max_y = max(y2 for (x1, y1, x2, y2) in STAT_COORDS)
    total_w = max_x - min_x
    total_h = max_y - min_y

    # single screenshot of the whole area
    full_img = pyautogui.screenshot(region=(min_x, min_y, total_w, total_h))
    if full_img.mode != "RGB":
        full_img = full_img.convert("RGB")

    # optional save folder
    if save_folder:
        os.makedirs(save_folder, exist_ok=True)
        full_img.save(os.path.join(save_folder, "stats_full.png"))

    for idx, (x1, y1, x2, y2) in enumerate(STAT_COORDS):
        # crop relative to full_img
        rel_box = (x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y)
        crop = full_img.crop(rel_box)

        # faster preprocessing tuned for digits
        proc = preprocess_for_ocr(crop, upscale=2)

        if save_folder:
            proc.save(os.path.join(save_folder, f"stat_{idx+1}_proc.png"))

        # try digits-only OCR first (psm7 + whitelist)
        text = ocr_stat_image(proc, lang=lang, digits_only=True)
        num = extract_number_from_text(text)

        # if digit extraction failed (0 could be valid but we try fallback when OCR returns no text)
        if num == 0:
            # fallback to looser OCR (allow words) once
            text_loose = ocr_stat_image(proc, lang=lang, digits_only=False)
            # prefer the looser text if it has something
            if text_loose.strip():
                text = text_loose
                num = extract_number_from_text(text_loose)

        raw_texts.append(text)
        numbers.append(num)

    elapsed = time.time() - start_time
    print(f"Tiempo transcurrido en captura y OCR: {elapsed:.2f} segundos")
    # imprimir texto por stat breve (solo primeras 80 chars)
    print("Texto OCR bruto por stat:")
    for i, t in enumerate(raw_texts):
        print(f"Stat {i+1}: {t.strip()[:80]}")
    print("Números extraídos:", numbers)
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