import time
import pyautogui

from Mage_Data_Extractor import capture_and_read_stats
from Mage_Introduce_Runes import mage_introduce_runes
from Mage_Introduce_Exo import introducir_exo
from Mage_Exo_Verify import verify_success

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

def stats_within_limits(stats_actuales, stats_min, stats_max):
    """
    Returns True if all stats are within min and max (inclusive).
    """
    for i in range(len(stats_actuales)):
        if stats_actuales[i] < stats_min[i] or stats_actuales[i] > stats_max[i]:
            return False
    return True

def mage_main(item_name, item_stats, max_iterations=None, no_progress_limit=6):
    """
    Ahora itera hasta que todas las stats >= stats_min.
    - max_iterations: opcional para proteger contra bucle infinito (None = sin límite).
    - no_progress_limit: aborta si no hay progreso tras N iteraciones.
    """
    print(f"Starting mage loop for item: {item_name}")
    ensure_ui_active()

    iterations = 0
    no_progress_count = 0
    prev_stats = None

    while True:
        # extraer stats actuales
        stats_actuales, _ = capture_and_read_stats()
        if not stats_actuales or len(stats_actuales) == 0:
            print("No se han detectado stats (OCR vacío). Reintentando tras breve espera.")
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
                print("Exo successful. Finished.")
                break
            else:
                print("Exo failed. Continuing loop.")
                time.sleep(0.2)
                ensure_ui_active()
                continue

        # si no están dentro, aplicar runas hasta que lo estén (o se alcance seguridad)
        print("Applying runes until stats >= min...")
        while not stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
            if max_iterations is not None and iterations >= max_iterations:
                print(f"Reached max_iterations ({max_iterations}). Aborting rune loop.")
                return

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
                # no bloquear el bucle completo; reintentar tras pequeña espera
                time.sleep(0.2)
                ensure_ui_active()
                continue

            # esperar menos para acelerar, luego re-leer
            time.sleep(0.18)
            stats_actuales, _ = capture_and_read_stats()
            if not stats_actuales:
                print("OCR returned vacío tras introducir runas, reintentando lectura...")
                time.sleep(0.2)
                ensure_ui_active()
                stats_actuales, _ = capture_and_read_stats()

            iterations += 1
            print(f"Iteration {iterations} -> stats: {stats_actuales}")

            # detectar no progreso
            if prev_stats is not None and stats_actuales == prev_stats:
                no_progress_count += 1
                print(f"No progress ({no_progress_count}/{no_progress_limit})")
                if no_progress_count >= no_progress_limit:
                    print("No progress after several iterations. Aborting to avoid infinite loop.")
                    return
            else:
                no_progress_count = 0

            prev_stats = stats_actuales

        # al salir del bucle interno, volver a la comprobación general (y posiblemente introducir exo)
        time.sleep(0.12)
        continue

if __name__ == "__main__":
    # Example usage: ask for item name and load stats from Setup_Item_Stats_Database
    time.sleep(0.6)  # menos espera antes de iniciar
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import Setup_Item_Stats_Database

    item_name = input("Enter item name: ").strip()
    item_stats = Setup_Item_Stats_Database.get_item_stats(item_name)
    if not item_stats:
        print("Item not found in database.")
        sys.exit(1)

    # por defecto sin límite: funcionará hasta que stats >= min o hasta que no-progreso cause abort
    mage_main(item_name, item_stats, max_iterations=None)
