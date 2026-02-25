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
general_x2 = 1600
STAT_COORDS = [
    (general_x1, 756, general_x2, 823),
    (general_x1, 823, 1610, 891),
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
    (general_x1, 1574, general_x2, 1644), #noai -15 x2
]

ONE_EQUIVALENTS = [
    "1", "l", "I", "L", "|", "!", "lalcance", "lalcanze", "lalcanse", "lal", r"lalcanc\n", "lin", "lin"
]

# --- Añadido: helper para comparar tokens con ONE_EQUIVALENTS manejando '\n' ---
def matches_one_equivalent(token):
    """
    Devuelve True si `token` coincide (tras normalizar) con alguno de los elementos
    de ONE_EQUIVALENTS. Normaliza salto de línea '\n' como literal '\\n' y elimina espacios.
    """
    if not token:
        return False
    # normalizar token: quitar zero-width, bajar a minúsculas y reemplazar salto real por la secuencia \n
    t = str(token).replace('\u200b', '').lower()
    t = t.replace('\r', '').replace('\n', r'\n')
    t = re.sub(r'\s+', '', t)
    for eq in ONE_EQUIVALENTS:
        eq_s = str(eq).lower()
        # asegurar que los patrones que contienen escape se traten de la misma forma
        eq_s = eq_s.replace('\r', '').replace('\n', r'\n')
        eq_s = re.sub(r'\s+', '', eq_s)
        if t == eq_s:
            return True
    return False

def normalize_number(text):
    t = (text or "")
    if not t:
        return None

    # Eliminar saltos de línea reales y la secuencia literal '\n' si aparecen
    try:
        t = t.replace('\r', '').replace('\n', '')
        t = t.replace('\\n', '')
    except Exception:
        pass

    # Si el token se parece a uno de los equivalentes a "1", devolver 1
    try:
        if matches_one_equivalent(t):
            return 1
    except Exception:
        pass

    t = t.strip()
    # Normalizaciones comunes de OCR
    t = t.replace('\u200b', '')  # zero-width
    t = t.replace('O', '0').replace('o', '0')
    t = t.replace('I', '1').replace('l', '1').replace('L', '1')
    t = t.replace(' ', '')
    # quitar símbolos comunes
    t = re.sub(r'[^\d+-]', '', t)
    if t in ['', '+', '-']:
        return None
    try:
        return int(t)
    except Exception:
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
    # Eliminar saltos de línea reales y la secuencia literal '\n' antes de procesar
    line = (text or "")
    try:
        line = line.replace('\r', '').replace('\n', '')
        line = line.replace('\\n', '')
    except Exception:
        pass
    line = line.replace('O', '0').replace('o', '0').strip()
    if is_noise_line(line):
        return 0
    # limpiar miles y espacios
    line_clean = re.sub(r'[^\d+-]', '', line)
    if not line_clean:
        return 0
    try:
        return int(line_clean)
    except Exception:
        # intentar buscar grupos de dígitos
        digit_groups = re.findall(r'\d+', line)
        if digit_groups:
            try:
                return int(digit_groups[-1])
            except Exception:
                pass
    return 0

def _best_numeric_token_from_image(img, config):
    """
    Usa image_to_data para seleccionar el token numérico con mayor confianza.
    Devuelve (number:int or 0, chosen_text:str, best_conf:int)
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
            # limpiar token y eliminar saltos de línea reales y literales
            tok_clean = tok.replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
            try:
                tok_clean = tok_clean.replace('\r', '').replace('\n', '')
                tok_clean = tok_clean.replace('\\n', '')
            except Exception:
                pass
            if re.search(r'\d', tok_clean):
                # convertir conf seguro
                try:
                    conf_v = int(float(conf))
                except Exception:
                    conf_v = -1
                n = normalize_number(tok_clean)
                if n is not None and conf_v > best_conf:
                    best_conf = conf_v
                    best_num = n
                    # guardar texto original saneado para debug (sin saltos)
                    try:
                        best_text = str(tok).replace('\r', '').replace('\n', '').replace('\\n', '')
                    except Exception:
                        best_text = str(tok)
        if best_num is not None:
            return best_num, best_text, best_conf
    except Exception:
        pass
    return 0, "", -100

def capture_and_read_stats(save_folder=None, lang='spa', num_stats=None, workers=6, debug_save_folder=None):
    """
    Captura única de pantalla + OCR por crop usando paralelismo.
    - Si num_stats se proporciona, solo procesa las primeras num_stats filas de STAT_COORDS.
    - workers: número de hilos para ThreadPoolExecutor.
    - debug_save_folder: si se proporciona, guardará cada crop original y procesado para depuración.
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

    # crear carpeta de debug si se pide
    if debug_save_folder:
        try:
            os.makedirs(debug_save_folder, exist_ok=True)
        except Exception:
            pass

    # UNA sola captura (rápida) y un único preprocesado
    full_img = pyautogui.screenshot(region=(min_x, min_y, total_w, total_h))
    if full_img.mode != "RGB":
        full_img = full_img.convert("RGB")

    processed_full = preprocess_full_image(full_img, upscale=1.05)

    # Calcular factores de escala entre la imagen procesada y la original (para mapear coordenadas)
    try:
        scale_x = processed_full.width / full_img.width
        scale_y = processed_full.height / full_img.height
    except Exception:
        scale_x = scale_y = 1.0

    # preparar cajas relativas con índice para poder guardar por index en paralelo
    rel_boxes = list(enumerate([(x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y) for (x1, y1, x2, y2) in coords], start=1))
    # también preparar cajas escaladas para recortar sobre processed_full (si hay upscale)
    rel_boxes_scaled = []
    for idx, (lx, ly, rx, ry) in rel_boxes:
        sx = int(max(0, round(lx * scale_x)))
        sy = int(max(0, round(ly * scale_y)))
        ex = int(max(0, round(rx * scale_x)))
        ey = int(max(0, round(ry * scale_y)))
        # clamp para evitar salirse de la imagen procesada
        ex = min(ex, processed_full.width)
        ey = min(ey, processed_full.height)
        rel_boxes_scaled.append((idx, (sx, sy, ex, ey)))

    def _process_crop(item):
        idx, rel_box = item
        # usar la caja escalada para recortar sobre la imagen procesada
        # buscamos la caja correspondiente en rel_boxes_scaled por idx
        scaled_box = next(((i, b) for (i, b) in rel_boxes_scaled if i == idx), None)
        if scaled_box:
            _, box_scaled = scaled_box
            try:
                crop_proc = processed_full.crop(box_scaled)
            except Exception:
                # fallback a recorte desde la imagen original si algo falla
                orig_box = rel_box
                crop_proc = full_img.crop((orig_box[0] + min_x, orig_box[1] + min_y, orig_box[2] + min_x, orig_box[3] + min_y))
                try:
                    crop_proc = crop_proc.convert("L")
                except Exception:
                    pass
        else:
            # si no encontramos caja escalada, recortar desde la original
            orig_box = rel_box
            crop_proc = full_img.crop((orig_box[0] + min_x, orig_box[1] + min_y, orig_box[2] + min_x, orig_box[3] + min_y))
            try:
                crop_proc = crop_proc.convert("L")
            except Exception:
                pass

        # guardar crops para debug si se solicita (original y procesado)
        if debug_save_folder:
            try:
                # orig_box en coordenadas de full_img (ya que full_img fue hecha con region=(min_x,min_y,...))
                orig_box = (rel_box[0] + min_x, rel_box[1] + min_y, rel_box[2] + min_x, rel_box[3] + min_y)
                # y el orig_crop relativo a la full_img (0..w,0..h) se obtiene sin offset
                orig_crop = full_img.crop((rel_box[0], rel_box[1], rel_box[2], rel_box[3]))
                # nombres claros por índice
                orig_path = os.path.join(debug_save_folder, f"stat_{idx:02d}_orig.png")
                proc_path = os.path.join(debug_save_folder, f"stat_{idx:02d}_proc.png")
                try:
                    orig_crop.save(orig_path)
                except Exception:
                    pass
                try:
                    # convertir a RGB para que se vea bien si es L
                    if hasattr(crop_proc, "mode") and crop_proc.mode != "RGB":
                        crop_proc.convert("RGB").save(proc_path)
                    else:
                        crop_proc.save(proc_path)
                except Exception:
                    pass
            except Exception:
                pass

        # intentar estrategia por niveles usando image_to_data para confiar en confs
        # 1) digits-only psm7 (mejor para un solo número)
        conf_cfg = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        num, chosen_text, conf = _best_numeric_token_from_image(crop_proc, conf_cfg)
        if num and conf > -90:
            return num, chosen_text

        # 2) digits-only psm6 (layout variable)
        conf_cfg2 = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        num2, chosen_text2, conf2 = _best_numeric_token_from_image(crop_proc, conf_cfg2)
        if num2 and conf2 > -90:
            return num2, chosen_text2

        # 3) fallback: imagen a string general (una sola vez por crop)
        text3 = ocr_stat_image_config(crop_proc, lang=lang, config='--oem 3 --psm 6')
        num3 = extract_number_from_text(text3)
        return num3, text3

    # ejecutar OCR en paralelo manteniendo orden con executor.map
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_process_crop, rel_boxes))

    for num, text in results:
        # limpiar textos brutos para que no contengan '\n' o '\\n'
        try:
            txt_clean = (text or "")
            txt_clean = txt_clean.replace('\r', '').replace('\n', '').replace('\\n', '')
        except Exception:
            txt_clean = text

        # Si el texto limpio corresponde a un equivalente de "1", forzar número y texto a '1'
        try:
            if matches_one_equivalent(txt_clean):
                num = 1
                txt_clean = '1'
        except Exception:
            pass

        numbers.append(num)
        raw_texts.append(txt_clean)

    elapsed = time.time() - start_time
    # prints de depuración: valores y textos leídos
    print(f"Tiempo captura+OCR: {elapsed:.2f}s - nonzeros: {sum(1 for v in numbers if v!=0)}")
    print("Valores extraídos:", numbers)
    print("Textos OCR brutos por fila:")
    for idx, txt in enumerate(raw_texts, start=1):
        print(f"  Stat {idx}: {repr(txt)}")
    if debug_save_folder:
        print(f"[DEBUG] Crops guardados en: {os.path.abspath(debug_save_folder)}")
    return numbers, raw_texts

if __name__ == "__main__":
    print("Preparando captura de stats individuales (debug mode: guarda crops)...")
    try:
        # sólo procesa las primeras N stats si quieres probar rápido; usa None para todas
        nums, raws = capture_and_read_stats(save_folder=None, lang='spa', num_stats=None, workers=8, debug_save_folder="debug_crops")
        print("Resultado final:", nums)
    except KeyboardInterrupt:
        print("Interrupción por usuario.")
    except Exception as exc:
        print("Error:", exc)