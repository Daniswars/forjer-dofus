import pyautogui
import time
import sys
from pathlib import Path

# Coordenadas de columnas (X) y filas (Y) para las celdas de runas
COLUMNAS_X = [2054, 2117, 2189]  # X de los 3 huecos (pequeña, media, grande)
FILA_Y_INICIAL = 790
FILA_DESNIVEL = 70

def get_fila_y(idx):
    return FILA_Y_INICIAL + idx * FILA_DESNIVEL

# acelerar interacción: desactivar failsafe y reducir pausa global
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.03

def click(x, y):
    """
    Realiza un único click fiable en (x, y).
    """
    try:
        pyautogui.moveTo(x, y, duration=0.05)
        pyautogui.click()
    except Exception:
        pass
    time.sleep(0.06)

def ensure_ui_active():
    # presionar Alt brevemente para "desatascar" la UI después de interacciones
    try:
        pyautogui.press('alt')
        time.sleep(0.04)
    except Exception:
        pass

def todas_estadisticas_al_60(estadisticas_actuales, estadisticas_min):
    # Devuelve True si todas las stats alcanzan al menos el 60% del mínimo
    for i in range(len(estadisticas_min)):
        actual = estadisticas_actuales[i] if i < len(estadisticas_actuales) else 0
        if actual < estadisticas_min[i] * 0.6:
            return False
    return True

def mage_introduce_runes(stats_actuales, stats_min, stats_obj, stats_max):
    """
    stats_actuales: lista de valores actuales (Mage_Data_Extractor)
    stats_min, stats_obj, stats_max: listas de la base de datos del objeto (Setup_Item_Stats_Database)
    Ahora sólo se procesan las filas que existen en stats_min (n = len(stats_min)).
    """
    # Asegurarnos de que la UI está activa al empezar
    ensure_ui_active()

    # Listas de tipos de runas (prioridades)
    runas_tochas = ["pa", "pm", "al", "inv", "da", "cri"]
    runas_re_por = ["re_agua_por", "re_aire_por", "re_tierra_por", "re_fuego_por", "re_neu_por"]
    runas_re = ["re_agua", "re_aire", "re_tierra", "re_fuego", "re_neu", "re_cri"]
    runas_vi = ["vi"]
    runas_da = ["da_agua", "da_aire", "da_tierra", "da_fuego", "da_neu", "da_cri", "da_tram", "da_emp"]
    runas_sa = ["sa"]
    runas_cu = ["cu"]
    runas_pla_hui = ["pla", "hui"]
    runas_esquivas_retiras = ["ret_pa", "ret_pm", "es_pa", "es_pm"]
    runas_basic_stats = ["fo", "inte", "agi", "sue"]
    runas_potencia = ["pot"]
    runas_ini = ["ini"]
    runas_da_20 = ["da"]
    runa_prospe = ["prospe"]
    runas_re_emp = ["re_emp"]

    # Usar la longitud de stats_min como fuente de verdad
    n = len(stats_min)

    # Aviso si hay desalineación, pero no abortar
    if len(stats_actuales) != n:
        print(f"AVISO: stats_actuales tiene {len(stats_actuales)} entradas pero stats_min tiene {n}. Se procesarán {n} filas (recortando o rellenando con 0).")

    # Registrar índices que ya han recibido click en la pasada crítica para evitar doble click
    clicked_indices = set()

    # Una pasada principal: primero manejar críticos (<30% del min)
    for i in range(n):
        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        minimo = stats_min[i]
        obj = stats_obj[i] if i < len(stats_obj) else ""
        maximo = stats_max[i] if i < len(stats_max) else 9999
        y = get_fila_y(i)

        # Si no hay nombre de stat en la DB, saltar (protección)
        if not obj:
            # debug opcional
            # print(f"SKIP idx {i}: sin nombre de stat en stats_obj")
            continue

        # Caso crítico: muy por debajo del mínimo
        if actual < minimo * 0.3:
            # Re_emp prioritario: usar columna media/grande según criterio simple
            if obj in runas_re_emp:
                x = COLUMNAS_X[1]
                print(f"[CRITICO] click en ({x},{y}) para stat {obj} (idx {i})")
                click(x, y)
                ensure_ui_active()
                clicked_indices.add(i)
                continue

            # Selección por tipo
            if obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
                x = COLUMNAS_X[0]

            elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
                x = COLUMNAS_X[0]

            elif obj in runas_re or obj in runas_da or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
                x = COLUMNAS_X[1] if actual + 3 <= maximo else COLUMNAS_X[0]

            elif obj in runas_potencia or obj in runas_sa:
                if actual + 10 <= maximo:
                    x = COLUMNAS_X[2]
                elif actual + 3 <= maximo:
                    x = COLUMNAS_X[1]
                else:
                    x = COLUMNAS_X[0]

            elif obj in runas_vi or obj in runas_ini or obj in runas_basic_stats:
                # vitalidad/iniciativa/stats básicos: preferir columna grande si cabe
                if obj in runas_vi:
                    x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                elif obj in runas_ini:
                    x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                else:  # basic_stats
                    x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
            else:
                x = COLUMNAS_X[0]

            print(f"[CRITICO] click en ({x},{y}) para stat {obj} (actual {actual} < 30% min {minimo}) idx {i}")
            try:
                click(x, y)
            except Exception as e:
                print("ERROR al clickar:", e)
            ensure_ui_active()
            clicked_indices.add(i)

    # --- CAMBIO: siempre intentar subir las stats por debajo del mínimo ---
    # Hacemos una pasada intermedia para cualquier stat actual < minimo (si no se clicó ya),
    # con reglas similares a la "fase 60%" pero aplicada siempre para no dejar stat sin tocar.
    for i in range(n):
        if i in clicked_indices:
            continue

        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        minimo = stats_min[i]
        obj = stats_obj[i] if i < len(stats_obj) else ""
        maximo = stats_max[i] if i < len(stats_max) else 9999
        y = get_fila_y(i)

        # Si no hay nombre de stat en la DB, saltar (protección)
        if not obj:
            continue

        # Si está por debajo del mínimo, intentar aplicar una runa
        if actual < minimo:
            # Reglas de selección (más conservadoras que la fase crítica)
            if obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
                x = COLUMNAS_X[0]
            elif obj in runas_sa:
                x = COLUMNAS_X[2] if maximo >= 35 and actual + 10 <= maximo else COLUMNAS_X[1]
            elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
                x = COLUMNAS_X[0]
            elif obj in runas_re or obj in runas_da or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
                # preferir columna media por defecto
                x = COLUMNAS_X[1] if actual + 3 <= maximo else COLUMNAS_X[0]
            elif obj in runas_vi:
                x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
            elif obj in runas_ini:
                x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
            elif obj in runas_basic_stats:
                x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
            else:
                x = COLUMNAS_X[0]

            print(f"[PASADA INTERMEDIA] click en ({x},{y}) para stat {obj} (actual {actual} < min {minimo}) idx {i}")
            try:
                click(x, y)
            except Exception as e:
                print("ERROR al clickar en pasada intermedia:", e)
            ensure_ui_active()
            clicked_indices.add(i)

# --- NUEVAS FUNCIONES: reintentos y saneamiento de primera fila ---
def capture_with_retries(capture_func, attempts=3, wait_between=0.4):
    """
    Llama a capture_func() que debe devolver (valores, texto).
    Reintenta hasta attempts si la suma de valores es 0 (posible mala lectura).
    """
    for attempt in range(1, attempts + 1):
        start = time.time()
        valores, texto = capture_func()
        elapsed = time.time() - start
        suma = sum(valores) if valores else 0
        print(f"Tiempo transcurrido en captura y OCR: {elapsed:.2f} segundos (intento {attempt}) - suma={suma}")
        if suma > 0:
            return valores, texto
        if attempt < attempts:
            print("Lectura vacía/dudosa: reintentando captura OCR...")
            time.sleep(wait_between)
    # devolver la última lectura aunque sea cero
    return valores, texto

def sanitize_initial_values(valores_actuales, stats_min_len):
    """
    Si la primera lectura tiene la primera fila en 0 y la segunda con valor,
    descartar la primera fila (desplazar).
    Solo se aplica si tiene al menos 2 entradas.
    """
    if not valores_actuales:
        return valores_actuales
    if len(valores_actuales) >= 2:
        if valores_actuales[0] == 0 and valores_actuales[1] > 0:
            print("Saneando primera lectura: descartando primera fila porque sale 0 y la segunda tiene valor.")
            return valores_actuales[1:]
    # si hay muchos elementos y stats_min es más corto, no tocar aquí (se recortará después)
    return valores_actuales

# --- NUEVO: asegurar que el root del proyecto esté en sys.path para imports locales ---
def ensure_project_in_path():
    # Este fichero está en ...\pythonProject\02_Mage\ ; queremos añadir ...\pythonProject\ y su padre por si acaso
    p = Path(__file__).resolve()
    candidates = [
        p.parent,              # ...\02_Mage
        p.parent.parent,       # ...\pythonProject
        p.parent.parent.parent # ...\pythonProject (1) si aplica
    ]
    for c in candidates:
        s = str(c)
        if s not in sys.path:
            sys.path.insert(0, s)

if __name__ == "__main__":
    # Intentar importar módulos locales; añadir ruta del proyecto si falla
    try:
        import Setup_Item_Stats_Database
        import Mage_Data_Extractor
    except ModuleNotFoundError:
        ensure_project_in_path()
        try:
            import Setup_Item_Stats_Database
            import Mage_Data_Extractor
        except Exception as e:
            print("ERROR: no se han podido importar los módulos locales necesarios.")
            print("Detalle:", repr(e))
            print("Rutas actuales de búsqueda (sys.path):")
            for p in sys.path[:6]:
                print(" -", p)
            print("Asegúrate de que Setup_Item_Stats_Database.py y Mage_Data_Extractor.py están en el árbol del proyecto.")
            sys.exit(1)

    nombre = input("Nombre exacto del objeto: ").strip()
    stats_db = Setup_Item_Stats_Database.get_item_stats(nombre)
    if not stats_db:
        print("Objeto no encontrado en la base de datos.")
        exit(1)

    print("Preparando OCR para extraer valores actuales...")
    time.sleep(0.3)

    # Primera captura: usar reintentos y saneamiento de la primera fila problemática
    valores_actuales, texto_ocr = capture_with_retries(Mage_Data_Extractor.capture_and_read_stats, attempts=3, wait_between=0.5)
    # si la primera lectura suele fallar en la primera fila, sanearla aquí
    valores_actuales = sanitize_initial_values(valores_actuales, len(stats_db["min"]))

    print("Números extraídos:", valores_actuales)
    print("Valores actuales detectados:", valores_actuales)

    # Ajustar valores_actuales para que tenga exactamente la longitud de stats_min (recortar o rellenar con 0)
    n = len(stats_db["min"])
    if len(valores_actuales) < n:
        valores_actuales = valores_actuales + [0] * (n - len(valores_actuales))
    elif len(valores_actuales) > n:
        valores_actuales = valores_actuales[:n]

    print(f"Valores ajustados a la longitud de stats_min ({n}):", valores_actuales)

    if len(valores_actuales) != len(stats_db["obj"]):
        print("ADVERTENCIA: número de stats detectadas distinto a la base de datos de objeto (se usará stats_min como referencia).")

    mage_introduce_runes(
        stats_actuales=valores_actuales,
        stats_min=stats_db["min"],
        stats_obj=stats_db["obj"],
        stats_max=stats_db["max"]
    )
