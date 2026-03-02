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
    REWORKED: Solo reinicia la sesión del cliente:
    - cierra la ventana del juego si está abierta,
    - hace click en 'Play' del launcher,
    - selecciona el personaje (click en CHARACTER_PLAY_BUTTON_COORD),
    - espera la carga y verifica (pre_check_game_status_with_timeout),
    - hace click en el workbench (1626, 1154).
    NO realiza ninguna acción de colocación de objetos.
    """
    print("--- Starting Dofus session reset (no workbench actions) ---")
    print(f"Ignoring objeto_seleccionado='{objeto_seleccionado}' for session reset.")

    global DOFUS_WINDOW_TITLE

    try:
        # 1. Close Dofus if it's already open
        current_dofus_title = find_dofus_window_title()
        if current_dofus_title:
            DOFUS_WINDOW_TITLE = current_dofus_title
            if not close_dofus_window(DOFUS_WINDOW_TITLE):
                print("Failed to close Dofus window. Session reset aborted.")
                return False
        else:
            print("Dofus window not found at the start. Proceeding to launcher.")

        # 2. Open Launcher and click "Play" to start the game
        print(f"Looking for Dofus Launcher window: '{DOFUS_LAUNCHER_TITLE}'...")
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
        # Esperar lo suficiente para que el cliente aparezca
        time.sleep(15)
        print("Clicked Play and waited for the game client to load (15s).")

        # 3. Click "Jugar" en la pantalla de selección de personaje
        print(f"Clicking character play button at {CHARACTER_PLAY_BUTTON_COORD}...")
        pyautogui.click(CHARACTER_PLAY_BUTTON_COORD[0], CHARACTER_PLAY_BUTTON_COORD[1])
        time.sleep(10)  # Esperar a que el personaje entre en el mundo
        print("Clicked character Play and waited (10s).")

        # 4. Verificar que el juego haya terminado de cargar (ej. detectando 'Brakmar')
        if not pre_check_game_status_with_timeout():
            print("Failed to confirm game loaded within timeout. Session reset incomplete.")
            return False

        # 5. NUEVO: Click en el workbench para abrirlo
        WORKBENCH_COORD = (1626, 1154)
        print(f"Clicking workbench at {WORKBENCH_COORD} to open it...")
        pyautogui.click(WORKBENCH_COORD[0], WORKBENCH_COORD[1])
        time.sleep(2)  # Esperar a que se abra la ventana del workbench
        print("Workbench clicked and opened.")

        print("--- Session reset completed successfully (workbench opened) ---")
        return True

    except gw.PyGetWindowException as e:
        print(
            f"PyGetWindow error: {e}. Asegúrate de que el launcher y el cliente estén abiertos con los títulos correctos.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during session reset: {e}")
        return False


# --- Example Usage (for testing the module directly) ---
if __name__ == "__main__":
    # Create a debug captures directory if it doesn't exist
    if not os.path.exists("../debug_captures"):
        os.makedirs("../debug_captures")

    print("\n--- Running Dofus Session Reset Module Test ---")
    print("Este test solo reiniciará la sesión: cerrará el cliente, pulsará Play en el launcher")
    print("y seleccionará el personaje. NO realizará acciones de workbench.")
    success = restart_dofus_and_click_forge("IGNORED_PARA_RESET")
    if success:
        print("\nSession reset completed successfully.")
    else:
        print("\nSession reset failed or encountered an issue.")
