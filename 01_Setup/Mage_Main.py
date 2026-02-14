import time
import math
import pyautogui

from Mage_Data_Extractor import capture_and_read_stats
from Mage_Introduce_Runes import mage_introduce_runes
from Mage_Introduce_Exo import introducir_exo
from Mage_Exo_Verify import verify_success
import Extra_Correo as Correo

# Coordenadas del área de lectura: (x1,y1) -> (x2,y2)
X1, Y1 = 1512, 761
X2, Y2 = 1863, 1634
REGION = (X1, Y1, X2 - X1, Y2 - Y1)  # (x, y, width, height)

# acelerar interacción
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.02  # acelerado ligeramente

def ensure_ui_active():
    # presionar Alt brevemente para "desatascar" la UI
    try:
        pyautogui.press('alt')
        time.sleep(0.04)
    except Exception:
        pass

# --- Cambiado: comprobar según stats_min (toma missing como 0) ---
def stats_within_limits(stats_actuales, stats_min, stats_max):
    """
    Returns True if all stats are >= min (ignora stats_max aquí porque se usa en otras comprobaciones).
    Se itera sobre stats_min: si falta un valor en stats_actuales se considera 0 (no cumple).
    """
    n = len(stats_min)
    for i in range(n):
        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        if actual < stats_min[i]:
            return False
    return True

# --- Nuevas helpers: reintentos y normalización de lecturas ---
def capture_with_retries(attempts=3, wait_between=0.25):
    """
    Reintentos rápidos de OCR. Acepta la primera lectura con contenido razonable.
    Devuelve (valores, texto).
    """
    last_vals, last_text = [], ""
    for attempt in range(1, attempts + 1):
        start = time.time()
        valores, texto = capture_and_read_stats()
        elapsed = time.time() - start
        suma = sum(valores) if valores else 0
        nonzeros = sum(1 for v in (valores or []) if v != 0)
        print(f"Tiempo captura OCR: {elapsed:.2f}s (intento {attempt}) - suma={suma} nonzeros={nonzeros}")
        # Si hay al menos un valor no cero lo aceptamos inmediatamente
        if suma > 0 and nonzeros > 0:
            return valores, texto
        last_vals, last_text = valores, texto
        if attempt < attempts:
            # reintento rápido, intentando "desatascar" UI
            ensure_ui_active()
            time.sleep(wait_between)
    # devolver la última lectura incluso si es 0 (fallback)
    return last_vals, last_text

def sanitize_and_align(valores_actuales, target_len):
    """
    - Si la primera fila siempre sale 0 y la segunda tiene valor, desplazar (descartar la primera).
    - Recortar o rellenar con ceros para que la lista tenga exactamente target_len.
    """
    if not valores_actuales:
        valores_actuales = []
    # posible bug: primera fila 0 y segunda con valor -> desplazar
    if len(valores_actuales) >= 2 and valores_actuales[0] == 0 and valores_actuales[1] > 0:
        print("Saneando lectura inicial: descartando primera fila (0) ya que la segunda tiene valor.")
        valores_actuales = valores_actuales[1:]
    # ajustar longitud
    if len(valores_actuales) < target_len:
        valores_actuales = valores_actuales + [0] * (target_len - len(valores_actuales))
    elif len(valores_actuales) > target_len:
        valores_actuales = valores_actuales[:target_len]
    return valores_actuales

def normalize_prev(prev, target_len):
    if prev is None:
        return None
    p = list(prev)
    if len(p) < target_len:
        p = p + [0] * (target_len - len(p))
    elif len(p) > target_len:
        p = p[:target_len]
    return p

# Nuevo: control_events es dict opcional con 'pause_event' (Event) y 'stop_event' (Event)
def _wait_handle_control(control_events):
    """
    Si se pasa control_events, espera mientras pause_event está clear (pausado).
    Devuelve False si stop_event se encontró durante la espera -> indicar que se debe abortar.
    """
    if not control_events:
        return True
    pause_ev = control_events.get('pause_event')
    stop_ev = control_events.get('stop_event')
    # Si stop already set -> abort
    if stop_ev and getattr(stop_ev, "is_set", lambda: False)():
        return False
    # Si pause_event existe y no está set -> esperar
    if pause_ev:
        while not pause_ev.is_set():
            # comprobamos stop durante la pausa
            if stop_ev and stop_ev.is_set():
                return False
            time.sleep(0.15)
    return True

# ----------------------------------------------------------------------
# Optimización: aplicar runas priorizando stats muy bajas (<30% del min)
# ----------------------------------------------------------------------
def apply_runes_optimized(stats_actuales, stats_min, stats_obj=None, stats_max=None,
                          control_events=None, pre_clicks=3):
    """
    Construye un plan único de clicks por stat y llama a mage_introduce_runes UNA vez
    para ejecutar todas las rondas. Esto evita aplicar runas repetidamente y sobrepasar.
    """
    n = len(stats_min)
    # seguridad: normalizar listas
    stats_obj = stats_obj or []
    stats_max = stats_max or [99999] * n
    if len(stats_actuales) < n:
        stats_actuales = stats_actuales + [0] * (n - len(stats_actuales))
    else:
        stats_actuales = stats_actuales[:n]

    # parámetros
    incr_by_col = {0: 1, 1: 3, 2: 10}
    # obtener max clicks por stat desde Main.shared_state si existe
    default_max = pre_clicks
    try:
        import Main as MainModule
        default_max = int(MainModule.shared_state.get("max_clicks_per_stat", default_max))
    except Exception:
        pass

    planned_clicks = [0] * n
    preferred_col = [1] * n

    # heurística simple para elegir columna preferida (no cambia durante la iteración)
    for i in range(n):
        actual = stats_actuales[i]
        minimo = stats_min[i]
        maximo = stats_max[i] if i < len(stats_max) else 99999
        obj = stats_obj[i] if i < len(stats_obj) else ""
        name = str(obj).lower() if obj else ""
        if "vi" in name or "vital" in name:
            preferred_col[i] = 2 if actual + 30 <= maximo else 1
        elif "ini" in name:
            preferred_col[i] = 2 if actual + 100 <= maximo else 1
        elif "crit" in name or "da" in name:
            preferred_col[i] = 1
        elif "sue" in name or "suerte" in name:
            preferred_col[i] = 0
        else:
            preferred_col[i] = 1

    # construir plan: clicks necesarios intentando no sobrepasar en exceso
    for i in range(n):
        actual = stats_actuales[i]
        minimo = stats_min[i]
        if minimo <= 0 or actual >= minimo:
            planned_clicks[i] = 0
            continue
        col = preferred_col[i]
        inc = incr_by_col.get(col, 1)
        deficit = minimo - actual
        # aproximación inicial (ceil)
        need = (deficit + inc - 1) // inc
        # evitar overshoot grande: si ceil produce mucha sobre elevación, reducir si posible
        overshoot = actual + need * inc - minimo
        # si overshoot > inc/2 y need>1 reducimos uno (intenta menor overshoot)
        if need > 1 and overshoot > (inc // 2):
            need -= 1
        if need < 1:
            need = 1  # al menos 1 si hay déficit pequeño
        # limitar por max
        planned_clicks[i] = min(need, default_max)

    # si no hay clicks planificados, dejar que la función original haga una pasada mínima
    if not any(planned_clicks):
        # marcar una pasada mínima para stats por debajo de min
        for i in range(n):
            if stats_actuales[i] < stats_min[i]:
                planned_clicks[i] = 1

    # Validación: si lectura es dudosa, no aplicar
    suma = sum(stats_actuales)
    nonzeros = sum(1 for v in stats_actuales if v != 0)
    min_nonzeros = max(1, n // 6)
    if suma == 0 or nonzeros < min_nonzeros:
        print("Lectura dudosa antes de aplicar runas (apply_runes_optimized). Reintentando OCR...")
        nuevos, _ = capture_with_retries(attempts=2, wait_between=0.16)
        nuevos = sanitize_and_align(nuevos, n)
        suma2 = sum(nuevos) if nuevos else 0
        nonzeros2 = sum(1 for v in (nuevos or []) if v != 0)
        if suma2 == 0 or nonzeros2 < min_nonzeros:
            print("Persisten lecturas dudosas: no se aplicarán runas ahora.")
            return False
        stats_actuales = nuevos

    # Llamar a mage_introduce_runes UNA vez con el plan
    try:
        applied = mage_introduce_runes(stats_actuales, stats_min, stats_obj or [], stats_max or [], planned_clicks=planned_clicks)
        return bool(applied)
    except Exception as e:
        print("ERROR al ejecutar mage_introduce_runes con plan:", e)
        return False

# ----------------------------------------------------------------------
# mage_main principal (modificado): intentos y tiempo por intento desde EXO only
# ----------------------------------------------------------------------
def mage_main(item_name, item_stats, control_events=None, max_iterations=None, no_progress_limit=6):
    """
    Bucle principal del magueo. RESPONSABILIDAD:
      - No contar 'intentos' por runas; contar intentos únicamente cuando se introduce EXO (Mage_Introduce_Exo).
      - Calcular tiempo medio por intento usando el contador de EXO expuesto en Main.shared_state (si disponible).
    """
    print(f"Starting mage loop for item: {item_name}")
    ensure_ui_active()

    # Notificar inicio (si hay correo configurado)
    try:
        Correo.send_mail(item_name, "inicio magueo")
    except Exception:
        pass

    no_progress_count = 0
    prev_stats = None
    target_len = len(item_stats["min"])
    start_time = time.time()

    try:
        while True:
            # control (pausa/stop)
            if not _wait_handle_control(control_events):
                # calcular elapsed y attempts desde shared_state si es posible
                elapsed = time.time() - start_time
                attempts_exo = 0
                try:
                    import Main as MainModule
                    attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
                except Exception:
                    attempts_exo = 0
                time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
                return {"success": False, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": "stopped_by_user"}

            # captura de stats
            stats_actuales, _ = capture_with_retries(attempts=3, wait_between=0.25)
            stats_actuales = sanitize_and_align(stats_actuales, target_len)

            if not stats_actuales:
                print("OCR vacío tras reintentos. Reintentando...")
                time.sleep(0.12)
                ensure_ui_active()
                continue

            print("Current stats:", stats_actuales)

            # Si ya cumplen mínimos -> intentar exo
            if stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                print("Stats dentro de mínimos -> introducir exo.")
                if not _wait_handle_control(control_events):
                    elapsed = time.time() - start_time
                    attempts_exo = 0
                    try:
                        import Main as MainModule
                        attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
                    except Exception:
                        attempts_exo = 0
                    time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
                    return {"success": False, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": "stopped_by_user"}

                # introducir EXO (la función introducir_exo debe incrementar el contador global en Main.shared_state)
                introducir_exo()
                time.sleep(0.18)  # dar tiempo al juego
                print("Verificando exo...")
                if verify_success():
                    elapsed = time.time() - start_time
                    # obtener intentos a partir del contador global
                    attempts_exo = 0
                    try:
                        import Main as MainModule
                        attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
                    except Exception:
                        attempts_exo = 0
                    time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
                    try:
                        Correo.send_mail(item_name, "Exito PA")
                    except Exception:
                        pass
                    return {"success": True, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": None}
                else:
                    print("EXO falló. Continuando con runas si procede.")
                    # NO incrementar contador aquí; se incrementa solo en introducir_exo
                    # Esperar y continuar (no forzar incremento)
                    time.sleep(0.18)
                    ensure_ui_active()
                    # continuar bucle sin modificar counters
                    continue

            # aplicar runas optimizadas (priorizar <30% min y reducir lecturas)
            print("Aplicando runas (optimizadas)...")
            prev_stats = normalize_prev(prev_stats, target_len)

            # Validar lectura antes de aplicar runas: si dudosa reintentar rápido
            suma = sum(stats_actuales) if stats_actuales else 0
            nonzeros = sum(1 for v in (stats_actuales or []) if v != 0)
            min_nonzeros = max(1, target_len // 6)
            if suma == 0 or nonzeros < min_nonzeros:
                print("Lectura dudosa antes de aplicar runas. Reintentando OCR rápido...")
                stats_actuales_retry, _ = capture_with_retries(attempts=2, wait_between=0.16)
                stats_actuales_retry = sanitize_and_align(stats_actuales_retry, target_len)
                suma2 = sum(stats_actuales_retry) if stats_actuales_retry else 0
                nonzeros2 = sum(1 for v in (stats_actuales_retry or []) if v != 0)
                print(f"Re-captura: suma={suma2} nonzeros={nonzeros2}")
                if suma2 == 0 or nonzeros2 < min_nonzeros:
                    print("Persisten lecturas dudosas: se omiten runas en esta iteración.")
                    # forzamos siguiente iteración sin aplicar runas
                    time.sleep(0.08)
                    ensure_ui_active()
                    continue
                else:
                    stats_actuales = stats_actuales_retry

            applied = apply_runes_optimized(stats_actuales, item_stats["min"], item_stats.get("obj", []), item_stats.get("max", []), control_events=control_events, pre_clicks=3)
            # apply_runes_optimized delega y devuelve None/False si no aplicó; en nuestra implementación la aplicación ocurre dentro
            # Tras aplicar runas, hacer UNA recaptura
            if applied is False:
                # No se aplicaron runas (lectura dudosa o fallo), ya pasamos a iterar
                print("No se aplicaron runas en esta iteración.")
                time.sleep(0.08)
                ensure_ui_active()
                continue

            # tras aplicar runas, hacemos UNA lectura para comprobar progreso
            if not _wait_handle_control(control_events):
                elapsed = time.time() - start_time
                attempts_exo = 0
                try:
                    import Main as MainModule
                    attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
                except Exception:
                    attempts_exo = 0
                time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
                return {"success": False, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": "stopped_by_user"}

            time.sleep(0.12)
            stats_nuevos, _ = capture_with_retries(attempts=2, wait_between=0.18)
            stats_nuevos = sanitize_and_align(stats_nuevos, target_len)

            print(f"Post-runas stats: {stats_nuevos}")

            # detección de no progreso
            if prev_stats is not None and stats_nuevos == prev_stats:
                no_progress_count += 1
                print(f"No progress ({no_progress_count}/{no_progress_limit})")
                if no_progress_count >= no_progress_limit:
                    elapsed = time.time() - start_time
                    attempts_exo = 0
                    try:
                        import Main as MainModule
                        attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
                    except Exception:
                        attempts_exo = 0
                    time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
                    try:
                        Correo.send_mail(item_name, "Sin runas")
                    except Exception:
                        pass
                    return {"success": False, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": "no_progress"}
            else:
                no_progress_count = 0

            prev_stats = list(stats_nuevos)
            # breve espera antes de la siguiente iteración
            time.sleep(0.08)
            continue

    except Exception as e:
        elapsed = time.time() - start_time
        attempts_exo = 0
        try:
            import Main as MainModule
            attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
        except Exception:
            attempts_exo = 0
        try:
            Correo.send_mail(item_name, "Finalizar forzado")
        except Exception:
            pass
        return {"success": False, "attempts": attempts_exo, "elapsed": elapsed, "time_per_attempt": (elapsed / attempts_exo) if attempts_exo > 0 else None, "error": repr(e)}

if __name__ == "__main__":
    # Example usage: ask for item name and load stats from Setup_Item_Stats_Database
    time.sleep(0.6)  # menos espera antes de iniciar
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import Setup_Item_Stats_Database

    item_name = "Anillo del Conde Kontatras"
    item_stats = Setup_Item_Stats_Database.get_item_stats(item_name)
    if not item_stats:
        print("Item not found in database.")
        sys.exit(1)

    # por defecto sin límite: funcionará hasta que stats >= min o hasta que no-progreso cause abort
    result = mage_main(item_name, item_stats, max_iterations=None)
    print("Result summary:", result)
