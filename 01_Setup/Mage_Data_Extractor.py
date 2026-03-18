import pyautogui
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import re
import time
import os
import pytesseract
import concurrent.futures
from pytesseract import Output

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# Coordenadas de las filas (stats)
general_x1 = 1552
general_x2 = 1610
STAT_COORDS = [
    (general_x1, 756, general_x2+50, 823),
    (general_x1, 823, general_x2, 891),
    (general_x1, 891, general_x2, 958),
    (general_x1, 958, general_x2, 1026),
    (general_x1, 1026, general_x2, 1097),
    (general_x1, 1097, general_x2, 1161),
    (general_x1, 1161, general_x2, 1235),
    (general_x1, 1235, general_x2, 1302),
    (general_x1, 1302, general_x2, 1367),
    (general_x1, 1367, general_x2, 1437),
    (general_x1, 1437, general_x2, 1506),
    (general_x1, 1506, general_x2, 1574),
    (general_x1, 1574, general_x2, 1644),
]

ONE_EQUIVALENTS = [
    "1", "l", "I", "L", "|", "!", "i", "lalc", "1alc", "talc"
]

def normalize_number(text):
    """
    Normaliza texto OCR a número entero.
    Reglas:
    1. Si texto vacío -> None
    2. Si contiene "alc" o "Alc" y empieza con O/0 -> 0 (caso "Oalc")
    3. Si es exactamente equivalente a "1" -> 1
    4. Si contiene "%r" -> 9 (regla específica)
    5. Normalizar O->0, l/I/L->1
    6. Extraer dígitos y convertir a int
    """
    if not text:
        return None

    t = str(text).replace('\r', '').replace('\n', '').replace('\\n', '').strip()
    if not t:
        return None

    t_lower = t.lower()

    # Caso especial: "Oalc", "0alc" -> 0
    if 'alc' in t_lower and (t_lower.startswith('o') or t_lower.startswith('0')):
        return 0

    # Caso especial: "%r" -> 9
    if t_lower == '%r' or t_lower == '% r':
        return 9

    # Caso exacto: equivalentes de "1"
    t_clean = t.replace(' ', '').lower()
    if t_clean in [x.lower() for x in ONE_EQUIVALENTS]:
        return 1

    # Normalización estándar
    t = t.replace('O', '0').replace('o', '0')
    t = t.replace('I', '1').replace('l', '1').replace('L', '1').replace('|', '1')

    # Extraer solo dígitos
    digits = re.sub(r'[^\d]', '', t)
    if not digits:
        return None

    try:
        return int(digits)
    except:
        return None

def is_noise_line(line):
    return bool(re.search(r'(.)\1{4,}', (line or "")))

def preprocess_full_image(img, upscale=1.05):
    """
    Preprocesado ligero aplicado a la imagen completa.
    """
    try:
        im = img.convert("L")
        im = ImageOps.autocontrast(im, cutoff=1)
        im = ImageEnhance.Contrast(im).enhance(1.25)
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
    """Extrae número de texto OCR usando normalize_number"""
    if not text:
        return 0

    line = str(text).replace('\r', '').replace('\n', '').replace('\\n', '').strip()

    if re.search(r'(.)\1{4,}', line):
        return 0

    num = normalize_number(line)
    return num if num is not None else 0

def _best_numeric_token_from_image(img, config):
    """
    Usa image_to_data para seleccionar el token numérico con mayor confianza.
    """
    try:
        data = pytesseract.image_to_data(img, config=config, output_type=Output.DICT)
        texts = data.get('text', [])
        confs = data.get('conf', [])
        best_num = None
        best_conf = -100
        best_text = ""

        for tok, conf in zip(texts, confs):
            if not tok or str(tok).strip() == "":
                continue

            n = normalize_number(tok)
            if n is not None:
                try:
                    conf_v = int(float(conf))
                except:
                    conf_v = -1

                if conf_v > best_conf:
                    best_conf = conf_v
                    best_num = n
                    best_text = str(tok).replace('\r', '').replace('\n', '').replace('\\n', '')

        if best_num is not None:
            return best_num, best_text, best_conf
    except:
        pass

    return 0, "", -100

def capture_and_read_stats(save_folder=None, lang='spa', num_stats=None, workers=8, debug_save_folder=None, item_stats=None):
    """
    Captura única de pantalla + OCR por crop usando paralelismo.
    """
    start_time = time.time()
    numbers = []
    raw_texts = []
    raw_texts_crudos = []

    coords = STAT_COORDS if num_stats is None else STAT_COORDS[:max(0, int(num_stats))]
    if not coords:
        return [], []

    # Determinar listas de máximos/minimos
    max_list = None
    min_list = None
    try:
        if item_stats is None:
            max_list = None
            min_list = None
        elif isinstance(item_stats, dict):
            max_list = item_stats.get("max")
            min_list = item_stats.get("min")
        elif isinstance(item_stats, (list, tuple)):
            max_list = list(item_stats)
            min_list = None
        else:
            max_list = getattr(item_stats, "max", None)
            min_list = getattr(item_stats, "min", None)
    except Exception:
        max_list = None
        min_list = None

    # Bounding box sobre coords usados
    min_x = min(x1 for (x1, y1, x2, y2) in coords)
    min_y = min(y1 for (x1, y1, x2, y2) in coords)
    max_x = max(x2 for (x1, y1, x2, y2) in coords)
    max_y = max(y2 for (x1, y1, x2, y2) in coords)
    total_w = max_x - min_x
    total_h = max_y - min_y

    if debug_save_folder:
        try:
            os.makedirs(debug_save_folder, exist_ok=True)
        except Exception:
            pass

    # Captura única y preprocesado
    full_img = pyautogui.screenshot(region=(min_x, min_y, total_w, total_h))
    if full_img.mode != "RGB":
        full_img = full_img.convert("RGB")

    processed_full = preprocess_full_image(full_img, upscale=1.05)

    try:
        scale_x = processed_full.width / full_img.width
        scale_y = processed_full.height / full_img.height
    except Exception:
        scale_x = scale_y = 1.0

    rel_boxes = list(enumerate([(x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y) for (x1, y1, x2, y2) in coords], start=1))
    rel_boxes_scaled = []
    for idx, (lx, ly, rx, ry) in rel_boxes:
        sx = int(max(0, round(lx * scale_x)))
        sy = int(max(0, round(ly * scale_y)))
        ex = int(max(0, round(rx * scale_x)))
        ey = int(max(0, round(ry * scale_y)))
        ex = min(ex, processed_full.width)
        ey = min(ey, processed_full.height)
        rel_boxes_scaled.append((idx, (sx, sy, ex, ey)))

    def _process_crop(item):
        idx, rel_box = item
        scaled_box = next(((i, b) for (i, b) in rel_boxes_scaled if i == idx), None)
        if scaled_box:
            _, box_scaled = scaled_box
            try:
                crop_proc = processed_full.crop(box_scaled)
            except Exception:
                orig_box = rel_box
                crop_proc = full_img.crop((orig_box[0] + min_x, orig_box[1] + min_y, orig_box[2] + min_x, orig_box[3] + min_y))
                try:
                    crop_proc = crop_proc.convert("L")
                except Exception:
                    pass
        else:
            orig_box = rel_box
            crop_proc = full_img.crop((orig_box[0] + min_x, orig_box[1] + min_y, orig_box[2] + min_x, orig_box[3] + min_y))
            try:
                crop_proc = crop_proc.convert("L")
            except Exception:
                pass

        if debug_save_folder:
            try:
                orig_box = (rel_box[0] + min_x, rel_box[1] + min_y, rel_box[2] + min_x, rel_box[3] + min_y)
                orig_crop = full_img.crop((rel_box[0], rel_box[1], rel_box[2], rel_box[3]))
                orig_path = os.path.join(debug_save_folder, f"stat_{idx:02d}_orig.png")
                proc_path = os.path.join(debug_save_folder, f"stat_{idx:02d}_proc.png")
                try:
                    orig_crop.save(orig_path)
                except Exception:
                    pass
                try:
                    if hasattr(crop_proc, "mode") and crop_proc.mode != "RGB":
                        crop_proc.convert("RGB").save(proc_path)
                    else:
                        crop_proc.save(proc_path)
                except Exception:
                    pass
            except Exception:
                pass

        # OCR por niveles
        conf_cfg = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        num, chosen_text, conf = _best_numeric_token_from_image(crop_proc, conf_cfg)
        if num and conf > -90:
            return num, chosen_text

        conf_cfg2 = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        num2, chosen_text2, conf2 = _best_numeric_token_from_image(crop_proc, conf_cfg2)
        if num2 and conf2 > -90:
            return num2, chosen_text2

        text3 = ocr_stat_image_config(crop_proc, lang=lang, config='--oem 3 --psm 6')
        num3 = extract_number_from_text(text3)
        return num3, text3

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_process_crop, rel_boxes))

    for num, text in results:
        txt_raw = "" if text is None else str(text)
        raw_texts_crudos.append(txt_raw)

        txt_clean = txt_raw.replace('\r', '').replace('\n', '').replace('\\n', '').strip()

        final_num = normalize_number(txt_clean)
        if final_num is None:
            final_num = num

        numbers.append(final_num)
        raw_texts.append(txt_clean)

    # Ajuste por 2*min o max+20
    if min_list or max_list:
        for i in range(min(len(numbers), len(coords))):
            try:
                minv = None
                maxv = None
                if min_list and i < len(min_list):
                    try:
                        minv = int(min_list[i])
                    except Exception:
                        minv = None
                if max_list and i < len(max_list):
                    try:
                        maxv = int(max_list[i])
                    except Exception:
                        maxv = None

                if (not minv or minv <= 0) and (maxv is None):
                    continue

                num = numbers[i] or 0
                txt = (raw_texts[i] or str(num))
                digits = "".join(re.findall(r'\d', txt)) or str(num)
                original_digits = digits

                triggered = False
                reason = None
                if minv and num > 2 * minv:
                    if (maxv is not None) and num > (maxv + 20):
                        triggered = True
                        reason = f"2*min={2*minv}"

                if triggered and len(digits) > 1:
                    new_digits = digits[:-1]
                    try:
                        new_val = int(new_digits)
                        numbers[i] = new_val
                        raw_texts[i] = new_digits
                        print(f"[ADJUST] fila {i+1}: OCR='{original_digits}' ajustado a '{raw_texts[i]}' por {reason}")
                    except Exception:
                        print(f"[ADJUST] fila {i+1}: OCR='{original_digits}' activó {reason} pero recorte no convertible")
            except Exception:
                continue

    elapsed = time.time() - start_time
    print(f"Tiempo captura+OCR: {elapsed:.2f}s - nonzeros: {sum(1 for v in numbers if v!=0)}")
    print("Valores extraídos:", numbers)

    print("Textos OCR CRUDOS por fila (repr):")
    for idx, txt in enumerate(raw_texts_crudos, start=1):
        print(f"  Stat {idx}: {repr(txt)}")

    print("Textos OCR brutos por fila:")
    for idx, txt in enumerate(raw_texts, start=1):
        print(f"  Stat {idx}: {repr(txt)}")

    if debug_save_folder:
        print(f"[DEBUG] Crops guardados en: {os.path.abspath(debug_save_folder)}")

    return numbers, raw_texts

if __name__ == "__main__":
    print("Preparando captura de stats individuales (debug mode: guarda crops)...")

    test_item_stats = {
        "min": [86, 55, 55, 21, 6, 1, 1, 6, 6, 8, 3, 3, 11],
        "max": [100, 60, 60, 30, 6, 1, 1, 6, 6, 8, 10, 10, 11],
        "obj": ["vi", "inte", "agi", "sa", "cri", "al", "inv", "da_fuego", "da_aire", "re_agua_por", "re_tierra",
                "re_aire", "da_cri"]
    }

    try:
        nums, raws = capture_and_read_stats(
            save_folder=None,
            lang='spa',
            num_stats=None,
            workers=8,
            debug_save_folder="debug_crops",
            item_stats=test_item_stats
        )
        print("\n=== RESULTADO FINAL ===")
        print("Números extraídos:", nums)
        print("\nComparación con stats esperadas:")
        print(f"  Min esperado: {test_item_stats['min']}")
        print(f"  Max esperado: {test_item_stats['max']}")
        print(f"  Atributos:    {test_item_stats['obj']}")
    except KeyboardInterrupt:
        print("\nInterrupción por usuario.")
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback
        traceback.print_exc()
