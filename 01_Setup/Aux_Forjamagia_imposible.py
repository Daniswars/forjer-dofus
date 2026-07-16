import pyautogui
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import pytesseract
import unicodedata
import os
import time

# Configura aquí la ruta a tesseract si la necesitas (coincidir con la que uses en el proyecto)
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

def _preprocess_for_ocr(img, upscale=1.15):
    try:
        im = img.convert("L")
        im = ImageOps.autocontrast(im, cutoff=1)
        im = ImageEnhance.Contrast(im).enhance(1.3)
        im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=1))
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

def _normalize_text(s):
    if not s:
        return ""
    # minúsculas
    s = s.lower()
    # eliminar diacríticos
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # normalizar espacios y saltos
    s = s.replace("\r", " ").replace("\n", " ").strip()
    s = " ".join(s.split())
    return s

def _strip_spaces(s):
    return "".join(s.split())

def forjamagia_impossible_at_points(points=None, region_size=(600, 120), lang='spa', debug_save_folder=None, save_prefix=None):
    """
    Captura las regiones centradas en 'points' (lista de (x,y)) con tamaño region_size (w,h).
    Devuelve True si en alguna captura aparece 'Forjamagia imposible' (insensible a acentos/espacios).
    Opcional: debug_save_folder para guardar crops y poder inspeccionar OCR.
    """
    if points is None:
        points = [(1788, 1050), (2048, 1087)]
    found = False
    texts = []

    if debug_save_folder:
        try:
            os.makedirs(debug_save_folder, exist_ok=True)
        except Exception:
            pass

    for idx, (cx, cy) in enumerate(points, start=1):
        w, h = region_size
        left = max(0, int(cx - w // 2))
        top = max(0, int(cy - h // 2))
        try:
            crop = pyautogui.screenshot(region=(left, top, w, h))
        except Exception as exc:
            # en caso de fallo, continuar con la siguiente
            texts.append("")
            continue

        proc = _preprocess_for_ocr(crop, upscale=1.15)

        if debug_save_folder:
            try:
                fname = f"{save_prefix or 'forja'}_crop_{idx}.png"
                proc.convert("RGB").save(os.path.join(debug_save_folder, fname))
            except Exception:
                pass

        # usar psm 6 para bloque de texto
        try:
            config = '--oem 3 --psm 6'
            raw = pytesseract.image_to_string(proc, lang=lang, config=config)
        except Exception:
            raw = pytesseract.image_to_string(proc, lang='eng', config='--oem 3 --psm 6')

        norm = _normalize_text(raw)
        texts.append(norm)
        # comprobar sin espacios para evitar discrepancias por separación
        norm_nospace = _strip_spaces(norm)
        if (
            "forjamagiaimposible" in norm_nospace or 
            "dnoesta" in norm_nospace or 
            "disponible" in norm_nospace or 
            "cantidad" in norm_nospace
        ):
            found = True
            # podemos devolver pronto, pero seguimos capturando si queremos debug de todas
            # break

    return found, texts

if __name__ == "__main__":
    time.sleep(2)
    print("Comprobando 'Forjamagia imposible' en puntos configurados...")
    start = time.time()
    ok, debug_texts = forjamagia_impossible_at_points(
        points=[(1788, 1050), (2048, 1087)],
        region_size=(600, 120),
        lang='spa',
        debug_save_folder="debug_forja",
        save_prefix="test"
    )
    elapsed = time.time() - start
    print(f"Resultado: {ok} (tiempo {elapsed:.2f}s)")
    for i, t in enumerate(debug_texts, start=1):
        print(f"  Punto {i}: {repr(t)}")
