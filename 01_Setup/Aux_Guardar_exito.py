import pyautogui
import time

def perform_dofus_sequence():
    """
    Executes a specific sequence of actions in Dofus:
    Presses Escape, clicks a precise location (replacing 'H' press),
    clicks a precise location, double-clicks another location,
    and then repeats Escape and the click.
    """
    print("Starting Dofus action sequence...")

    # Press Escape
    print("Pressing Escape...")
    pyautogui.click(x = 2947, y = 517)
    time.sleep(0.7) # Short delay to ensure the game registers the input

    # Click at X=3813, Y=331 (replaces 'H' press)
    print("Clicking at X=3813, Y=331 (replacing 'H' key)...")
    pyautogui.click(x=3813, y=331)
    time.sleep(1.2) # Longer delay as this click might open an interface

    # Click at the first position (from original script)
    print("Clicking at X=1590, Y=1021...")
    pyautogui.click(x=1590, y=1021)
    time.sleep(2) # Delay after the click

    pyautogui.click(x=1370, y=650)
    time.sleep(1)  # Delay after the click

    # Double click at the second position
    print("Double clicking at X=1490, Y=732...")
    pyautogui.moveTo(x=2150, y=722)
    time.sleep(1)
    pyautogui.click(clicks=2, interval=0.1)
    time.sleep(1)
    pyautogui.click(x=2630, y=513)
    time.sleep(2)  # Delay after the click

    # Click at X=3813, Y=331 again (replaces 'H' press)
    print("Clicking at X=3813, Y=331 again (replacing 'H' key)...")
    pyautogui.click(x=3813, y=331)
    time.sleep(1.2)

    print("Dofus action sequence completed.")

# --- How to Run the Script ---
if __name__ == "__main__":
    # IMPORTANT: Ensure your Dofus window is active and in focus BEFORE this countdown ends.
    print("Script will start in 5 seconds. Please switch to your Dofus window NOW!")
    time.sleep(5) # Gives you time to switch to the Dofus window

    perform_dofus_sequence()