import time
import pytesseract
import pyautogui
# Reutiliza funciones desde Extra_get_kamas.py
from Extra_get_kamas import preprocess_image

REGION_ITEM = (2539, 492, 2731 - 2539, 538 - 492)  # (x, y, width, height)

def check_inventory():
    """Verifica si la región contiene el texto 'Inventario'."""
    screenshot = pyautogui.screenshot(region=REGION_ITEM)
    processed_image = preprocess_image(screenshot)
    text = pytesseract.image_to_string(processed_image).strip()
    print(f"Texto leído: '{text}'")
    return "Inventario" in text

def main(input):
    print("Configurando equipo y recursos...")

    # Verificar si se lee "Inventario"
    if not check_inventory():
        print("No se detectó 'Inventario'. Realizando click en (1629, 1118)...")
        pyautogui.click(1629, 1118)
        print("Click en (1629, 1118) realizado.")
        time.sleep(1)  # espera adicional de 1 segundo

    # Realizar acción según el input
    if input == "Equipo":
        print("Seleccionando Equipo...")
        pyautogui.click(2350, 648)
        print("Click en (2350, 648) realizado.")
    elif input == "Recursos":
        print("Seleccionando Recursos...")
        pyautogui.click(2350, 789)
        print("Click en (2350, 789) realizado.")
    else:
        print("Input no reconocido. Usa 'Equipo' o 'Recursos'.")

if __name__ == "__main__":
    user_input = input("Introduce 'Equipo' o 'Recursos': ").strip()
    main(user_input)
