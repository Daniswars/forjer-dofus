import pyautogui
import pytesseract
from pytesseract import Output
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import re
import time
import os
import concurrent.futures
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# ──────────────────────────────────────────────
# Coordenadas de la FILA 1 (referencia)
# basica: (2021,760) -> (2079,796)
# bu    : (2087,760) -> (2150,794)
# su    : (2156,758) -> (2223,796)
# ────────────────────────────��─────────────────
FILA_1_Y_TOP = 760
DESNIVEL      = 70
NUM_FILAS     = 13

RECTS_FILA1 = {
    "basica": (2021, 760, 2079, 796),
    "bu"    : (2087, 760, 2150, 794),
    "su"    : (2156, 758, 2223, 796),
}

# Coordenadas base por tipo (X)
basic_y_1 = 2025
basic_y_2 = 2081
bu_y_1 = 2095
bu_y_2 = 2149
su_y_1 = 2159
su_y_2 = 2213

# Límites verticales por fila (Y) para las 6 primeras
fila_1_x_1 = 765
fila_1_x_2 = 788

fila_2_x_1 = 833
fila_2_x_2 = 854

fila_3_x_1 = 902
fila_3_x_2 = 926

fila_4_x_1 = 966
fila_4_x_2 = 996

fila_5_x_1 = 1034
fila_5_x_2 = 1064

fila_6_x_1 = 1106
fila_6_x_2 = 1133


def _build_first_6_rows():
    y_rows = [
        (fila_1_x_1, fila_1_x_2),
        (fila_2_x_1, fila_2_x_2),
        (fila_3_x_1, fila_3_x_2),
        (fila_4_x_1, fila_4_x_2),
        (fila_5_x_1, fila_5_x_2),
        (fila_6_x_1, fila_6_x_2),
    ]
    out = {}
    for i, (y1, y2) in enumerate(y_rows):
        out[i] = {
            "basica": (basic_y_1, y1, basic_y_2, y2),
            "bu":     (bu_y_1,    y1, bu_y_2,    y2),
            "su":     (su_y_1,    y1, su_y_2,    y2),
        }
    return out

def _add_rows_7_to_13(out: dict):
    """
    Añade filas 7..13 (índices 6..12) a la misma lista de rectángulos.
    """
    y_rows_7_13 = [
        (1171, 1201),  # fila 7
        (1237, 1268),  # fila 8
        (1306, 1334),  # fila 9
        (1381, 1408),  # fila 10
        (1444, 1468),  # fila 11
        (1510, 1543),  # fila 12
        (1582, 1613),  # fila 13
    ]
    start_idx = 6
    for k, (y1, y2) in enumerate(y_rows_7_13):
        i = start_idx + k
        out[i] = {
            "basica": (basic_y_1, y1, basic_y_2, y2),
            "bu":     (bu_y_1,    y1, bu_y_2,    y2),
            "su":     (su_y_1,    y1, su_y_2,    y2),
        }
    return out

ROW_RECTS_FIXED = _add_rows_7_to_13(_build_first_6_rows())

# Carpeta base de debug (subcarpeta con timestamp en cada ejecución)
DEBUG_BASE = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\pythonProject (1)\pythonProject\01_Setup\debug_runes"

def _debug_folder():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DEBUG_BASE, ts)
    os.makedirs(path, exist_ok=True)
    return path

def _rect_for_fila(tipo: str, fila: int):
    # Usa coordenadas exactas donde existen (ahora 1..13 en la misma lista)
    if fila in ROW_RECTS_FIXED and tipo in ROW_RECTS_FIXED[fila]:
        return ROW_RECTS_FIXED[fila][tipo]

    # Fallback final por si falta alguna fila
    x1, y1_ref, x2, y2_ref = RECTS_FILA1[tipo]
    dy = fila * DESNIVEL
    return (x1, y1_ref + dy, x2, y2_ref + dy)

# ──────────────────────────────────────────────
# Preprocesado
# ──────────────────────────────────────────────
def preprocess_crop(img: Image.Image) -> Image.Image:
    im = img.convert("L")
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.5)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=1))
    new_w = max(1, int(im.width * 2.5))
    new_h = max(1, int(im.height * 2.5))
    im = im.resize((new_w, new_h), Image.LANCZOS)
    return im

# ──────────────────────────────────────────────
# OCR numérico
# ──────────────────────────────────────────────
_CFG  = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
_CFG2 = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
_CFG3 = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'

def _ocr_img(img: Image.Image, cfg: str) -> str:
    for lang in ('spa', 'eng'):
        try:
            return pytesseract.image_to_string(img, lang=lang, config=cfg).strip()
        except pytesseract.pytesseract.TesseractError:
            continue
    return ""

def _best_token(img: Image.Image) -> int:
    for lang in ('spa', 'eng'):
        try:
            data = pytesseract.image_to_data(img, lang=lang, config=_CFG, output_type=Output.DICT)
            best_n, best_c = None, -999
            for tok, conf in zip(data['text'], data['conf']):
                tok = str(tok).strip()
                if not tok:
                    continue
                digits = re.sub(r'[^\d]', '', tok)
                if digits:
                    try:
                        c = int(float(conf))
                    except Exception:
                        c = -1
                    if c > best_c:
                        best_c = c
                        best_n = int(digits)
            if best_n is not None:
                return best_n
            break
        except pytesseract.pytesseract.TesseractError:
            continue
    for cfg in (_CFG, _CFG2, _CFG3):
        txt = _ocr_img(img, cfg)
        digits = re.sub(r'[^\d]', '', txt)
        if digits:
            return int(digits)
    return 0

# ──────────────────────────────────────────────
# Captura global única + OCR paralelo
# ──────────────────────────────────────────────
def read_runes(debug_folder: str = None):
    """
    1 screenshot global → crops paralelos → OCR.
    Guarda raw + processed en debug_folder si se pasa.
    """
    # Bounding box de todos los rectángulos
    all_rects = [(tipo, fila, _rect_for_fila(tipo, fila))
                 for fila in range(NUM_FILAS)
                 for tipo in ("basica", "bu", "su")]

    min_x = min(r[0] for _, _, r in all_rects)
    min_y = min(r[1] for _, _, r in all_rects)
    max_x = max(r[2] for _, _, r in all_rects)
    max_y = max(r[3] for _, _, r in all_rects)

    # Captura única
    full_raw = pyautogui.screenshot(region=(min_x, min_y, max_x - min_x, max_y - min_y))
    full_proc = preprocess_crop(full_raw)  # escala 2.5×

    sx = full_proc.width  / full_raw.width
    sy = full_proc.height / full_raw.height

    if debug_folder:
        full_raw.save(os.path.join(debug_folder, "00_full_raw.png"))
        full_proc.save(os.path.join(debug_folder, "00_full_proc.png"))

    def _process_one(args):
        tipo, fila, (x1, y1, x2, y2) = args
        # crop sobre imagen preprocesada
        lx = int((x1 - min_x) * sx);  ly = int((y1 - min_y) * sy)
        rx = int((x2 - min_x) * sx);  ry = int((y2 - min_y) * sy)
        rx = min(rx, full_proc.width);  ry = min(ry, full_proc.height)
        crop = full_proc.crop((lx, ly, rx, ry))

        if debug_folder:
            # raw (sin procesar) para referencia visual
            raw_crop = full_raw.crop((x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y))
            raw_crop.save(os.path.join(debug_folder, f"fila{fila+1:02d}_{tipo}_raw.png"))
            crop.save(os.path.join(debug_folder,     f"fila{fila+1:02d}_{tipo}_proc.png"))

        n = _best_token(crop)
        return (fila, tipo, n)

    # OCR paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        resultados = list(ex.map(_process_one, all_rects))

    # Ensamblar
    grid = {fila: {"fila": fila + 1, "basica": 0, "bu": 0, "su": 0}
            for fila in range(NUM_FILAS)}
    totales = {"basica": 0, "bu": 0, "su": 0}

    for fila, tipo, n in resultados:
        grid[fila][tipo] = n
        totales[tipo] += n

    detalle = []
    for fila in range(NUM_FILAS):
        d = grid[fila]
        detalle.append(d)
        print(f"  Fila {fila+1:2d}: basica={d['basica']:4d}  bu={d['bu']:4d}  su={d['su']:4d}")

    return totales, detalle

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
UMBRAL = 300

# Mapa de stat -> runas válidas REALES (solo las que existen en el juego)
# basica = sin prefijo, bu X = runa bu, su X = runa su
# Si una stat no tiene variante bu o su, NO se incluye
STAT_TO_RUNE = {
    "vi":           ("vi", "bu vi", "su vi"),
    "fo":           ("fo", "bu fo"),
    "inte":         ("inte", "bu inte"),
    "agi":          ("agi", "bu agi"),
    "sue":          ("sue", "bu sue"),
    "sa":           ("sa", "bu sa", "su sa"),
    "cri":          ("cri",),
    "al":           ("al",),
    "inv":          ("inv",),
    "pa":           ("pa",),
    "pm":           ("pm",),
    "pla":          ("pla", "bu pla"),
    "hui":          ("hui", "bu hui"),
    "prospe":       ("prospe", "bu prospe"),
    "da_tierra":    ("da_tierra", "bu da_tierra"),
    "da_aire":      ("da_aire", "bu da_aire"),
    "da_fuego":     ("da_fuego", "bu da_fuego"),
    "da_agua":      ("da_agua", "bu da_agua"),
    "da_neu":       ("da_neu", "bu da_neu"),
    "da_cri":       ("da_cri", "bu da_cri"),
    "re_neu_por":   ("re_neu_por",),
    "re_tierra_por":("re_tierra_por",),
    "re_aire_por":  ("re_aire_por",),
    "re_fuego_por": ("re_fuego_por",),
    "re_agua_por":  ("re_agua_por",),
    "re_neu":       ("re_neu", "bu re_neu"),
    "re_tierra":    ("re_tierra", "bu re_tierra"),
    "re_aire":      ("re_aire", "bu re_aire"),
    "re_fuego":     ("re_fuego", "bu re_fuego"),
    "re_agua":      ("re_agua", "bu re_agua"),
    "re_cri":       ("re_cri", "bu re_cri"),
    "ret_pa":       ("ret_pa", "bu ret_pa"),
    "ret_pm":       ("ret_pm", "bu ret_pm"),
    "re_pm":        ("re_pm", "bu re_pm"),
    "es_pa":        ("es_pa", "bu es_pa"),
    "es_pm":        ("es_pm", "bu es_pm"),
    "pot":          ("pot", "bu pot"),
    "ini":          ("ini", "bu ini"),
    "re_emp":       ("re_emp", "bu re_emp"),
}

def _parse_stats_input(s: str):
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]

def _rune_stock_from_totales(label: str, totales: dict) -> int:
    """
    Traduce etiqueta de runa al stock OCR leído.
    OCR actual solo distingue columnas: basica / bu / su.
    """
    l = (label or "").strip().lower()
    if l.startswith("su "):
        return int(totales.get("su", 0))
    if l.startswith("bu "):
        return int(totales.get("bu", 0))
    # etiquetas sin prefijo (fo, sa, da_aire, etc.) => básica
    # especiales (al, pa, pm, inv, cri) no tienen columna dedicada aquí
    if l in {"al", "pa", "pm", "inv", "cri"}:
        return 0
    return int(totales.get("basica", 0))

def _build_missing_string(selected_stats, totales, umbral=UMBRAL):
    """
    Para cada stat seleccionada:
      - mira sus runas candidatas
      - si TODAS están < umbral => se considera faltante
      - añade la runa "más alta" (última del tuple) al mensaje
    """
    faltan = []
    seen = set()

    for st in selected_stats:
        runes = STAT_TO_RUNE.get(st)
        if not runes:
            continue

        stocks = [_rune_stock_from_totales(r, totales) for r in runes]
        if all(v < umbral for v in stocks):
            chosen = runes[-1]  # preferir la más alta definida en el mapa
            if chosen not in seen:
                seen.add(chosen)
                faltan.append(f'"{chosen}"')

    return "Falta " + (", ".join(faltan) if faltan else '""')

def _rune_label_for_fila_tipo(stat: str, tipo: str) -> str:
    """
    Dado el nombre de stat y el tipo de columna (basica/bu/su),
    devuelve la etiqueta de runa correspondiente.
    Usa STAT_TO_RUNE para respetar el mapa definido.
    """
    runes = STAT_TO_RUNE.get(stat)
    if not runes:
        return None
    tipo_idx = {"basica": 0, "bu": 1, "su": 2}
    idx = tipo_idx.get(tipo, 0)
    if idx < len(runes):
        return runes[idx]
    return runes[-1]  # si hay menos variantes, la más alta disponible

def _build_missing_string_by_fila(selected_stats, detalle, umbral=UMBRAL):
    """
    Relaciona cada fila con la stat en esa posición (orden).
    Fila 1 -> stat[0], Fila 2 -> stat[1], ...
    Solo marca faltante si la runa EXISTE en STAT_TO_RUNE.
    """
    faltan = []
    seen = set()

    tipos = ["basica", "bu", "su"]

    for fila_idx, fila_data in enumerate(detalle):
        if fila_idx >= len(selected_stats):
            break

        stat = selected_stats[fila_idx]
        runes = STAT_TO_RUNE.get(stat)
        if not runes:
            # stat no mapeada: no inventar nombres
            print(f"[WARN] stat '{stat}' no está en STAT_TO_RUNE, se ignora.")
            continue

        for tipo_idx, tipo in enumerate(tipos):
            # Si no hay runa real para este tipo, no inventar
            if tipo_idx >= len(runes):
                break

            label = runes[tipo_idx]
            if label is None:
                continue

            stock = fila_data.get(tipo, 0)
            if stock < umbral and label not in seen:
                seen.add(label)
                faltan.append(f'"{label}"({stock})')

    return "Falta " + (", ".join(faltan) if faltan else '""')

def main(test_obj=None):
    dbg = _debug_folder()
    print(f"Debug folder: {dbg}")

    if test_obj is not None:
        selected_stats = [str(x).strip().lower() for x in test_obj if str(x).strip()]
        print(f"[TEST] Usando stats fijas: {selected_stats}")
    else:
        stats_in = input(
            "Stats item (coma): vi,fo,agi,sa,cri,da_tierra,da_aire,re_neu_por,pla,re_cri\n> "
        ).strip()
        selected_stats = _parse_stats_input(stats_in)

    t0 = time.monotonic()
    totales, detalle = read_runes(debug_folder=dbg)
    elapsed = time.monotonic() - t0
    print(f"\nTiempo total OCR: {elapsed:.2f}s")

    print("\n========== TOTALES ==========")
    for tipo in ("basica", "bu", "su"):
        estado = "✓" if totales[tipo] >= UMBRAL else "✗ FALTA"
        print(f"  {tipo:6s}: {totales[tipo]:6d}  {estado}")

    print("\n========== RELACIÓN FILA → STAT ==========")
    for fila_idx, fila_data in enumerate(detalle):
        if fila_idx >= len(selected_stats):
            break
        stat = selected_stats[fila_idx]
        runes = STAT_TO_RUNE.get(stat, ())
        r_basica = runes[0] if len(runes) > 0 else stat
        r_bu     = runes[1] if len(runes) > 1 else "---"
        r_su     = runes[2] if len(runes) > 2 else "---"
        b  = fila_data["basica"]
        bu = fila_data["bu"]
        su = fila_data["su"]
        flag_b  = "✗" if b  < UMBRAL else "✓"
        flag_bu = "✗" if bu < UMBRAL else "✓"
        flag_su = "✗" if su < UMBRAL else "✓"
        print(
            f"  Fila {fila_idx+1:2d} [{stat:14s}] "
            f"{r_basica:20s}={b:5d}{flag_b}  "
            f"{r_bu:20s}={bu:5d}{flag_bu}  "
            f"{r_su:20s}={su:5d}{flag_su}"
        )

    resultado = _build_missing_string_by_fila(selected_stats, detalle, UMBRAL)
    print(f"\n{resultado}")
    print(f"\nFotos guardadas en: {dbg}")

def build_missing_runes_for_item_stats(item_stats_obj, debug_folder=None, umbral=UMBRAL):
    """
    API para RUN.py:
    - item_stats_obj: lista de stats (orden del item)
    - devuelve: (mensaje_falta, totales, detalle)
    """
    selected_stats = [str(x).strip().lower() for x in (item_stats_obj or []) if str(x).strip()]
    if debug_folder is None:
        debug_folder = _debug_folder()

    totales, detalle = read_runes(debug_folder=debug_folder)
    mensaje = _build_missing_string_by_fila(selected_stats, detalle, umbral)
    return mensaje, totales, detalle

if __name__ == "__main__":
    test_item_stats = {
        "obj": [
            "vi",
            "inte",
            "sue",
            "sa",
            "al",
            "inv",
            "da_fuego",
            "da_agua",
            "prospe",
            "re_neu",
            "hui",
            "ret_pm"
        ]
    }
    main(test_obj=test_item_stats["obj"])
