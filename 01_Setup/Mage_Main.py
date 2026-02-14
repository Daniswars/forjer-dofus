import time
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
pyautogui.PAUSE = 0.03

def ensure_ui_active():
    # presionar Alt brevemente para "desatascar" la UI
    try:
        pyautogui.press('alt')
        time.sleep(0.06)
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
def capture_with_retries(attempts=3, wait_between=0.4):
    """
    Usa capture_and_read_stats() y reintenta si la lectura parece vacía o inestable.
    Devuelve (valores, texto).
    """
    last_vals, last_text = [], ""
    for attempt in range(1, attempts + 1):
        start = time.time()
        valores, texto = capture_and_read_stats()
        elapsed = time.time() - start
        suma = sum(valores) if valores else 0
        nonzeros = sum(1 for v in (valores or []) if v != 0)
        print(f"Tiempo transcurrido en captura y OCR: {elapsed:.2f}s (intento {attempt}) - suma={suma} nonzeros={nonzeros}")
        # si hay al menos un número y no es todo cero, aceptamos
        if suma > 0 and nonzeros > 0:
            return valores, texto
        # guardamos última lectura por si no hay mejoría
        last_vals, last_text = valores, texto
        if attempt < attempts:
            print("Lectura dudosa (ceros/ruido). Reintentando captura OCR...")
            time.sleep(wait_between)
            ensure_ui_active()
    # devolver la última lectura aunque sea cero
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

def mage_main(item_name, item_stats, control_events=None, max_iterations=None, no_progress_limit=6):
    """
    Bucle principal del magueo. Ya no guarda datos: devuelve un dict resumen.
    control_events: dict con 'pause_event' y 'stop_event' (ambos threading.Event).
    """
    print(f"Starting mage loop for item: {item_name}")
    ensure_ui_active()

    # Notificar inicio (si hay correo configurado)
    try:
        Correo.send_mail(item_name, "inicio magueo")
    except Exception:
        pass

    iterations = 0
    no_progress_count = 0
    prev_stats = None
    target_len = len(item_stats["min"])
    start_time = time.time()

    try:
        while True:
            # control check (pause/stop)
            if not _wait_handle_control(control_events):
                return {"success": False, "attempts": iterations, "elapsed": time.time() - start_time, "time_per_attempt": (time.time() - start_time) / max(1, iterations), "error": "stopped_by_user"}

            # extraer stats actuales con reintentos y normalizar a la longitud de stats_min
            stats_actuales, _ = capture_with_retries(attempts=3, wait_between=0.2)
            stats_actuales = sanitize_and_align(stats_actuales, target_len)

            if not stats_actuales or len(stats_actuales) == 0:
                print("No se han detectado stats (OCR vacío) incluso tras reintentos. Reintentando tras breve espera.")
                time.sleep(0.2)
                ensure_ui_active()
                continue

            print("Current stats:", stats_actuales)

            # si ya están dentro -> exo
            if stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                print("Stats within limits -> introducing exo.")
                # control check antes de acciones de UI
                if not _wait_handle_control(control_events):
                    return {"success": False, "attempts": iterations, "elapsed": time.time() - start_time, "time_per_attempt": (time.time() - start_time) / max(1, iterations), "error": "stopped_by_user"}
                introducir_exo()
                time.sleep(0.25)  # pequeño tiempo para que la UI procese
                print("Verifying exo...")
                if verify_success():
                    elapsed = time.time() - start_time
                    time_per_attempt = elapsed / max(1, iterations)
                    try:
                        Correo.send_mail(item_name, "Exito PA")
                    except Exception:
                        pass
                    return {"success": True, "attempts": iterations, "elapsed": elapsed, "time_per_attempt": time_per_attempt, "error": None}
                else:
                    print("Exo failed. Continuing loop.")
                    time.sleep(0.2)
                    ensure_ui_active()
                    iterations += 1
                    print(f"Iteration {iterations} -> stats: {stats_actuales}")
                    if iterations % 10 == 0:
                        try:
                            Correo.send_mail(item_name, "10 intentos exo PA")
                        except Exception:
                            pass
                    continue

            # aplicar runas hasta dentro de min
            print("Applying runes until stats >= min...")
            prev_stats = normalize_prev(prev_stats, target_len)
            while not stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                if not _wait_handle_control(control_events):
                    return {"success": False, "attempts": iterations, "elapsed": time.time() - start_time, "time_per_attempt": (time.time() - start_time) / max(1, iterations), "error": "stopped_by_user"}

                if max_iterations is not None and iterations >= max_iterations:
                    elapsed = time.time() - start_time
                    try:
                        Correo.send_mail(item_name, "10 intentos")
                    except Exception:
                        pass
                    return {"success": False, "attempts": iterations, "elapsed": elapsed, "time_per_attempt": elapsed / max(1, iterations), "error": "max_iterations_reached"}

                ensure_ui_active()
                try:
                    mage_introduce_runes(
                        stats_actuales=stats_actuales,
                        stats_min=item_stats["min"],
                        stats_obj=item_stats.get("obj", []),
                        stats_max=item_stats.get("max", [])
                    )
                except Exception as e:
                    print("ERROR en mage_introduce_runes:", repr(e))
                    time.sleep(0.2)
                    ensure_ui_active()
                    continue

                time.sleep(0.12)
                # control check antes de nueva lectura
                if not _wait_handle_control(control_events):
                    return {"success": False, "attempts": iterations, "elapsed": time.time() - start_time, "time_per_attempt": (time.time() - start_time) / max(1, iterations), "error": "stopped_by_user"}

                stats_actuales, _ = capture_with_retries(attempts=2, wait_between=0.18)
                stats_actuales = sanitize_and_align(stats_actuales, target_len)

                if not stats_actuales:
                    print("OCR returned vacío tras introducir runas, reintentando lectura...")
                    time.sleep(0.2)
                    ensure_ui_active()
                    stats_actuales, _ = capture_with_retries(attempts=2, wait_between=0.18)
                    stats_actuales = sanitize_and_align(stats_actuales, target_len)

                iterations += 1
                print(f"Iteration {iterations} -> stats: {stats_actuales}")
                if iterations % 10 == 0:
                    try:
                        Correo.send_mail(item_name, "10 intentos exo PA")
                    except Exception:
                        pass

                if prev_stats is not None and stats_actuales == prev_stats:
                    no_progress_count += 1
                    print(f"No progress ({no_progress_count}/{no_progress_limit})")
                    if no_progress_count >= no_progress_limit:
                        elapsed = time.time() - start_time
                        try:
                            Correo.send_mail(item_name, "Sin runas")
                        except Exception:
                            pass
                        return {"success": False, "attempts": iterations, "elapsed": elapsed, "time_per_attempt": elapsed / max(1, iterations), "error": "no_progress"}
                else:
                    no_progress_count = 0

                prev_stats = list(stats_actuales)

            time.sleep(0.12)
            continue
    except Exception as e:
        elapsed = time.time() - start_time
        try:
            Correo.send_mail(item_name, "Finalizar forzado")
        except Exception:
            pass
        return {"success": False, "attempts": iterations, "elapsed": elapsed, "time_per_attempt": elapsed / max(1, iterations), "error": repr(e)}

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
