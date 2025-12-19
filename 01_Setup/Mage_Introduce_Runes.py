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

def click(x, y):
    pyautogui.click(x=x, y=y)
    time.sleep(0.25)

def todas_estadisticas_al_60(estadisticas_actuales, estadisticas_min):
    # Devuelve True si todas las stats alcanzan al menos el 60% del mínimo
    for i in range(len(estadisticas_actuales)):
        if i >= len(estadisticas_min):
            return False
        if estadisticas_actuales[i] < estadisticas_min[i] * 0.6:
            return False
    return True

def mage_introduce_runes(stats_actuales, stats_min, stats_obj, stats_max):
    """
    stats_actuales: lista de valores actuales (Mage_Data_Extractor)
    stats_min, stats_obj, stats_max: listas de la base de datos del objeto (Setup_Item_Stats_Database)
    Lógica adaptada desde maguear.py: manejo de casos críticos (<30% min),
    fase "60%" y selección de columna según tipo de runa.
    """

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

    # Seguridad: asegurar consistencia de longitudes
    n = len(stats_actuales)
    for i in range(n):
        if i >= len(stats_min) or i >= len(stats_obj) or i >= len(stats_max):
            print(f"ERROR: listas de stats desalineadas en índice {i}.")
            return

    # Una pasada principal: primero manejar críticos (<30% del min)
    for i in range(n):
        actual = stats_actuales[i]
        minimo = stats_min[i]
        obj = stats_obj[i]
        maximo = stats_max[i]
        y = get_fila_y(i)

        # Caso crítico: muy por debajo del mínimo
        if actual < minimo * 0.3:
            # Re_emp prioritario: usar columna media/grande según criterio simple
            if obj in runas_re_emp:
                x = COLUMNAS_X[1]
                print(f"[CRITICO re_emp] click en ({x},{y}) para {obj} (actual {actual} <= min {minimo})")
                click(x, y)
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

            print(f"[CRITICO] click en ({x},{y}) para stat {obj} (actual {actual} < 30% min {minimo})")
            click(x, y)

    # Segunda fase: si todas las stats alcanzan al menos 60% del mínimo, aplicar segunda lógica
    if todas_estadisticas_al_60(stats_actuales, stats_min):
        for i in range(n):
            actual = stats_actuales[i]
            minimo = stats_min[i]
            obj = stats_obj[i]
            maximo = stats_max[i]
            y = get_fila_y(i)

            if actual < minimo:
                # Repetir selección con reglas de la fase 60% (más conservadora)
                if obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
                    x = COLUMNAS_X[0]
                elif obj in runas_sa:
                    x = COLUMNAS_X[2] if maximo >= 35 and actual + 10 <= maximo else COLUMNAS_X[1]
                elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
                    x = COLUMNAS_X[0]
                elif obj in runas_re or obj in runas_da or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
                    x = COLUMNAS_X[1]
                elif obj in runas_vi:
                    x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                elif obj in runas_ini:
                    x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                elif obj in runas_basic_stats:
                    x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
                else:
                    x = COLUMNAS_X[0]

                print(f"[60% FASE] click en ({x},{y}) para stat {obj} (actual {actual} < min {minimo})")
                click(x, y)

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
    time.sleep(1.5)
    valores_actuales, texto_ocr = Mage_Data_Extractor.capture_and_read_numbers()
    print("Valores actuales detectados:", valores_actuales)

    if len(valores_actuales) != len(stats_db["obj"]):
        print("ADVERTENCIA: número de stats detectadas distinto a la base de datos.")

    mage_introduce_runes(
        stats_actuales=valores_actuales,
        stats_min=stats_db["min"],
        stats_obj=stats_db["obj"],
        stats_max=stats_db["max"]
    )
