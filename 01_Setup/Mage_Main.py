import time

from Mage_Data_Extractor import capture_and_read_numbers
from Mage_Introduce_Runes import mage_introduce_runes
from Mage_Introduce_Exo import introducir_exo
from Mage_Exo_Verify import verify_success

# Coordenadas del área de lectura: (x1,y1) -> (x2,y2)
X1, Y1 = 1512, 761
X2, Y2 = 1863, 1634
REGION = (X1, Y1, X2 - X1, Y2 - Y1)  # (x, y, width, height)

def stats_within_limits(stats_actuales, stats_min, stats_max):
    """
    Returns True if all stats are within min and max (inclusive).
    """
    for i in range(len(stats_actuales)):
        if stats_actuales[i] < stats_min[i] or stats_actuales[i] > stats_max[i]:
            return False
    return True

def mage_main(item_name, item_stats):
    """
    Main mage loop.
    Inputs:
        item_name: str, name of the item.
        item_stats: dict, must contain keys 'min', 'max', 'obj'.
    """
    print(f"Starting mage loop for item: {item_name}")
    while True:
        # 1. Extract current stats
        print("Extracting current stats...")
        stats_actuales, _ = capture_and_read_numbers(region=REGION, save_path=None, max_lines=13, lang='eng')
        print("Current stats:", stats_actuales)

        # 2. Check if stats are within limits
        if stats_within_limits(stats_actuales, item_stats["min"], item_stats["max"]):
            print("Stats are within limits. Proceeding to exo introduction.")
            # 3. Introduce exo
            introducir_exo()
            # 4. Verify exo
            print("Verifying exo...")
            if verify_success():
                print("Exo successful! Exiting loop.")
                break
            else:
                print("Exo failed. Restarting mage loop.")
                time.sleep(1)
        else:
            print("Stats not within limits. Introducing runes...")
            mage_introduce_runes(
                stats_actuales=stats_actuales,
                stats_min=item_stats["min"],
                stats_obj=item_stats["obj"],
                stats_max=item_stats["max"]
            )
            time.sleep(1)

if __name__ == "__main__":
    # Example usage: ask for item name and load stats from Setup_Item_Stats_Database
    time.sleep(1)  # Give user time to switch to terminal
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import Setup_Item_Stats_Database

    item_name = input("Enter item name: ").strip()
    item_stats = Setup_Item_Stats_Database.get_item_stats(item_name)
    if not item_stats:
        print("Item not found in database.")
        sys.exit(1)

    mage_main(item_name, item_stats)

