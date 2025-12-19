import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image
import time
import os
import psutil

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

# --- Configuration ---
DOFUS_WINDOW_TITLE = None  # Initialized to None, will be set dynamically
DOFUS_LAUNCHER_TITLE = "Ankama Launcher"

# Coordinates for actions
LAUNCHER_PLAY_BUTTON_COORD = (1242, 991)
CHARACTER_PLAY_BUTTON_COORD = (2350, 1593)

BRAKMAR_TOP_LEFT = (4, 63)
BRAKMAR_BOTTOM_RIGHT = (160, 100)
BRAKMAR_CHECK_TIMEOUT_SECONDS = 20  # NEW: Timeout for Brakmar detection

# Coordinates for checking for the "mago" text (the forge interface is active)
MAGUS_TOP_LEFT = (993, 597)
MAGUS_BOTTOM_RIGHT = (1144, 627)

# --- COORDINATES FOR PLACING THE OBJECT ON THE WORKBENCH ---
PLACE_OBJECT_CLICK_1_COORD = (2352, 667)
PLACE_OBJECT_CLICK_2_COORD = (2473, 732)
PLACE_OBJECT_CLICK_3_COORD = (2473, 732) # Redundant but included as specified

# Coordinates for forge tables to test
FORGE_TABLE_CLICK_1 = (1857, 1338)
FORGE_TABLE_CLICK_2 = (1624, 1145)
FORGE_TABLE_CLICK_3 = (1581, 1278)

# --- COORDINATES FOR WORKBENCH SELECTION ---
# Workbench for Rings/Amulets (standard)
WORKBENCH_RING_AMULET_COORD = (1609, 1067)  # Double click to add object

# Workbench for Shields
WORKBENCH_SHIELD_CLICK_1 = (1341, 415)  # First click for shield workbench
WORKBENCH_SHIELD_CLICK_2 = (1435, 558)  # Second click for shield workbench

# Workbench for Capes/Hats
WORKBENCH_CAPE_HAT_COORD = (1919, 405)  # Click for cape/hat workbench

# --- COORDINATES FOR POST-WORKBENCH ACTIONS ---
RESOURCE_MENU_CLICK_COORD = (2344, 811)  # Click for resource menu
ORDER_DROPDOWN_CLICK_COORD = (2536, 630)  # Click for order dropdown
SCROLL_MOUSE_POS_COORD = (2560, 758)  # Mouse position for scrolling
SORT_BY_LEVEL_CLICK_COORD = (2558, 927)  # Click to sort by level


# --- Helper Functions (No changes needed here unless specified) ---

def is_window_open(title: str) -> bool:
    """Checks if a window with the given title is currently open."""
    return gw.getWindowsWithTitle(title) != []


def find_dofus_window_title() -> str | None:
    """
    Searches for the Dofus game window title more robustly.
    Prints all window titles for debugging.
    """
    print("Searching for Dofus window title...")
    all_windows = gw.getAllWindows()
    dofus_title = None
    for win in all_windows:
        title = win.title
        # print(f"Found window: '{title}'") # Uncomment to debug ALL window titles
        if 'prossil' in title.lower() or 'dofus' in title.lower():  # More flexible keywords
            # Filter out launcher if it has 'dofus' in title and isn't the main game
            if "launcher" not in title.lower() and "beta" not in title.lower():
                dofus_title = title
                print(f"Detected Dofus game window title: '{dofus_title}'")
                return dofus_title
    print("Dofus game window title not found among open windows based on keywords.")
    return None


def close_dofus_window(window_title: str):
    """
    Closes the Dofus game window by bringing it to the foreground and sending Alt+F4.
    If that fails, it attempts to kill the process.
    """
    print(f"Attempting to close Dofus window: '{window_title}'...")
    dofus_windows = gw.getWindowsWithTitle(window_title)

    if not dofus_windows:
        print(f"Window '{window_title}' not found or already closed. No action needed.")
        return True  # Indicate successful "closing" if it's already gone

    dofus_window = dofus_windows[0]

    # Try Alt+F4 multiple times
    for attempt in range(3):
        if not is_window_open(window_title):
            print(f"Window '{window_title}' closed after {attempt + 1} Alt+F4 attempts.")
            return True  # Successfully closed

        print(f"Attempt {attempt + 1}: Activating Dofus window and sending Alt+F4...")
        try:
            dofus_window.activate()  # Bring the window to the foreground
            time.sleep(1.5)  # Give it ample time to become active

            pyautogui.keyDown('alt')
            pyautogui.press('f4')
            pyautogui.keyUp('alt')
            time.sleep(3)  # Give it some time to fully close

        except Exception as e:
            print(f"Error during Alt+F4 attempt {attempt + 1}: {e}")
            time.sleep(1)  # Small pause before next attempt

    # If Alt+F4 failed after multiple attempts, try to kill the process
    if is_window_open(window_title):
        print(f"Warning: Window '{window_title}' is still open after multiple Alt+F4 attempts.")
        print("Attempting to forcefully close the Dofus process...")
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                # Adjust 'dofus.exe' if your Dofus client executable name is different
                if "dofus.exe" in proc.info['name'].lower():
                    print(f"Found Dofus process: PID {proc.info['pid']}, Name: {proc.info['name']}. Killing...")
                    proc.kill()
                    time.sleep(3)  # Give process time to terminate
                    print("Dofus process killed.")
                    return True
            print("Could not find a Dofus process to kill.")
            return False
        except Exception as e:
            print(f"Error attempting to kill Dofus process: {e}")
            return False
    return False  # Failed to close


def read_text_from_screen(top_left: tuple, bottom_right: tuple, lang='eng', config='--psm 6') -> str:
    """
    Captures a region of the screen and extracts text using Tesseract.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    width = x2 - x1
    height = y2 - y1

    if width <= 0 or height <= 0:
        print(f"Warning: Invalid capture region (width={width}, height={height}). Returning empty string.")
        return ""

    try:
        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        text = pytesseract.image_to_string(screenshot, lang=lang, config=config).strip()
        # print(f"OCR read text in region {top_left} to {bottom_right}: '{text}'") # Only print if needed for debug
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""


def pre_check_game_status_with_timeout() -> bool:
    """
    Performs a pre-check by trying to read 'Brakmar' to confirm the game is loaded,
    with a timeout.
    """
    print(f"Pre-check: Attempting to read 'Brakmar' in-game for up to {BRAKMAR_CHECK_TIMEOUT_SECONDS} seconds...")
    start_time = time.time()
    while time.time() - start_time < BRAKMAR_CHECK_TIMEOUT_SECONDS:
        detected_text = read_text_from_screen(BRAKMAR_TOP_LEFT, BRAKMAR_BOTTOM_RIGHT)
        if "brakmar" in detected_text.lower():
            print(f"Pre-check successful: 'Brakmar' detected after {int(time.time() - start_time)} seconds.")
            return True
        print(f"Brakmar not detected yet. Retrying in 2 seconds... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(2)  # Wait before retrying
    print(f"Pre-check failed: 'Brakmar' not detected within {BRAKMAR_CHECK_TIMEOUT_SECONDS} seconds.")
    return False


# --- Main Function ---

def restart_dofus_and_click_forge(objeto_seleccionado: str):
    """
    Automates the process of restarting Dofus and clicking a forge table,
    followed by adding object, setting resource menu, and sorting.
    The workbench selection is dynamic based on `objeto_seleccionado`.
    """
    print("--- Starting Dofus Restart and Forge Click Automation ---")
    print(f"Selected object for magueo: '{objeto_seleccionado}'")

    global DOFUS_WINDOW_TITLE

    # 1. Close Dofus if it's already open
    current_dofus_title = find_dofus_window_title()
    if current_dofus_title:
        DOFUS_WINDOW_TITLE = current_dofus_title
        if not close_dofus_window(DOFUS_WINDOW_TITLE):
            print("Failed to close Dofus window. Automation stopped.")
            return False
    else:
        print("Dofus window not found at the start. Assuming it's closed, proceeding to launch from Ankama Launcher.")

    # 2. Open Launcher and click "Play" to start the game
    print(f"Looking for Dofus Launcher window: '{DOFUS_LAUNCHER_TITLE}'...")
    try:
        launcher_windows = gw.getWindowsWithTitle(DOFUS_LAUNCHER_TITLE)
        if not launcher_windows:
            print(f"Error: Dofus Launcher window '{DOFUS_LAUNCHER_TITLE}' not found. Please open it manually.")
            return False

        launcher_window = launcher_windows[0]
        if not launcher_window.isActive:
            print("Activating Dofus Launcher window...")
            launcher_window.activate()
            time.sleep(1)

        print(f"Clicking launcher play button at {LAUNCHER_PLAY_BUTTON_COORD}...")
        pyautogui.click(LAUNCHER_PLAY_BUTTON_COORD[0], LAUNCHER_PLAY_BUTTON_COORD[1])
        time.sleep(15)  # Wait for the game client to load
        print("Waited 15 seconds for game client to load.")

        # 3. Click "Jugar" on the character selection screen
        print(f"Clicking character play button at {CHARACTER_PLAY_BUTTON_COORD}...")
        pyautogui.click(CHARACTER_PLAY_BUTTON_COORD[0], CHARACTER_PLAY_BUTTON_COORD[1])
        time.sleep(10)  # Wait for the game to fully load after character selection
        print("Waited 10 seconds for character to log in.")

        # 4. Verify game loaded by reading "Brakmar" with timeout
        if not pre_check_game_status_with_timeout():
            print("Failed to confirm game loaded within timeout. Automation stopped.")
            return False

        objeto_lower = objeto_seleccionado.lower()
        print(f"Object name in lowercase for check: '{objeto_lower}'")

        # Dynamic workbench selection based on the object type
        if "anillo" in objeto_lower or "amuleto" in objeto_lower:
            print(f"'{objeto_seleccionado}' detected. Using Ring/Amulet workbench.")
            # Double click to add object to workbench
            print(f"Moving mouse to {WORKBENCH_RING_AMULET_COORD} for double-clicking...")
            pyautogui.moveTo(WORKBENCH_RING_AMULET_COORD[0], WORKBENCH_RING_AMULET_COORD[1])
            time.sleep(3)  # Small pause after moving mouse
            print("Performing custom double click...")
            pyautogui.click(clicks=2, interval=0.1)  # Custom double click
            time.sleep(3)  # Pause after double click

        elif "escudo" in objeto_lower:
            print(f"'{objeto_seleccionado}' detected. Using Shield workbench.")
            # Click 1 for shield workbench
            print(f"Clicking Shield workbench first point at {WORKBENCH_SHIELD_CLICK_1}...")
            pyautogui.click(WORKBENCH_SHIELD_CLICK_1[0], WORKBENCH_SHIELD_CLICK_1[1])
            time.sleep(3)  # Delay for character to move/interface to update

            # Click 2 for shield workbench
            print(f"Clicking Shield workbench second point at {WORKBENCH_SHIELD_CLICK_2}...")
            pyautogui.click(WORKBENCH_SHIELD_CLICK_2[0], WORKBENCH_SHIELD_CLICK_2[1])
            time.sleep(2)  # Pause after click


        elif "capa" in objeto_lower or "sombrero" in objeto_lower:
            print(f"'{objeto_seleccionado}' detected. Using Cape/Hat workbench.")
            # Click for cape/hat workbench
            print(f"Clicking Cape/Hat workbench at {WORKBENCH_CAPE_HAT_COORD}...")
            pyautogui.click(WORKBENCH_CAPE_HAT_COORD[0], WORKBENCH_CAPE_HAT_COORD[1])
            time.sleep(0.8)  # Pause after click

        else:
            print(f"Warning: Unknown object type '{objeto_seleccionado}'. Defaulting to Ring/Amulet workbench.")
            # Default to ring/amulet if type is not recognized
            print(f"Moving mouse to {WORKBENCH_RING_AMULET_COORD} for double-clicking...")
            pyautogui.moveTo(WORKBENCH_RING_AMULET_COORD[0], WORKBENCH_RING_AMULET_COORD[1])
            time.sleep(0.2)
            print("Performing custom double click...")
            pyautogui.click(clicks=2, interval=0.1)
            time.sleep(0.8)

        # --- Subsequent actions (common for all types) ---
        # These actions are performed regardless of which workbench was selected

        # 1 Introduce item in workbench
        print("Placing object on workbench...")
        # Step 1: Click at (2352, 667)
        pyautogui.click(PLACE_OBJECT_CLICK_1_COORD)
        time.sleep(0.5)

        # Step 2: Double-click at (2473, 732)
        pyautogui.moveTo(PLACE_OBJECT_CLICK_2_COORD[0], PLACE_OBJECT_CLICK_2_COORD[1])
        time.sleep(0.5)
        print("Performing custom double click...")
        pyautogui.click(clicks=2, interval=0.1)
        time.sleep(0.8)

        # 2. Click for resource menu
        print(f"Clicking resource menu at {RESOURCE_MENU_CLICK_COORD}...")
        pyautogui.click(RESOURCE_MENU_CLICK_COORD[0], RESOURCE_MENU_CLICK_COORD[1])
        time.sleep(0.5)  # Short pause after click

        # 3. Click for order dropdown
        print(f"Clicking order dropdown at {ORDER_DROPDOWN_CLICK_COORD}...")
        pyautogui.click(ORDER_DROPDOWN_CLICK_COORD[0], ORDER_DROPDOWN_CLICK_COORD[1])
        time.sleep(0.5)  # Short pause after click to ensure dropdown appears

        # 4. Scroll down
        print(f"Moving mouse to {SCROLL_MOUSE_POS_COORD} for scrolling...")
        pyautogui.moveTo(SCROLL_MOUSE_POS_COORD[0], SCROLL_MOUSE_POS_COORD[1])
        time.sleep(0.5)  # Pause for mouse to move
        print("Scrolling down...")
        pyautogui.scroll(-500)  # Scroll down by 500 units (adjust as needed)
        time.sleep(1)  # Pause after scroll to ensure menu updates

        # 5. Click to sort by level
        print(f"Clicking to sort by level at {SORT_BY_LEVEL_CLICK_COORD}...")
        pyautogui.click(SORT_BY_LEVEL_CLICK_COORD[0], SORT_BY_LEVEL_CLICK_COORD[1])
        time.sleep(1)  # Pause after click to ensure sort applies

        print("--- Dofus Restart and Forge Click Automation Finished ---")
        return True

    except gw.PyGetWindowException as e:
        print(
            f"PyGetWindow error: {e}. Make sure the Dofus game and launcher windows are running with the correct titles.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


# --- Example Usage (for testing the module directly) ---
if __name__ == "__main__":
    # Create a debug captures directory if it doesn't exist
    if not os.path.exists("debug_captures"):
        os.makedirs("debug_captures")

    print("\n--- Running Dofus Restart Module Test ---")
    print("Please ensure Dofus and its launcher are visible on screen for testing.")
    print("The script will attempt to close Dofus, restart it via the launcher,")
    print("verify the game loads, and then click a forge table and perform subsequent actions.")

    # Test with a Shield
    print("\n--- Testing with 'Escudo Volante' (should use shield workbench) ---")
    success_shield = restart_dofus_and_click_forge("Escudo Volante")
    if success_shield:
        print("\nAutomation sequence for Escudo completed successfully.")
    else:
        print("\nAutomation sequence for Escudo failed or encountered an issue.")