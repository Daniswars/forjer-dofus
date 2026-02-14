import pyautogui
import time
import os


def cambio_objeto(numero_casilla_destino: int):
    """
    Clicks on the appropriate inventory slot to change the item based on the
    target slot number, navigating through Dofus menus as needed.

    Args:
        numero_casilla_destino (int): The 1-indexed number of the inventory slot to click.
                                     (e.g., 1 for the first slot, 2 for the second, etc.)
    """
    # Define las coordenadas para los botones de menú
    MENU_OBJETOS_COORD = (2345, 651)
    MENU_RECURSOS_COORD = (2349, 797)

    # Define las coordenadas para cada casilla de inventario, indexadas desde 1
    inventory_slots = {
        1: (2478, 735),
        2: (2583, 735),
        3: (2695, 735),
        4: (2794, 737),
        5: (2911, 738),
        6: (2466, 846),
        7: (2584, 835),
        8: (2680, 830),
        9: (2785, 849),
        10: (2880, 847),
        11: (2486, 936),
        12: (2584, 941),
        13: (2692, 942),
        14: (2781, 944),
        15: (2869, 936)
    }

    slot_to_click = numero_casilla_destino-1

    if slot_to_click not in inventory_slots:
        print(f"Advertencia: No hay coordenadas definidas para el objeto en la casilla número {slot_to_click}.")
        print("Asegúrate de que la lista 'inventory_slots' en 'cambio_objeto.py' esté completa si esperas más objetos.")
        return  # Sale de la función si la casilla no está definida

    x, y = inventory_slots[slot_to_click]

    print(f"Navegando a menú Objetos para cambiar al objeto en casilla {slot_to_click}...")

    # 1. Cambiar al menú de objetos
    pyautogui.moveTo(MENU_OBJETOS_COORD[0], MENU_OBJETOS_COORD[1])
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(0.5)  # Espera un poco a que cargue la interfaz de objetos

    # 2. Hacer clic en la casilla del objeto destino
    pyautogui.moveTo(x, y)
    time.sleep(0.2)
    pyautogui.click(clicks=2, interval=0.1)  # Doble clic para seleccionar el objeto
    time.sleep(0.5)

    print(f"Selección del objeto en casilla {slot_to_click} completada.")

    # 3. Volver al menú de recursos
    print("Volviendo al menú de Recursos...")
    pyautogui.moveTo(MENU_RECURSOS_COORD[0], MENU_RECURSOS_COORD[1])
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(0.5)  # Espera un poco a que cargue la interfaz de recursos

    print("Retorno al menú de Recursos completado.")


# --- Función de Prueba Real ---
def prueba_real_cambio_objeto():
    """
    Realiza una prueba interactiva de la función cambio_objeto moviendo el ratón
    y haciendo clic en las coordenadas reales de la pantalla.
    """
    print("\n--- INICIANDO PRUEBA REAL DE CAMBIO DE OBJETO ---")
    print("¡ADVERTENCIA!: Este test MOVERÁ TU RATÓN y hará clics.")
    print("Asegúrate de que Dofus esté abierto y la ventana de la forjamagia esté en la posición correcta.")
    print(
        "Puedes detener el script en cualquier momento moviendo tu ratón a una de las esquinas de la pantalla (falla segura de PyAutoGUI) o presionando CTRL+C en la consola.\n")

    input("Presiona ENTER para continuar y comenzar la prueba...")

    # Ahora test_cases son directamente los números de las casillas que quieres probar
    # Ten en cuenta que la casilla 0 no existe en tu lista, así que ajustamos la prueba
    test_cases = [1, 2, 6, 11, 15, 16]  # 16 para probar fuera de rango y la advertencia

    for i, casilla_a_probar in enumerate(test_cases):
        print(f"\n--- Prueba {i + 1}/{len(test_cases)}: Casilla a probar = {casilla_a_probar} ---")
        input(
            f"Presiona ENTER para que el script intente seleccionar el objeto en la casilla {casilla_a_probar}...")
        cambio_objeto(casilla_a_probar)  # Le pasamos directamente el número de casilla
        time.sleep(2)  # Pausa para observar el resultado antes de la siguiente prueba

    print("\n--- PRUEBA REAL FINALIZADA ---")
    print("Revisa los clics que se realizaron en tu pantalla.")


# --- Bloque principal para ejecutar tests ---
if __name__ == "__main__":
    print("--- Menú de Ejecución ---")
    print("1. Ejecutar prueba de simulación (no mueve el ratón).")
    print("2. Ejecutar prueba REAL (mueve el ratón y hace clics).")
    print("3. Introducir número de casilla para cambio de objeto manual.")

    choice = input("Ingresa tu opción (1, 2 o 3): ")

    if choice == '1':
        # Función de test original que solo imprime (adaptada a la nueva lógica de 'numero_casilla_destino')
        def test_cambio_objeto_simulacion():
            print("\n--- Iniciando TEST DE SIMULACIÓN para cambio_objeto.py ---")
            print("Este test simulará los clics, pero no moverá el ratón realmente.\n")

            # Para simular, podemos evitar los clics de PyAutoGUI temporalmente en esta función de test.
            # Sin embargo, la función `cambio_objeto` ahora tiene clics reales.
            # Para una simulación pura, necesitaríamos una versión de `cambio_objeto` que no use pyautogui,
            # o envolver `pyautogui` en un condicional. Por ahora, si eliges 1, los print se harán.
            # Si quieres que realmente no haga nada de PyAutoGUI, tendrías que modificar la función `cambio_objeto`
            # con un `if test_mode: print(...) else: pyautogui.click(...)`

            print("Simulando cambio para Casilla 1...")
            # No llamamos a la función real aquí si queremos simular sin PyAutoGUI
            # En su lugar, replicamos la lógica de impresión sin el movimiento del ratón
            x, y = (2478, 735)  # Coordenadas de la casilla 1
            print(f"Simulando clic para seleccionar el objeto en la casilla número 1 con coordenadas ({x}, {y})...")
            print(f"Simulación de selección para el objeto en casilla 1 completada.")
            print("Simulando retorno al menú de Recursos.")
            time.sleep(0.5)

            print("\nSimulando cambio para Casilla 5...")
            x, y = (2911, 738)  # Coordenadas de la casilla 5
            print(f"Simulando clic para seleccionar el objeto en la casilla número 5 con coordenadas ({x}, {y})...")
            print(f"Simulación de selección para el objeto en casilla 5 completada.")
            print("Simulando retorno al menú de Recursos.")
            time.sleep(0.5)

            print("\nSimulando cambio para Casilla 15 (última definida)...")
            x, y = (2869, 936)  # Coordenadas de la casilla 15
            print(f"Simulando clic para seleccionar el objeto en la casilla número 15 con coordenadas ({x}, {y})...")
            print(f"Simulación de selección para el objeto en casilla 15 completada.")
            print("Simulando retorno al menú de Recursos.")
            time.sleep(0.5)

            print("\nSimulando cambio para Casilla 16 (fuera de rango)...")
            print("Advertencia: No hay coordenadas definidas para el objeto en la casilla número 16.")
            print(
                "Asegúrate de que la lista 'inventory_slots' en 'cambio_objeto.py' esté completa si esperas más objetos.")
            print("Simulación de selección para el objeto en casilla 16 completada.")
            time.sleep(0.5)

            print("\n--- TEST DE SIMULACIÓN finalizado ---")


        test_cambio_objeto_simulacion()
    elif choice == '2':
        prueba_real_cambio_objeto()  # Ejecuta la prueba que mueve el ratón y los clics de menú
    elif choice == '3':
        try:
            # Aquí el usuario introduce directamente la casilla a la que quiere ir
            casilla = int(input("Introduce el NÚMERO DE CASILLA del objeto a cambiar (ej. 1, 2, 6): "))
            if casilla < 1:
                print("El número de casilla debe ser 1 o superior.")
            else:
                cambio_objeto(casilla)  # Llama a la función con clics de menú
        except ValueError:
            print("Entrada no válida. Por favor, introduce un número entero.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
    else:
        print("Opción no válida. Por favor, ejecuta el script de nuevo e ingresa 1, 2 o 3.")