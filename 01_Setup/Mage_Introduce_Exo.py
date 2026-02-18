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
    """
    Introduce exo de forma fiable:
     - realiza la secuencia mínima de movimientos/clicks evitando movimientos falsos
     - devuelve True si aplicó el exo (éxito), False en caso contrario
     - NO modifica shared_state ni realiza side-effects de contador (lo hará el wrapper en Main)
    """
    nombre_runa = leer_nombre_runa()
    if not nombre_runa:
        print("No se pudo leer el nombre de la runa.")
        return False

    nombre_runa = nombre_runa.lower()
    if nombre_runa in ["runa ga pa", "runa ga pm", "runa ga al", "pa", "pm", "al"]:
        print(f"Detectada {nombre_runa}. Procediendo con la introducción del exo...")
        try:
            # Secuencia compacta y fiable: seleccionar la runa (un click), breve espera, click de aplicación
            pyautogui.moveTo(2486, 731, duration=0.1)
            time.sleep(0.2)
            pyautogui.click(clicks=2, interval=0.1)
            time.sleep(0.5)
            pyautogui.moveTo(1744, 655, duration=0.1)
            pyautogui.click(1744, 655)  # aplicar exo
            time.sleep(0.14)  # dejar tiempo a que el juego procese la aplicación
            print("Exo introducido (secuencia minima).")
            return True
        except Exception as e:
            print("ERROR al introducir exo (pyautogui):", e)
            return False
    else:
        print(f"Runa detectada: {nombre_runa}. No es exo PA/PM/Al. No se hace nada.")
        return False

if __name__ == "__main__":
    ok = introducir_exo()
    print("introducir_exo ->", ok)

