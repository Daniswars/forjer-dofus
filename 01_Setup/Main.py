import time
import sys
from pathlib import Path

# Asegurar imports locales
root = Path(__file__).parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
# permitir buscar un nivel arriba también
parent = str(root.parent)
if parent not in sys.path:
    sys.path.insert(0, parent)

import pyautogui
from Mage_Data_Extractor import capture_and_read_stats
from Mage_Introduce_Runes import mage_introduce_runes
from Mage_Introduce_Exo import introducir_exo
from Mage_Exo_Verify import verify_success
import Extra_Correo as Correo
from Extra_get_kamas import get_kamas
from Extra_Database import agregar_datos
import Setup_Item_Stats_Database

# acelerar interacción
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.03

def ensure_ui_active():
    try:
        pyautogui.press('alt')
        time.sleep(0.06)
    except Exception:
        pass

def stats_within_limits(stats_actuales, stats_min, stats_max):
    n = len(stats_min)
    for i in range(n):
        actual = stats_actuales[i] if i < len(stats_actuales) else 0
        if actual < stats_min[i]:
            return False
    return True

def capture_with_retries(attempts=3, wait_between=0.4):
    last_vals, last_text = [], ""
    for attempt in range(1, attempts + 1):
        start = time.time()
        valores, texto = capture_and_read_stats()
        elapsed = time.time() - start
        suma = sum(valores) if valores else 0
        nonzeros = sum(1 for v in (valores or []) if v != 0)
        print(f"Tiempo transcurrido en captura y OCR: {elapsed:.2f}s (intento {attempt}) - suma={suma} nonzeros={nonzeros}")
        if suma > 0 and nonzeros > 0:
            return valores, texto
        last_vals, last_text = valores, texto
        if attempt < attempts:
            print("Lectura dudosa (ceros/ruido). Reintentando captura OCR...")
            time.sleep(wait_between)
            ensure_ui_active()
    return last_vals, last_text

def sanitize_and_align(valores_actuales, target_len):
    if not valores_actuales:
        valores_actuales = []
    if len(valores_actuales) >= 2 and valores_actuales[0] == 0 and valores_actuales[1] > 0:
        print("Saneando lectura inicial: descartando primera fila (0) ya que la segunda tiene valor.")
        valores_actuales = valores_actuales[1:]
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

def mage_main(item_name, item_stats, max_iterations=None, no_progress_limit=6):
    print(f"Starting mage loop for item: {item_name}")
    ensure_ui_active()

    try:
        Correo.send_mail(item_name, "inicio magueo")
    except Exception as e:
        print("Aviso: no se pudo enviar correo de inicio:", e)

    iterations = 0
    no_progress_count = 0
    prev_stats = None
    target_len = len(item_stats["min"])
    start_time = time.time()

    try:
        while True:
            stats_actuales, _ = capture_with_retries(attempts=3, wait_between=0.2)
            stats_actuales = sanitize_and_align(stats_actuales, target_len)

            if not stats_actuales or len(stats_actuales) == 0:
                print("No se han detectado stats (OCR vacío) incluso tras reintentos. Reintentando tras breve espera.")
                time.sleep(0.2)
                ensure_ui_active()
                continue

            print("Current stats:", stats_actuales)

            if stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                print("Stats within limits -> introducing exo.")
                introducir_exo()
                time.sleep(0.25)
                print("Verifying exo...")
                if verify_success():
                    elapsed = time.time() - start_time
                    time_per_attempt = elapsed / max(1, iterations)
                    print("Exo successful. Finished.")
                    try:
                        Correo.send_mail(item_name, "Exito PA")
                    except Exception as e:
                        print("Aviso: no se pudo enviar correo de éxito:", e)
                    return {
                        "success": True,
                        "attempts": iterations,
                        "elapsed": elapsed,
                        "time_per_attempt": time_per_attempt,
                        "error": None
                    }
                else:
                    print("Exo failed. Continuing loop.")
                    time.sleep(0.2)
                    ensure_ui_active()
                    iterations += 1
                    print(f"Iteration {iterations} -> stats: {stats_actuales}")
                    if iterations % 10 == 0:
                        try:
                            Correo.send_mail(item_name, "10 intentos exo PA")
                        except Exception as e:
                            print("Aviso: no se pudo enviar correo de 10 intentos exo PA:", e)
                    continue

            print("Applying runes until stats >= min...")
            prev_stats = normalize_prev(prev_stats, target_len)
            while not stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                if max_iterations is not None and iterations >= max_iterations:
                    elapsed = time.time() - start_time
                    try:
                        Correo.send_mail(item_name, "10 intentos")
                    except Exception:
                        pass
                    return {
                        "success": False,
                        "attempts": iterations,
                        "elapsed": elapsed,
                        "time_per_attempt": elapsed / max(1, iterations),
                        "error": "max_iterations_reached"
                    }

                ensure_ui_active()
                try:
                    mage_introduce_runes(
                        stats_actuales=stats_actuales,
                        stats_min=item_stats["min"],
                        stats_obj=item_stats["obj"],
                        stats_max=item_stats["max"]
                    )
                except Exception as e:
                    print("ERROR en mage_introduce_runes:", repr(e))
                    time.sleep(0.2)
                    ensure_ui_active()
                    continue

                time.sleep(0.12)
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
                    except Exception as e:
                        print("Aviso: no se pudo enviar correo de 10 intentos exo PA:", e)

                if prev_stats is not None and stats_actuales == prev_stats:
                    no_progress_count += 1
                    print(f"No progress ({no_progress_count}/{no_progress_limit})")
                    if no_progress_count >= no_progress_limit:
                        elapsed = time.time() - start_time
                        print("No progress after several iterations. Aborting to avoid infinite loop.")
                        try:
                            Correo.send_mail(item_name, "Sin runas")
                        except Exception as e:
                            print("Aviso: no se pudo enviar correo 'Sin runas':", e)
                        return {
                            "success": False,
                            "attempts": iterations,
                            "elapsed": elapsed,
                            "time_per_attempt": elapsed / max(1, iterations),
                            "error": "no_progress"
                        }
                else:
                    no_progress_count = 0

                prev_stats = list(stats_actuales)

            time.sleep(0.12)
            continue
    except Exception as e:
        elapsed = time.time() - start_time
        print("ERROR crítico en mage_main:", repr(e))
        try:
            Correo.send_mail(item_name, "Finalizar forzado")
        except Exception:
            pass
        return {
            "success": False,
            "attempts": iterations,
            "elapsed": elapsed,
            "time_per_attempt": elapsed / max(1, iterations),
            "error": repr(e)
        }

# ----------------- CAMBIO: nueva fase de SETUP y main reestructurado -----------------
def setup_phase():
    """
    Fase de setup: obtener el nombre del objeto automáticamente desde Setup_Item_Stats_Database
    y leer kamas iniciales. No pide input al usuario.
    Devuelve (item_name, item_stats, kamas_iniciales) o (None, None, None) si no se obtiene el nombre.
    """
    # Intentar varias funciones posibles que el módulo de setup podría exponer
    candidates = [
        "get_selected_item_name",
        "get_current_item_name",
        "detect_item_name",
        "get_item_from_ui",
        "auto_get_item_name",
        "get_item_name",
        "get_item",
        "get_item_stats_by_screen"
    ]
    item_name = None
    for fn_name in candidates:
        fn = getattr(Setup_Item_Stats_Database, fn_name, None)
        if callable(fn):
            try:
                item_name = fn()
                if item_name:
                    print(f"SETUP: nombre de objeto detectado por '{fn_name}': {item_name}")
                    break
            except Exception as e:
                print(f"SETUP: la función '{fn_name}' falló: {e}")

    if not item_name:
        print("ERROR_SETUP: No se pudo obtener el nombre del objeto automáticamente desde Setup_Item_Stats_Database. Abortando setup.")
        return None, None, None

    item_stats = Setup_Item_Stats_Database.get_item_stats(item_name)
    if not item_stats:
        print(f"Item '{item_name}' no encontrado en la base de datos. Abortando setup.")
        return None, None, None

    print("Leyendo kamas iniciales (setup)...")
    try:
        kamas_iniciales = get_kamas()
    except Exception as e:
        print("Error leyendo kamas iniciales en setup:", e)
        kamas_iniciales = 0

    return item_name, item_stats, kamas_iniciales

def main():
    # Primera: SETUP
    item_name, item_stats, kamas_iniciales = setup_phase()
    if not item_name or not item_stats:
        print("Setup no completado. Saliendo.")
        return

    # Segunda: MAGE (ejecutar el bucle principal con los datos del setup)
    start_time = time.time()
    result = mage_main(item_name, item_stats, max_iterations=None)
    elapsed_total = time.time() - start_time

    # Lectura kamas final y guardado en BD
    print("Leyendo kamas finales...")
    try:
        kamas_finales = get_kamas()
    except Exception as e:
        print("Error leyendo kamas finales:", e)
        kamas_finales = 0

    attempts = result.get("attempts", 0) if isinstance(result, dict) else 0
    time_per_attempt = result.get("time_per_attempt", 0) if isinstance(result, dict) else (elapsed_total / max(1, attempts))
    success_flag = result.get("success", False) if isinstance(result, dict) else False
    exito_str = "Success" if success_flag else "Fail"

    print(f"Resumen: item={item_name}, attempts={attempts}, exito={exito_str}, kamas_iniciales={kamas_iniciales}, kamas_finales={kamas_finales}")

    # Guardar en la base de datos Excel
    try:
        agregar_datos(
            objeto_seleccionado=item_name,
            intentos=attempts,
            kamas_iniciales=kamas_iniciales,
            kamas_finales=kamas_finales,
            exito=exito_str,
            tiempo_medio_intento=time_per_attempt,
            modo_encadenado_activo=False
        )
    except Exception as e:
        print("Error guardando datos en la base de datos:", e)

if __name__ == "__main__":
    main()
