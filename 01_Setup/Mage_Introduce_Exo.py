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
     - incrementa contador global de intentos EXO si Main.shared_state existe
     - realiza la secuencia mínima de movimientos/clicks evitando movimientos falsos
    """
    nombre_runa = leer_nombre_runa()
    if not nombre_runa:
        print("No se pudo leer el nombre de la runa.")
        return

    # Intentar incrementar contador en Main.shared_state si está disponible
    try:
        import Main
        if hasattr(Main, "shared_state") and isinstance(Main.shared_state, dict):
            Main.shared_state["exo_attempts"] = Main.shared_state.get("exo_attempts", 0) + 1
    except Exception:
        # Si no se puede importar Main (por path o circular import), ignorar el incremento
        try:
            # alternativamente intentar importar desde package path
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            import Main as Main2
            if hasattr(Main2, "shared_state"):
                Main2.shared_state["exo_attempts"] = Main2.shared_state.get("exo_attempts", 0) + 1
        except Exception:
            pass

    nombre_runa = nombre_runa.lower()
    if nombre_runa in ["runa ga pa", "runa ga pm", "runa ga al"]:
        print(f"Detectada {nombre_runa}. Procediendo con la introducción del exo...")
        # Hacer una secuencia compacta y fiable: moverse brevemente, doble click en la posición del objeto y confirmar
        try:
            # mover con pequeña duración para evitar "falso movimiento"
            pyautogui.moveTo(2486, 731, duration=0.05)
            pyautogui.click(2486, 731, clicks=2, interval=0.06)
            time.sleep(0.18)
            # click final de aplicación
            pyautogui.click(1744, 655)
            time.sleep(0.18)
            print("Exo introducido.")
        except Exception as e:
            print("ERROR al introducir exo (pyautogui):", e)
    else:
        print(f"Runa detectada: {nombre_runa}. No es exo PA/PM/Al. No se hace nada.")

if __name__ == "__main__":
    introducir_exo()
