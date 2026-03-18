import pyautogui
import time
import sys
from pathlib import Path
import inspect
from datetime import datetime
import random

# Coordenadas de columnas (X) y filas (Y) para las celdas de runas
COLUMNAS_X = [2054, 2117, 2189]  # X de los 3 huecos (pequeña, media, grande)
FILA_Y_INICIAL = 790
FILA_DESNIVEL = 70

def get_fila_y(idx):
    return FILA_Y_INICIAL + idx * FILA_DESNIVEL

# acelerar interacción: desactivar failsafe y reducir pausa global
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.03

def click(x, y, reason=None):
    """
    Realiza un único click fiable en (x, y) y hace print de depuración.
    - reason: cadena opcional indicando por qué se hace el click (ayuda al debug).
    """
    try:
        # información del llamador para trazas
        caller = inspect.stack()[1]
        caller_fn = caller.function
        caller_line = caller.lineno
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[CLICK] {ts} called_by={caller_fn}:{caller_line} coords=({x},{y}) reason={reason!r}")
        pyautogui.moveTo(x, y, duration=0.05)
        pyautogui.click()
    except Exception as e:
        print(f"[CLICK-ERROR] al intentar click en ({x},{y}) reason={reason!r} error={e}")
    time.sleep(random.uniform(0.06,0.08))

def ensure_ui_active():
    # presionar Alt brevemente para "desatascar" la UI después de interacciones
    try:
        pyautogui.press('alt')
        time.sleep(0.04)
    except Exception:
        pass

# --- NUEVO HELPER: estimar incremento real por runa según objeto y columna X ---
def estimate_increment_for(obj, x):
    """
    Devuelve el incremento esperado (entero) cuando se hace click en la columna X
    para la stat 'obj'. Mantiene la lógica existente sobre qué columna se elige,
    pero corrige la estimación (p. ej. 'vi' => +50 en columna grande, 'ini' => +100).
    """
    # default pequeño
    try:
        name = str(obj).lower()
    except Exception:
        name = ""
    if x == COLUMNAS_X[0]:
        # columna pequeña
        if "ini" in name:
            return 10
        return 1
    if x == COLUMNAS_X[1]:
        # columna media
        if "ini" in name:
            return 30
        # para resistencia/sustracciones suele ser +3
        if "re" in name or "res" in name or "resistencia" in name:
            return 3
        # vida en columna media no suele darse, devolvemos 3/10 safe
        return 3
    if x == COLUMNAS_X[2]:
        # columna grande: puede ser +10, +50 (vida) o +100 (ini)
        if "vi" in name or "vital" in name:
            return 50
        if "ini" in name:
            return 100
        # estadisticas grandes (fuerza/inte/agilidad) ~ +10
        return 10
    # fallback
    return 1

def todas_estadisticas_al_60(estadisticas_actuales, estadisticas_min):
    # Devuelve True si todas las stats alcanzan al menos el 60% del mínimo
    for i in range(len(estadisticas_min)):
        actual = estadisticas_actuales[i] if i < len(estadisticas_actuales) else 0
        if actual < estadisticas_min[i] * 0.6:
            return False
    return True

def select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats):
    """
    Función auxiliar que encapsula la lógica de selección de columna X para una stat.
    Evita duplicación masiva del mismo código en múltiples lugares.
    """
    if obj in runas_re_emp:
        return COLUMNAS_X[1]
    elif obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
        return COLUMNAS_X[0]
    elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
        return COLUMNAS_X[0]
    elif obj in runas_re or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
        return COLUMNAS_X[1] if actual + 3 <= maximo else COLUMNAS_X[0]
    elif obj in runas_da:
        if actual + 3 <= maximo and actual > 12:
            return COLUMNAS_X[1]
        else:
            return COLUMNAS_X[0]
    elif obj in runas_sa:
        if actual + 10 <= maximo:
            return COLUMNAS_X[2]
        elif actual + 3 <= maximo:
            return COLUMNAS_X[1]
        else:
            return COLUMNAS_X[0]
    elif obj in runas_vi or obj in runas_ini or obj in runas_basic_stats:
        if obj in runas_vi:
            return COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
        elif obj in runas_ini:
            if actual + 100 <= maximo:
                return COLUMNAS_X[2]
            elif actual + 30 <= maximo:
                return COLUMNAS_X[1]
            else:
                return COLUMNAS_X[0]
        else:
            return COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
    else:
        return COLUMNAS_X[0]

def mage_introduce_runes(stats_actuales, stats_min, stats_obj, stats_max, planned_clicks=None, max_clicks_per_stat=5):
    """
    Versión mejorada: aplicar múltiples clicks por stat en un ciclo si es necesario y beneficioso.
    - Primera pasada: crítica (<30% del mínimo) - 1 click por stat.
    - Segunda pasada: alcanzar mínimo (<min) - clicks repetidos en ciclos mientras sea útil.
    - Tercera pasada: aplicar planned_clicks si se pasó.
    - Cuarta pasada: doble ciclo para resistencias si siguen bajas.
    """
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

    n = len(stats_min)

    # Validación mínima de lectura
    suma = sum(stats_actuales) if stats_actuales else 0
    nonzeros = sum(1 for v in (stats_actuales or []) if v != 0)
    min_nonzeros = max(1, n // 6)
    if suma == 0 or nonzeros < min_nonzeros:
        print("mage_introduce_runes: lectura dudosa (suma={}, nonzeros={}). No se aplicarán runas.".format(suma, nonzeros))
        return False

    clicked_indices = set()
    did_click_any = False

    # --- FASE CRÍTICA: manejar <30% del mínimo ---
    print("\n=== FASE CRÍTICA: stats < 30% del mínimo ===")
    for i in range(n):
        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        minimo = stats_min[i]
        obj = stats_obj[i] if i < len(stats_obj) else ""
        maximo = stats_max[i] if i < len(stats_max) else 9999
        y = get_fila_y(i)

        if not obj or actual >= minimo * 0.3:
            continue

        x = select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats)

        print(f"[CRÍTICO] click en ({x},{y}) para stat {obj} (actual {actual} < 30% min {minimo}) idx {i}")
        try:
            click(x, y, reason=f"critical_stat_{i}")
            did_click_any = True
            inc = estimate_increment_for(obj, x)
            stats_actuales[i] = min(stats_actuales[i] + inc, maximo)
        except Exception as e:
            print("ERROR al clickar (crítico):", e)
        ensure_ui_active()
        clicked_indices.add(i)

    # --- PASADA INTERMEDIA MEJORADA: clickar múltiples veces por stat en ciclos ---
    print("\n=== PASADA INTERMEDIA: alcanzar mínimo (múltiples clicks por ciclo) ===")
    max_passes = 8  # máximo de pasadas para evitar loops infinitos
    pass_count = 0

    while pass_count < max_passes:
        pass_count += 1
        any_clicked_this_pass = False

        for i in range(n):
            actual = stats_actuales[i] if i < len(stats_actuales) else 0
            minimo = stats_min[i]
            obj = stats_obj[i] if i < len(stats_obj) else ""
            maximo = stats_max[i] if i < len(stats_max) else 9999

            if not obj or actual >= minimo:
                continue

            # NUEVA REGLA: vida solo 1 click máximo, no múltiples
            if obj in runas_vi and i in clicked_indices:
                print(f"[PASADA {pass_count}] saltando stat {obj} (vida): ya recibió 1 click en fase crítica")
                continue

            x = select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats)
            inc = estimate_increment_for(obj, x)

            # Comprobar si el click sería útil y no superaría máximo
            if inc <= 0 or (actual + inc) > maximo:
                continue

            y = get_fila_y(i)
            print(f"[PASADA {pass_count}] click en ({x},{y}) para stat {obj} (actual {actual} < min {minimo}) idx {i}")
            try:
                click(x, y, reason=f"intermediate_stat_{i}_pass{pass_count}")
                did_click_any = True
                any_clicked_this_pass = True
                stats_actuales[i] = min(stats_actuales[i] + inc, maximo)
                # Si es vida, pausa más larga
                if obj in runas_vi:
                    time.sleep(0.08)
            except Exception as e:
                print("ERROR al clickar en pasada intermedia:", e)
            ensure_ui_active()
            clicked_indices.add(i)

        # Si no se hizo ningún click en esta pasada, salir del bucle
        if not any_clicked_this_pass:
            print(f"Fin de pasada intermedia en pass {pass_count}: sin clicks en esta ronda.")
            break

    # --- NUEVA FASE: ejecutar planned_clicks como rondas arriba->abajo ---
    if planned_clicks:
        print("\n=== FASE PLANIFICADA: ejecutar planned_clicks ===")
        plan = list(planned_clicks)[:n] + [0] * max(0, n - len(planned_clicks))

        # restar 1 del plan si ya se hizo 1 click en clicked_indices
        for i in range(n):
            if i in clicked_indices and plan[i] > 0:
                plan[i] = max(0, plan[i] - 1)

        max_extra = 3
        if max_clicks_per_stat is None:
            try:
                import RUN as MainModule
                max_extra = int(MainModule.shared_state.get("max_clicks_per_stat", max_extra))
            except Exception:
                pass

        # asegurar límites y no pasarse del stats_max
        for i in range(n):
            actual = stats_actuales[i] if i < len(stats_actuales) else 0
            maximo = stats_max[i] if i < len(stats_max) else 9999
            obj = stats_obj[i] if i < len(stats_obj) else ""

            col_x = select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats)
            inc = estimate_increment_for(obj, col_x)

            if inc > 0:
                allowed = max(0, (maximo - actual) // inc)
            else:
                allowed = 0

            plan[i] = min(plan[i], max_extra, allowed)

            # MODIFICADO: vida máximo 1 click TOTAL (si ya recibió en crítica, no más)
            if obj in runas_vi:
                if i in clicked_indices:
                    plan[i] = 0  # Ya recibió 1 click, no más
                else:
                    plan[i] = min(plan[i], 1)

        if any(p > 0 for p in plan):
            print("Ejecutando plan adicional de clicks por stat (rondas)...")
            while any(p > 0 for p in plan):
                for i in range(n):
                    if plan[i] <= 0:
                        continue

                    actual = stats_actuales[i] if i < len(stats_actuales) else 0
                    maximo = stats_max[i] if i < len(stats_max) else 9999
                    obj = stats_obj[i] if i < len(stats_obj) else ""
                    minimo = stats_min[i]

                    x = select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats)
                    inc = estimate_increment_for(obj, x)

                    # Recomprobar justo antes
                    if actual >= minimo or inc <= 0 or (actual + inc) > maximo:
                        plan[i] = 0
                        continue

                    y = get_fila_y(i)
                    try:
                        click(x, y, reason=f"planned_stat_{i}")
                        did_click_any = True
                        stats_actuales[i] = min(stats_actuales[i] + inc, maximo)
                        try:
                            import RUN as MainModule
                            MainModule.shared_state["rune_clicks"] = MainModule.shared_state.get("rune_clicks", 0) + 1
                        except Exception:
                            pass
                    except Exception as e:
                        print("ERROR al ejecutar click planificado:", e)
                    plan[i] -= 1
                    if obj in runas_vi:
                        time.sleep(0.08)
                    else:
                        time.sleep(0.045)

                ensure_ui_active()
                time.sleep(0.07)

            # --- DOBLE CICLO ESPECÍFICO PARA RESISTENCIAS ---
            print("\n=== DOBLE CICLO: resistencias ===")
            resist_indices = []
            for i in range(n):
                obj = stats_obj[i] if i < len(stats_obj) else ""
                if not obj or obj in runas_vi:
                    continue
                if obj in runas_re or obj in runas_re_por:
                    actual = stats_actuales[i]
                    minimo = stats_min[i]
                    maximo = stats_max[i] if i < len(stats_max) else 9999
                    inc = 3
                    if actual < minimo and (actual + inc) <= maximo:
                        resist_indices.append(i)

            if resist_indices:
                print(f"Doble ciclo resistencias: aplicando click extra en índices: {resist_indices}")
                for i in resist_indices:
                    obj = stats_obj[i] if i < len(stats_obj) else ""

                    # NUEVA REGLA: vida no entra en doble ciclo
                    if obj in runas_vi:
                        print(f"[RESIST-DOUBLE] saltando {obj} (vida): solo 1 click máximo")
                        continue

                    actual = stats_actuales[i]
                    maximo = stats_max[i] if i < len(stats_max) else 9999

                    x = select_column_for_stat(obj, actual, maximo, runas_tochas, runas_re_por, runas_da_20, runas_cu, runas_esquivas_retiras, runas_pla_hui, runas_re, runas_potencia, runa_prospe, runas_re_emp, runas_da, runas_sa, runas_vi, runas_ini, runas_basic_stats)
                    y = get_fila_y(i)
                    inc = estimate_increment_for(obj, x)

                    if actual >= stats_min[i] or inc <= 0 or (actual + inc) > maximo:
                        continue

                    try:
                        click(x, y, reason=f"resist_double_cycle_{i}")
                        did_click_any = True
                        stats_actuales[i] = min(stats_actuales[i] + inc, maximo)
                        try:
                            import RUN as MainModule
                            MainModule.shared_state["rune_clicks"] = MainModule.shared_state.get("rune_clicks", 0) + 1
                        except Exception:
                            pass
                    except Exception as e:
                        print("ERROR en doble ciclo resistencia click:", e)
                    time.sleep(0.05)
                ensure_ui_active()
                time.sleep(0.08)

    # --- CLICK FINAL SEGURO ---
    try:
        if did_click_any:
            SAFE_CLICK_X, SAFE_CLICK_Y = 2679, 1151
            try:
                click(SAFE_CLICK_X, SAFE_CLICK_Y, reason="safe_final")
                time.sleep(0.06)
                NEUTRAL_X, NEUTRAL_Y = 100, 100
                try:
                    pyautogui.moveTo(NEUTRAL_X, NEUTRAL_Y, duration=0.04)
                    print(f"[MOVE] movido a zona neutra ({NEUTRAL_X},{NEUTRAL_Y})")
                except Exception:
                    pass
                ensure_ui_active()
                time.sleep(0.06)
            except Exception:
                pass
    except Exception:
        pass

    return bool(did_click_any)

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
    # MODIFICADO: pasar stats_db al extractor usando lambda para capture_with_retries
    def capture_func():
        return Mage_Data_Extractor.capture_and_read_stats(item_stats=stats_db)

    valores_actuales, texto_ocr = capture_with_retries(capture_func, attempts=3, wait_between=0.5)
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
