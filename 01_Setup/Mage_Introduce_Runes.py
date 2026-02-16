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
        return 1
    if x == COLUMNAS_X[1]:
        # columna media
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

def mage_introduce_runes(stats_actuales, stats_min, stats_obj, stats_max, planned_clicks=None, max_clicks_per_stat=None):
    """
    Versión extendida:
     - mantiene la lógica original de selección de columna/X para cada stat (NO la modifico).
     - si planned_clicks es una lista, ejecuta esas pulsaciones en rondas arriba->abajo
       (ajustando si ya se hizo un click en fases previas).
     - valida lectura antes de actuar (suma/nonzeros) y devuelve True si hizo clicks.
     - NO sobrepasa stats_max: cada plan se recorta para cumplir max permitido y se actualiza 'actual' local tras cada click.
    """
    ensure_ui_active()

    # Listas de tipos de runas (prioridades) - idénticas a la implementación previa
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

    # Validación mínima de lectura antes de tocar UI
    suma = sum(stats_actuales) if stats_actuales else 0
    nonzeros = sum(1 for v in (stats_actuales or []) if v != 0)
    min_nonzeros = max(1, n // 6)
    if suma == 0 or nonzeros < min_nonzeros:
        print("mage_introduce_runes: lectura dudosa (suma={}, nonzeros={}). No se aplicarán runas.".format(suma, nonzeros))
        return False

    # Registrar índices que ya han recibido click en la pasada crítica/intermedia para evitar doble click inmediato
    clicked_indices = set()
    did_click_any = False

    # --- FASE CRÍTICA (idéntica a la lógica previa): manejar <30% del mínimo ---
    for i in range(n):
        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        minimo = stats_min[i]
        obj = stats_obj[i] if i < len(stats_obj) else ""
        maximo = stats_max[i] if i < len(stats_max) else 9999
        y = get_fila_y(i)

        if not obj:
            continue

        if actual < minimo * 0.3:
            # Selección exacta de X mantenida (NO la modifico)
            if obj in runas_re_emp:
                x = COLUMNAS_X[1]
            elif obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
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
                if obj in runas_vi:
                    x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                elif obj in runas_ini:
                    x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                else:
                    x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
            else:
                x = COLUMNAS_X[0]

            print(f"[CRITICO] click en ({x},{y}) para stat {obj} (actual {actual} < 30% min {minimo}) idx {i}")
            try:
                click(x, y)
                did_click_any = True
                # actualizar valor local para evitar overclick en fases siguientes
                try:
                    inc = estimate_increment_for(obj, x)
                    stats_actuales[i] = stats_actuales[i] + inc
                except Exception:
                    pass
            except Exception as e:
                print("ERROR al clickar (crítico):", e)
            ensure_ui_active()
            clicked_indices.add(i)

    # --- PASADA INTERMEDIA (idéntica a la lógica previa): intentar stats < min si no fueron clicadas ---
    for i in range(n):
        if i in clicked_indices:
            continue

        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        minimo = stats_min[i]
        obj = stats_obj[i] if i < len(stats_obj) else ""
        maximo = stats_max[i] if i < len(stats_max) else 9999
        y = get_fila_y(i)

        if not obj:
            continue

        if actual < minimo:
            # Selección exacta de X mantenida (NO la modifico)
            if obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
                x = COLUMNAS_X[0]
            elif obj in runas_sa:
                x = COLUMNAS_X[2] if maximo >= 35 and actual + 10 <= maximo else COLUMNAS_X[1]
            elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
                x = COLUMNAS_X[0]
            elif obj in runas_re or obj in runas_da or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
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
                did_click_any = True
                # actualizar valor local para evitar overclick en fases siguientes
                try:
                    inc = estimate_increment_for(obj, x)
                    stats_actuales[i] = stats_actuales[i] + inc
                except Exception:
                    pass
            except Exception as e:
                print("ERROR al clickar en pasada intermedia:", e)
            ensure_ui_active()
            clicked_indices.add(i)

    # --- NUEVA FASE: ejecutar planned_clicks (si se pasó) como rondas arriba->abajo ---
    if planned_clicks:
        # normalizar plan a tamaño n y convertir a enteros
        plan = list(planned_clicks)[:n] + [0] * max(0, n - len(planned_clicks))
        # si ya se hizo 1 click en clicked_indices restamos 1 del plan para no duplicar
        for i in range(n):
            if i in clicked_indices and plan[i] > 0:
                plan[i] = max(0, plan[i] - 1)

        # obtener límite por stat desde parámetro o Main.shared_state
        max_extra = 3
        if max_clicks_per_stat is None:
            try:
                import Main as MainModule
                max_extra = int(MainModule.shared_state.get("max_clicks_per_stat", max_extra))
            except Exception:
                pass

        # asegurar límites y, CRUCIAL: no pasarse del stats_max calculando máximo permitido por stat
        for i in range(n):
            actual = stats_actuales[i] if i < len(stats_actuales) else 0
            maximo = stats_max[i] if i < len(stats_max) else 9999
            # estimar incremento por click según columna que usaríamos (reutilizamos lógica para calcular x)
            obj = stats_obj[i] if i < len(stats_obj) else ""
            # determinar columna prevista (misma lógica que arriba para coherencia)
            if obj in runas_re_emp:
                col_x = COLUMNAS_X[1]
            elif obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
                col_x = COLUMNAS_X[0]
            elif obj in runas_cu or obj in runas_esquivas_retiras or obj in runas_pla_hui:
                col_x = COLUMNAS_X[0]
            elif obj in runas_re or obj in runas_da or obj in runas_potencia or obj in runa_prospe or obj in runas_re_emp:
                col_x = COLUMNAS_X[1] if actual + 3 <= maximo else COLUMNAS_X[0]
            elif obj in runas_potencia or obj in runas_sa:
                if actual + 10 <= maximo:
                    col_x = COLUMNAS_X[2]
                elif actual + 3 <= maximo:
                    col_x = COLUMNAS_X[1]
                else:
                    col_x = COLUMNAS_X[0]
            elif obj in runas_vi or obj in runas_ini or obj in runas_basic_stats:
                if obj in runas_vi:
                    col_x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                elif obj in runas_ini:
                    col_x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                else:
                    col_x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
            else:
                col_x = COLUMNAS_X[0]

            # mapear col_x a incremento estimado
            # reemplazado por estimación robusta
            inc = estimate_increment_for(obj, col_x)

            # máximo clicks permitidos sin superar maximo
            if inc > 0:
                allowed = max(0, (maximo - actual) // inc)
            else:
                allowed = 0
            # no pasarse del límite por stat
            plan[i] = min(plan[i], max_extra, allowed)

        if any(p > 0 for p in plan):
            print("Ejecutando plan adicional de clicks por stat (rondas)...")
            # Ejecutar rondas: una pulsación por stat por ronda, de arriba->abajo
            while any(p > 0 for p in plan):
                for i in range(n):
                    if plan[i] <= 0:
                        continue
                    # recalcular columna X exactamente con la misma lógica de selección previa
                    actual = stats_actuales[i] if i < len(stats_actuales) else 0
                    maximo = stats_max[i] if i < len(stats_max) else 9999
                    obj = stats_obj[i] if i < len(stats_obj) else ""
                    # misma selección de X (idéntica a la usada arriba)
                    if obj in runas_re_emp:
                        x = COLUMNAS_X[1]
                    elif obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
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
                        if obj in runas_vi:
                            x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                        elif obj in runas_ini:
                            x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                        else:
                            x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
                    else:
                        x = COLUMNAS_X[0]

                    y = get_fila_y(i)
                    try:
                        click(x, y)
                        did_click_any = True
                        # intentar incrementar contador global de runa clicks si existe
                        try:
                            import Main as MainModule
                            MainModule.shared_state["rune_clicks"] = MainModule.shared_state.get("rune_clicks", 0) + 1
                        except Exception:
                            pass
                        # actualizar actual local para evitar sobrepasar el máximo en rondas siguientes
                        inc = estimate_increment_for(obj, x)
                        stats_actuales[i] = min(stats_actuales[i] + inc, stats_max[i] if i < len(stats_max) else stats_actuales[i] + inc)
                    except Exception as e:
                        print("ERROR al ejecutar click planificado:", e)
                    plan[i] -= 1
                    # pausa muy corta entre clicks para que el juego procese
                    time.sleep(0.045)
                # fin de ronda
                ensure_ui_active()
                time.sleep(0.07)

            # --- DOBLE CICLO ESPECÍFICO PARA RESISTENCIAS ---
            # Hacemos una pasada adicional SOLO para stats de resistencia (runas_re, runas_re_por)
            # Si tras las rondas siguen por debajo del mínimo y no se supera stats_max, se aplica 1 click extra.
            resist_indices = []
            for i in range(n):
                obj = stats_obj[i] if i < len(stats_obj) else ""
                if obj and (obj in runas_re or obj in runas_re_por):
                    # comprobar si sigue por debajo del mínimo y tiene margen para 1 click más
                    actual = stats_actuales[i]
                    minimo = stats_min[i]
                    maximo = stats_max[i] if i < len(stats_max) else 9999
                    # estimación del incremento por columna según la lógica usada: preferimos col1 (inc=3) para resistencias
                    inc = 3
                    # si aplicar inc no superará el máximo y sigue siendo útil (mejora hacia el mínimo) -> añadir
                    if actual < minimo and (actual + inc) <= maximo:
                        resist_indices.append(i)
            if resist_indices:
                print(f"Doble ciclo resistencias: aplicando click extra en índices: {resist_indices}")
                for i in resist_indices:
                    obj = stats_obj[i] if i < len(stats_obj) else ""
                    actual = stats_actuales[i]
                    maximo = stats_max[i] if i < len(stats_max) else 9999
                    # reutilizar la misma selección de columna/X para consistencia
                    if obj in runas_re_emp:
                        x = COLUMNAS_X[1]
                    elif obj in runas_tochas or obj in runas_re_por or obj in runas_da_20:
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
                        if obj in runas_vi:
                            x = COLUMNAS_X[2] if actual + 50 <= maximo else COLUMNAS_X[1]
                        elif obj in runas_ini:
                            x = COLUMNAS_X[2] if actual + 100 <= maximo else COLUMNAS_X[1]
                        else:
                            x = COLUMNAS_X[2] if actual + 10 <= maximo else COLUMNAS_X[1]
                    else:
                        x = COLUMNAS_X[0]
                    y = get_fila_y(i)
                    try:
                        click(x, y)
                        did_click_any = True
                        # actualizar valor local (inc = 3 por defecto para resistencias)
                        inc = estimate_increment_for(obj, x)
                        stats_actuales[i] = min(stats_actuales[i] + inc, stats_max[i] if i < len(stats_max) else stats_actuales[i] + inc)
                        try:
                            import Main as MainModule
                            MainModule.shared_state["rune_clicks"] = MainModule.shared_state.get("rune_clicks", 0) + 1
                        except Exception:
                            pass
                    except Exception as e:
                        print("ERROR en doble ciclo resistencia click:", e)
                    time.sleep(0.05)
                ensure_ui_active()
                time.sleep(0.08)

    # devolvemos True si se hicieron clicks en alguna fase
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
