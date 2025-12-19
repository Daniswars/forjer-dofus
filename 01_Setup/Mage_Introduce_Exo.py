import pyautogui
import time

def leer_nombre_runa():
    # Importa y usa la función de Setup_Read_First_Rune_Name
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        import Setup_Read_First_Rune_Name
    except Exception as e:
        print("No se pudo importar Setup_Read_First_Rune_Name:", e)
        return None
    return Setup_Read_First_Rune_Name.read_new_item_name()

def introducir_exo():
    nombre_runa = leer_nombre_runa()
    if not nombre_runa:
        print("No se pudo leer el nombre de la runa.")
        return
    nombre_runa = nombre_runa.lower()
    if nombre_runa in ["runa ga pa", "runa ga pm", "runa ga al"]:
        print(f"Detectada {nombre_runa}. Procediendo con la introducción del exo...")
        # 1: Doble click con movimiento en (2486, 731)

        pyautogui.moveTo(2486, 731)
        time.sleep(0.2)
        pyautogui.click(clicks=2, interval=0.1)
        time.sleep(0.5)
        pyautogui.doubleClick()
        time.sleep(0.5)
        # 2: Click en (1744, 655)
        pyautogui.click(1744, 655)
        print("Exo introducido.")
    else:
        print(f"Runa detectada: {nombre_runa}. No es exo PA/PM/Al. No se hace nada.")

if __name__ == "__main__":
    introducir_exo()

