import time
import math
import pyautogui

from Mage_Data_Extractor import capture_and_read_stats
from Mage_Introduce_Runes import mage_introduce_runes
import Mage_Introduce_Exo as Mage_Introduce_Exo_mod
from Mage_Exo_Verify import verify_success
import Extra_Correo as Correo
import Aux_Forjamagia_imposible as AuxForja

# Coordenadas del área de lectura: (x1,y1) -> (x2,y2)
X1, Y1 = 1512, 761
X2, Y2 = 1863, 1634
REGION = (X1, Y1, X2 - X1, Y2 - Y1)  # (x, y, width, height)

# reducir pausa global un poco para acelerar interacciones
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01  # más rápido

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
def capture_with_retries(attempts=2, wait_between=0.06, item_stats=None):
    """
    Reintentos rápidos de OCR. Acepta lecturas estables (dos iguales) o una lectura final.
    Valores por defecto reducidos para acelerar el flujo.
    NUEVO: acepta item_stats opcional para pasarlo al extractor.
    """
    last_vals, last_text = None, ""
    for attempt in range(1, attempts + 1):
        start = time.time()
        valores, texto = capture_and_read_stats(item_stats=item_stats)
        elapsed = time.time() - start
        suma = sum(valores) if valores else 0
        nonzeros = sum(1 for v in (valores or []) if v != 0)
        print(f"Tiempo captura OCR: {elapsed:.2f}s (intento {attempt}) - suma={suma} nonzeros={nonzeros}")
        if suma > 0 and nonzeros > 0:
            if last_vals is not None and valores == last_vals:
                return valores, texto
            if attempt == attempts:
                return valores, texto
        last_vals, last_text = valores, texto
        if attempt < attempts:
            ensure_ui_active()
            time.sleep(wait_between)
    return last_vals or [], last_text or ""

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
    default_max = pre_clicks
    try:
        import RUN as MainModule
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
        # estimar incremento real para esta stat+col
        obj = stats_obj[i] if i < len(stats_obj) else ""
        inc = estimate_inc_in_main(obj, col, actual, stats_max[i] if i < len(stats_max) else 99999)
        deficit = minimo - actual
        # aproximación inicial (ceil)
        need = (deficit + inc - 1) // inc
        # evitar overshoot grande: si ceil produce mucha sobre elevación, reducir si posible
        overshoot = actual + need * inc - minimo
        if need > 1 and overshoot > (inc // 2):
            need -= 1
        if need < 1:
            need = 1
        planned_clicks[i] = min(need, default_max)

    # si no hay clicks planificados, dejar que la función original haga una pasada mínima
    if not any(planned_clicks):
        # marcar una pasada mínima para stats por debajo de min
        for i in range(n):
            if stats_actuales[i] < stats_min[i]:
                planned_clicks[i] = 1

    # Validación: si lectura es dudosa, NO intentar re-capturar aquí (para evitar múltiples capturas)
    suma = sum(stats_actuales)
    nonzeros = sum(1 for v in stats_actuales if v != 0)
    min_nonzeros = max(1, n // 6)
    if suma == 0 or nonzeros < min_nonzeros:
        print("Lectura dudosa antes de aplicar runas (apply_runes_optimized). Se aborta la aplicación para evitar capturas extra.")
        return False

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
      - Calcular tiempo medio por intento usando el contador global de EXO expuesto en Main.shared_state (si disponible).
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

    # nuevos contadores para ratio de error
    reads_over_max = 0
    reads_under_min = 0

    def _make_result(success, error=None, extra=None):
        """
        Helper para construir el diccionario de retorno con elapsed, attempts y time_per_attempt
        usando shared_state['exo_attempts'] (vía Main.shared_state si existe).
        Añade además lecturas over/under y ratio_error para diagnóstico.
        """
        elapsed = time.time() - start_time
        attempts_exo = 0
        try:
            import RUN as MainModule
            attempts_exo = int(MainModule.shared_state.get("exo_attempts", 0))
        except Exception:
            attempts_exo = 0
        time_per_attempt = (elapsed / attempts_exo) if attempts_exo > 0 else None
        # ratio_error: porcentaje reads_over_max / reads_under_min
        try:
            ratio_error = (reads_over_max / max(1, reads_under_min)) * 100.0
        except Exception:
            ratio_error = None
        res = {
            "success": bool(success),
            "attempts": attempts_exo,
            "elapsed": elapsed,
            "time_per_attempt": time_per_attempt,
            "reads_over_max": reads_over_max,
            "reads_under_min": reads_under_min,
            "ratio_error": ratio_error,
            "error": error
        }
        if extra and isinstance(extra, dict):
            res.update(extra)
        return res

    try:
        while True:
            # control (pausa/stop)
            if not _wait_handle_control(control_events):
                return _make_result(False, error="stopped_by_user")

            # ---------- UNA SÓLA CAPTURA RÁPIDA antes de decidir ----------
            valores, _ = capture_and_read_stats(item_stats=item_stats)
            stats_actuales = sanitize_and_align(valores, target_len)

            # si la captura única salió vacía, reintentar UNA VEZ rápida; no más
            if not stats_actuales or sum(stats_actuales) == 0:
                print("OCR vacío en captura única. Reintentando rápido una vez...")
                ensure_ui_active()
                time.sleep(0.06)
                valores2, _ = capture_and_read_stats(item_stats=item_stats)
                stats_actuales = sanitize_and_align(valores2, target_len)
                if not stats_actuales or sum(stats_actuales) == 0:
                    print("Persisten lecturas vacías tras reintento: omitiendo iteración.")
                    time.sleep(0.04)
                    ensure_ui_active()
                    continue

            print("Current stats:", stats_actuales)

            # Si ya cumplen mínimos -> intentar exo PERO primero hacemos una LECTURA RAPIDA previa y comprobamos max
            if stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
                print("Stats cumplen mínimos -> lectura previa para verificar máximos antes de EXO.")
                if not _wait_handle_control(control_events):
                    return _make_result(False, error="stopped_by_user")

                # lectura previa (una sola) con el extractor para certificar estado actual
                try:
                    fresh_vals, _ = capture_with_retries(attempts=1, item_stats=item_stats)
                    fresh_stats = sanitize_and_align(fresh_vals, target_len)
                except Exception as e:
                    print("WARNING: no se pudo realizar lectura previa antes de EXO:", e)
                    fresh_stats = stats_actuales

                # comprobar si hay stat(s) por encima del máximo
                any_over = False
                any_under = False
                max_list = item_stats.get("max", []) or []
                min_list = item_stats.get("min", []) or []
                for i in range(min(target_len, len(fresh_stats))):
                    val = fresh_stats[i]
                    # comprobar over max
                    if i < len(max_list) and max_list[i] is not None:
                        try:
                            if max_list[i] < val < 101:
                                any_over = True
                        except Exception:
                            pass
                    # comprobar under min
                    try:
                        if val < min_list[i]:
                            any_under = True
                    except Exception:
                        pass

                # actualizar contadores
                if any_over:
                    reads_over_max += 1
                    print(f"DEBUG: lectura previa muestra stats > max. reads_over_max={reads_over_max}")
                    # click único en (2107, 781) para señalizar y proceder (no introducir EXO)
                    try:
                        print("DEBUG: realizando click en (2107, 781) por exceso antes de intentar reducir/continuar.")
                        pyautogui.moveTo(2107, 781, duration=0.05)
                        pyautogui.click()
                        time.sleep(0.06)
                        ensure_ui_active()
                    except Exception as e:
                        print("WARNING: no se pudo realizar click en (2107,781):", e)
                    # no introducir exo si hay exceso; continuar loop para intentar corrección en próximas iteraciones
                    continue

                if any_under:
                    reads_under_min += 1
                    print(f"DEBUG: lectura previa muestra stats < min. reads_under_min={reads_under_min}. No se puede introducir EXO.")
                    # no introducir exo porque alguna stat está por debajo del mínimo
                    continue

                # si llegamos aquí -> todas las stats están entre min y max: introducir exo
                try:
                    Mage_Introduce_Exo_mod.introducir_exo()
                except Exception:
                    try:
                        from Mage_Introduce_Exo import introducir_exo as __introducir_exo_fallback
                        __introducir_exo_fallback()
                    except Exception as _e:
                        print("ERROR: no se pudo ejecutar introducir_exo():", _e)

                time.sleep(0.08)  # dar tiempo al juego
                print("Verificando exo...")
                if verify_success():
                    try:
                        Correo.send_mail(item_name, "Exito PA")
                    except Exception:
                        pass

                    # intentar guardar directamente si Main_Save_Data está disponible
                    saved_bool = False
                    aux_executed = False
                    run_aux_flag = False
                    try:
                        try:
                            import Main_Save_Data as DataSaver
                        except Exception:
                            import sys
                            from pathlib import Path
                            sys.path.insert(0, str(Path(__file__).parent.parent))
                            import Main_Save_Data as DataSaver
                        result_save = DataSaver.finalize_session(
                            objeto=item_name,
                            intentos=int(_make_result(True)["attempts"]) or 1,
                            exito="PA",
                            tiempo_medio_intento=None,  # Main will compute based on shared_state
                            modo_encadenado_activo=True,
                            precio_objeto_base=None,
                            precio_venta_objeto_final=None,
                            tipo_exo="PA",
                            kamas_iniciales_arg=None
                        )
                        saved_bool = (result_save in (0, True))
                    except Exception as e:
                        print("Aviso: no se pudo ejecutar Main_Save_Data.finalize_session desde Mage_Main:", e)
                        saved_bool = False

                    if saved_bool:
                        try:
                            try:
                                import Aux_Guardar_exito as Aux
                            except Exception:
                                import sys
                                from pathlib import Path
                                sys.path.insert(0, str(Path(__file__).parent.parent))
                                import Aux_Guardar_exito as Aux
                            Aux.perform_dofus_sequence()
                            aux_executed = True
                        except Exception as e:
                            print("Aviso: no se pudo ejecutar Aux_Guardar_exito.perform_dofus_sequence():", e)
                            aux_executed = False
                    else:
                        run_aux_flag = True

                    return _make_result(True, extra={"saved": saved_bool, "aux_executed": aux_executed, "run_aux": run_aux_flag})
                else:
                    print("EXO falló. Continuando con runas si procede.")
                    time.sleep(0.06)
                    ensure_ui_active()
                    continue

            # aplicar runas optimizadas (priorizar <30% min y reducir lecturas)
            print("Aplicando runas (optimizadas)...")
            prev_stats = normalize_prev(prev_stats, target_len)

            suma = sum(stats_actuales) if stats_actuales else 0
            nonzeros = sum(1 for v in (stats_actuales or []) if v != 0)
            min_nonzeros = max(1, target_len // 6)
            if suma == 0 or nonzeros < min_nonzeros:
                print("Lectura dudosa antes de aplicar runas. No se aplicarán runas en esta iteración.")
                time.sleep(0.04)
                ensure_ui_active()
                continue

            applied = apply_runes_optimized(stats_actuales, item_stats["min"], item_stats.get("obj", []), item_stats.get("max", []), control_events=control_events, pre_clicks=3)
            if applied is False:
                print("No se aplicaron runas en esta iteración.")
                time.sleep(0.04)
                ensure_ui_active()
                continue

            if not _wait_handle_control(control_events):
                return _make_result(False, error="stopped_by_user")

            time.sleep(0.05)
            stats_nuevos, _ = capture_and_read_stats(item_stats=item_stats)
            stats_nuevos = sanitize_and_align(stats_nuevos, target_len)

            print(f"Post-runas stats: {stats_nuevos}")

            if prev_stats is not None and stats_nuevos == prev_stats:
                no_progress_count += 1
                print(f"No progress ({no_progress_count}/{no_progress_limit})")
                if no_progress_count >= no_progress_limit:
                    try:
                        # Nueva lógica: comprobar si aparece "Forjamagia imposible"
                        found_impossible = False
                        if AuxForja is not None:
                            try:
                                found_impossible, dbg_texts = AuxForja.forjamagia_impossible_at_points(
                                    points=[(1788, 1050), (2048, 1087)],
                                    region_size=(600, 120),
                                    lang='spa',
                                    debug_save_folder=None,
                                    save_prefix=None
                                )
                            except Exception as e:
                                print("WARNING: fallo al ejecutar AuxForja.forjamagia_impossible_at_points:", e)
                                found_impossible = False

                        if found_impossible:
                            print("DEBUG: 'Forjamagia imposible' detectado -> click en (1930,1143) y reinicio del contador.")
                            try:
                                pyautogui.moveTo(1930, 1143, duration=0.05)
                                pyautogui.click()
                                time.sleep(0.08)
                                ensure_ui_active()
                            except Exception as e:
                                print("WARNING: no se pudo hacer click en (1930,1143):", e)
                            # resetear estado para reintentar el bucle normal
                            no_progress_count = 0
                            prev_stats = None
                            time.sleep(0.06)
                            continue

                    except Exception:
                        pass

                    # Si no se detectó "Forjamagia imposible" o Aux no disponible -> comportamiento original
                    try:
                        Correo.send_mail(item_name, "Sin runas")
                    except Exception:
                        pass
                    return _make_result(False, error="no_progress")
            else:
                no_progress_count = 0

            prev_stats = list(stats_nuevos)
            time.sleep(0.04)
            continue

    except Exception as e:
        try:
            Correo.send_mail(item_name, "Finalizar forzado")
        except Exception:
            pass
        return _make_result(False, error=repr(e))

# --- Nuevo helper: estimar incremento por stat (coincidente con Mage_Introduce_Runes) ---
def estimate_inc_in_main(obj_name, col_index, actual=0, maximo=99999):
    """
    Estima el incremento real por click según el nombre de stat y la columna elegida.
    col_index: 0|1|2 (correspondiente a COLUMNAS_X pequeñas/medias/grandes lógicas)
    """
    name = str(obj_name).lower() if obj_name else ""
    if col_index == 0:
        return 1
    if col_index == 1:
        # columna media
        if "re" in name or "res" in name or "resistencia" in name:
            return 3
        return 3
    if col_index == 2:
        # columna grande
        if "vi" in name or "vital" in name:
            return 50
        if "ini" in name:
            return 100
        return 10
    return 1

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
