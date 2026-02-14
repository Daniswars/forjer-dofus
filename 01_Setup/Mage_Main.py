import time
import pyautogui

from Mage_Data_Extractor import capture_and_read_stats
from Mage_Introduce_Runes import mage_introduce_runes
from Mage_Introduce_Exo import introducir_exo
from Mage_Exo_Verify import verify_success
# --- Nuevo: importar módulo de correo (alineado con main.py) ---
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

# --- Nuevo: importar Main_Save_Data de forma robusta ---
try:
    import Main_Save_Data as DataSaver
except Exception:
    # intentar añadir carpeta padre al path y reintentar
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        import Main_Save_Data as DataSaver
    except Exception as e:
        DataSaver = None
        print("WARNING: no se pudo importar Main_Save_Data, las funciones de guardado no estarán disponibles:", e)

def mage_main(item_name, item_stats, max_iterations=None, no_progress_limit=6):
    """
    Ahora itera hasta que todas las stats >= stats_min.
    Devuelve un dict resumen con llaves: success (bool), attempts (int), elapsed (float),
    time_per_attempt (float), error (str|None).
    """
    print(f"Starting mage loop for item: {item_name}")
    ensure_ui_active()

    # --- Enviar correo de inicio ---
    try:
        Correo.send_mail(item_name, "inicio magueo")
    except Exception as e:
        print("Aviso: no se pudo enviar correo de inicio:", e)

    # --- Nuevo: guardar kamas iniciales usando Main_Save_Data.save_initial_kamas ---
    initial_kamas_saved = None
    if DataSaver is not None:
        try:
            initial_kamas_saved = DataSaver.save_initial_kamas(item_name)
            print(f"DEBUG_SAVEFLOW: Kamas iniciales guardadas: {initial_kamas_saved}")
        except Exception as e:
            print("WARNING: fallo al guardar kamas iniciales con Main_Save_Data:", e)
    else:
        print("WARNING: DataSaver no disponible, no se guardarán kamas iniciales automáticamente.")

    iterations = 0
    no_progress_count = 0
    prev_stats = None
    target_len = len(item_stats["min"])
    start_time = time.time()
    try:
        while True:
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
                introducir_exo()
                time.sleep(0.25)  # pequeño tiempo para que la UI procese
                print("Verifying exo...")
                if verify_success():
                    elapsed = time.time() - start_time
                    time_per_attempt = elapsed / max(1, iterations)
                    print("Exo successful. Finished.")
                    # --- ENVIAR correo de éxito ---
                    try:
                        Correo.send_mail(item_name, "Exito PA")
                    except Exception as e:
                        print("Aviso: no se pudo enviar correo de éxito:", e)

                    # --- NUEVO: llamar a Main_Save_Data.finalize_session para guardar éxito ---
                    if DataSaver is not None:
                        try:
                            attempts_to_save = max(1, iterations)
                            tiempo_promedio_guardar = time_per_attempt
                            print("DEBUG_SAVEFLOW: Guardando resultado SUCCESS en Excel mediante Main_Save_Data.finalize_session...")
                            saved = DataSaver.finalize_session(
                                objeto=item_name,
                                intentos=attempts_to_save,
                                exito="PA",
                                tiempo_medio_intento=tiempo_promedio_guardar,
                                modo_encadenado_activo=True,
                                precio_objeto_base=None,
                                precio_venta_objeto_final=None,
                                tipo_exo="PA",
                                kamas_iniciales_arg=None
                            )
                            print(f"DEBUG_SAVEFLOW: finalize_session returned: {saved}")
                        except Exception as e:
                            print("ERROR: fallo al guardar éxito con Main_Save_Data:", e)
                    else:
                        print("WARNING: DataSaver no disponible, no se guardó el resultado en Excel.")

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

                    # --- NUEVO: enviar correo cada 10 intentos indicando que son de exo PA ---
                    if iterations % 10 == 0:
                        try:
                            Correo.send_mail(item_name, "10 intentos exo PA")
                        except Exception as e:
                            print("Aviso: no se pudo enviar correo de 10 intentos exo PA:", e)
                    continue

            # si no están dentro, aplicar runas hasta que lo estén (o se alcance seguridad)
            print("Applying runes until stats >= min...")
            prev_stats = normalize_prev(prev_stats, target_len)
            while not stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                if max_iterations is not None and iterations >= max_iterations:
                    elapsed = time.time() - start_time
                    print(f"Reached max_iterations ({max_iterations}). Aborting rune loop.")
                    try:
                        Correo.send_mail(item_name, "10 intentos")
                    except Exception as e:
                        print("Aviso: no se pudo enviar correo de max_iterations:", e)
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
                    # continuar el bucle tras error puntual
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

                # detectar no progreso (comparando listas normalizadas)
                if prev_stats is not None and stats_actuales == prev_stats:
                    no_progress_count += 1
                    print(f"No progress ({no_progress_count}/{no_progress_limit})")
                    if no_progress_count >= no_progress_limit:
                        elapsed = time.time() - start_time
                        print("No progress after several iterations. Aborting to avoid infinite loop.")
                        # --- ENVIAR correo "Sin runas" antes de abortar ---
                        try:
                            Correo.send_mail(item_name, "Sin runas")
                        except Exception as e:
                            print("Aviso: no se pudo enviar correo 'Sin runas':", e)

                        # --- NUEVO: guardar como fallo usando Main_Save_Data.finalize_session ---
                        if DataSaver is not None:
                            try:
                                attempts_to_save = max(1, iterations)
                                tiempo_promedio_guardar = (elapsed / attempts_to_save) if attempts_to_save > 0 else 0.0
                                print("DEBUG_SAVEFLOW: Guardando resultado FAIL en Excel mediante Main_Save_Data.finalize_session...")
                                saved = DataSaver.finalize_session(
                                    objeto=item_name,
                                    intentos=attempts_to_save,
                                    exito=0,
                                    tiempo_medio_intento=tiempo_promedio_guardar,
                                    modo_encadenado_activo=True,
                                    precio_objeto_base=None,
                                    precio_venta_objeto_final=None,
                                    tipo_exo=None,
                                    kamas_iniciales_arg=None
                                )
                                print(f"DEBUG_SAVEFLOW: finalize_session returned: {saved}")
                            except Exception as e:
                                print("ERROR: fallo al guardar fallo con Main_Save_Data:", e)
                        else:
                            print("WARNING: DataSaver no disponible, no se guardó el fallo en Excel.")

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
        except Exception as ee:
            print("Aviso: no se pudo enviar correo tras error crítico:", ee)

        # Intentar guardar como fallo ante error crítico
        if DataSaver is not None:
            try:
                attempts_to_save = max(1, iterations)
                tiempo_promedio_guardar = (elapsed / attempts_to_save) if attempts_to_save > 0 else 0.0
                print("DEBUG_SAVEFLOW: Guardando resultado FAIL (error crítico) en Excel mediante Main_Save_Data.finalize_session...")
                DataSaver.finalize_session(
                    objeto=item_name,
                    intentos=attempts_to_save,
                    exito=0,
                    tiempo_medio_intento=tiempo_promedio_guardar,
                    modo_encadenado_activo=True,
                    precio_objeto_base=None,
                    precio_venta_objeto_final=None,
                    tipo_exo=None,
                    kamas_iniciales_arg=None
                )
            except Exception as e2:
                print("ERROR: fallo al guardar fallo por error crítico con Main_Save_Data:", e2)

        return {
            "success": False,
            "attempts": iterations,
            "elapsed": elapsed,
            "time_per_attempt": elapsed / max(1, iterations),
            "error": repr(e)
        }

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
