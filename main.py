import pyautogui
import time
import statistics
import keyboard
import maguear
import data_runner
import stats_not_full
import verificar_exito
import Correo
import get_kamas
import sin_runas_ventana
import Database
import Interfaz_magueo
import pygetwindow as gw
import pytesseract
import resetear_sesion
import Cambio_objeto
import Guardar_exito

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'


###########################
####### Variables #########
###########################

def detectar_ventana_dofus():
    """
    Busca y retorna el nombre de la primera ventana que contenga 'pro' en el título.
    Si no encuentra ninguna, retorna None.
    """
    ventanas = gw.getAllTitles()
    for v in ventanas:
        if 'pro' in v.lower():
            print(f"DEBUG_MAIN: Ventana Dofus detectada: {v}")
            return v
    print("Advertencia: No se encontró ninguna ventana de Dofus con 'pro' en el título.")
    return None


nombre_ventana = detectar_ventana_dofus()

intentos = 0
tiempo_medio_intento = []
tiempo_bug_inicio = time.time()
historial_valores = [None] * 8  # Initialize historial_valores with None to detect when it's fully populated
pause = False
finalizarPrograma = False

# --- Nuevas variables para el reseteo de sesión ---
TIEMPO_MAXIMO_MAGUEO_MINUTOS = 40
FORMAMAGIA_IMPOSIBLE_TOP_LEFT = (1792, 1050)
FORMAMAGIA_IMPOSIBLE_BOTTOM_RIGHT = (2042, 1084)
tiempo_inicio_magueo_sesion = time.time()  # Variable para controlar el inicio del tiempo de magueo de la sesión actual

# --- Nueva variable para la cantidad de exos deseados ---
cantidad_exos_deseados = 1  # Default to 1, will be overwritten by user input

# --- Nueva variable para indicar si el modo encadenado está activo ---
modo_encadenado_activo = False


def ajustar_columnas(columnas_x, offset):
    """Ajusta las posiciones de las columnas sumando un valor offset."""
    return [x + offset for x in columnas_x]


def read_text_from_screen(top_left: tuple, bottom_right: tuple, lang='eng', config='--psm 6') -> str:
    """
    Captura una región de la pantalla y extrae texto usando Tesseract.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    width = x2 - x1
    height = y2 - y1

    if width <= 0 or height <= 0:
        print(f"Advertencia: Región de captura inválida (ancho={width}, alto={height}). Retornando cadena vacía.")
        return ""

    try:
        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        text = pytesseract.image_to_string(screenshot, lang=lang, config=config).strip()
        # print(f"OCR leyó texto en la región {top_left} a {bottom_right}: '{text}'") # Descomentar para depurar
        return text
    except Exception as e:
        print(f"Error durante OCR: {e}")
        return ""


def detectar_formamagia_imposible():
    """
    Detecta si aparece el mensaje 'formamagia imposible' o 'el objeto seleccionado no está disponible en la cantidad solicitada'.
    """
    print("DEBUG_MAIN: Comprobando mensaje 'formamagia imposible' o de cantidad no disponible...")
    texto_detectado = read_text_from_screen(FORMAMAGIA_IMPOSIBLE_TOP_LEFT, FORMAMAGIA_IMPOSIBLE_BOTTOM_RIGHT)
    if "formamagia imposible" in texto_detectado.lower():
        print("DEBUG_MAIN: ¡Mensaje 'formamagia imposible' detectado!")
        return True
    texto_cantidad = read_text_from_screen((1439, 1042),
                                           (2398, 1093))  # Nueva región para el mensaje de cantidad no disponible
    if "disponible" in texto_cantidad.lower():
        print("DEBUG_MAIN: ¡Mensaje de cantidad no disponible detectado!")
        return True
    return False


def toggle_pause():
    """Pausa o reanuda la ejecución del script."""
    global pause
    pause = not pause
    print("Programa", "Pausado" if pause else "Reanudado")


def finalizar():
    """Finaliza el programa y guarda datos en la base."""
    global finalizarPrograma, objeto_seleccionado, intentos, kamas_iniciales, tiempo_medio_intento, modo_encadenado_activo
    print("DEBUG_MAIN: Hotkey F10 presionada. Iniciando finalización forzada del programa.")
    Correo.send_mail(objeto_seleccionado, "Finalizar forzado")
    current_kamas_at_exit = get_kamas.get_kamas()  # Make sure kamas_finales is updated before logging on forced exit
    # Pass modo_encadenado_activo to Database.agregar_datos
    Database.agregar_datos(objeto_seleccionado, intentos, kamas_iniciales, current_kamas_at_exit, "Fail",
                           statistics.mean(tiempo_medio_intento) if tiempo_medio_intento else 0, modo_encadenado_activo)
    finalizarPrograma = True


keyboard.add_hotkey('F9', toggle_pause)
keyboard.add_hotkey('F10', finalizar)

# --- Recibir la variable `cantidad_exos_deseados` de Interfaz_magueo ---
objeto_seleccionado, estadisticas_objeto, celdas_no_procesar, estadisticas_min, estadisticas_max, cantidad_exos_deseados = \
    Interfaz_magueo.recoger_nuevas_estadisticas_y_terminar()

modo_encadenado_activo = (cantidad_exos_deseados >= 2)
print(
    f"DEBUG_MAIN: Modo de magueo seleccionado: {cantidad_exos_deseados} exos deseados. Modo encadenado activo: {modo_encadenado_activo}")

Correo.send_mail(objeto_seleccionado, f"Inicio magueo automatizado para {cantidad_exos_deseados} exos")
kamas_iniciales = get_kamas.get_kamas()  # Get initial kamas for this session
print(f"DEBUG_MAIN: Kamas iniciales al comienzo del script: {kamas_iniciales}")

# Tus columnas X base (las que definen las divisiones verticales en tu UI de Dofus)
columnas_x = [1316, 1393, 1557, 1613, 2012, 2012, 2148]

# Tus filas Y base (las que definen las posiciones Y de cada estadística)
filas_y = [763, 822, 891, 959, 1029, 1097, 1163, 1232, 1302, 1367, 1439, 1505, 1570, 1638]

tiempo_inicio = time.time()  # Timer for individual attempt duration
exito_pa = False
exos_conseguidos = 0  # Counter for successfully maged exos

# Main loop
while not finalizarPrograma and exos_conseguidos < cantidad_exos_deseados:
    print(
        f"\n--- DEBUG_MAIN_LOOP: Iniciando iteración del bucle principal. Exo actual: {exos_conseguidos + 1}/{cantidad_exos_deseados} ---")
    print(f"DEBUG_MAIN_LOOP: Intentos en esta sesión para este exo: {intentos}")
    print(f"DEBUG_MAIN_LOOP: Kamas Iniciales de la sesión para este exo: {kamas_iniciales}")
    print(f"DEBUG_MAIN_LOOP: Historial de valores (para sin runas): {historial_valores}")

    if pause:
        print("DEBUG_MAIN_LOOP: Ejecución pausada. Presiona F9 para reanudar.")
        keyboard.wait('F9')  # Wait here until F9 is pressed
        print("DEBUG_MAIN_LOOP: Ejecución reanudada.")
        tiempo_inicio_magueo_sesion = time.time()  # Al reanudar, actualiza el tiempo de inicio de magueo para no contar el tiempo de pausa

    # --- COMPROBACIONES DE RESETEO DE SESIÓN ---
    tiempo_transcurrido_magueo = time.time() - tiempo_inicio_magueo_sesion
    reset_reason = ""

    if tiempo_transcurrido_magueo >= TIEMPO_MAXIMO_MAGUEO_MINUTOS * 60:
        reset_reason += f"Tiempo de magueo ({tiempo_transcurrido_magueo:.0f}s) excede el límite de {TIEMPO_MAXIMO_MAGUEO_MINUTOS} minutos. "
        print("DEBUG_RESET: " + reset_reason.strip())

    if detectar_formamagia_imposible():
        reset_reason += "Mensaje 'formamagia imposible' o de cantidad no disponible detectado. "
        print("DEBUG_RESET: Mensaje 'formamagia imposible' o de cantidad no disponible detectado. Reseteando sesión.")

    matriz_valores, reset_needed_from_data_runner = data_runner.obtener_valores(nombre_ventana, columnas_x, filas_y,
                                                                                celdas_no_procesar, estadisticas_min,
                                                                                objeto_seleccionado)

    if reset_needed_from_data_runner:
        reset_reason += "Reset necesario detectado desde data_runner. "
        print(
            "DEBUG_RESET: Reset necesario detectado desde data_runner. Ejecutando reseteo de sesión y saltando iteración.")

    # Si alguna de las condiciones de reseteo se cumple
    if reset_reason:
        print(f"DEBUG_RESET: Ejecutando reseteo de sesión debido a: {reset_reason.strip()}")
        Correo.send_mail(objeto_seleccionado, f"Reseteo de sesión: {reset_reason.strip()}")

        kamas_finales = get_kamas.get_kamas()  # Get current kamas before logging

        if intentos > 0:  # Only log a fail if actual attempts were made before this stall
            # Use kamas_iniciales from the start of the current *session* and kamas_finales from now.
            Database.agregar_datos(objeto_seleccionado, intentos, kamas_iniciales, kamas_finales, "Fail",
                                   statistics.mean(tiempo_medio_intento) if tiempo_medio_intento else 0,
                                   modo_encadenado_activo)
            print("DEBUG_SIN_RUNAS: Fallo registrado en Database debido a 'Sin runas/Actividad nula'.")

        resetear_sesion.restart_dofus_and_click_forge(objeto_seleccionado)

        # Resetea los contadores y el historial para la nueva sesión
        historial_valores = [None] * 8
        tiempo_inicio_magueo_sesion = time.time()  # Reinicia el temporizador de la sesión
        tiempo_inicio = time.time()  # Reinicia el temporizador del intento individual
        kamas_iniciales = get_kamas.get_kamas()  # Obtiene las kamas iniciales para la nueva sesión
        print("DEBUG_RESET: --- Reseteo de sesión de magueo completado. Reiniciando bucle. ---")
        continue  # Reinicia el bucle después del reseteo
    # --- FIN COMPROBACIONES DE RESETEO ---

    # Update historial_valores cyclically
    # Ensure historial_valores has at least one element before popping
    if historial_valores:
        historial_valores.pop(0)  # Remove the oldest entry
    historial_valores.append(matriz_valores)  # Add the new entry
    print(f"DEBUG_MAIN_LOOP: Historial de valores actualizado: {historial_valores}")

    # Check for "sin runas" condition (all 8 matrices are identical and not None)
    if None not in historial_valores and all(m == historial_valores[0] for m in historial_valores):
        print("DEBUG_SIN_RUNAS: Detectado: ¡Sin runas o actividad nula!")

        if detectar_formamagia_imposible():
            print(
                "DEBUG_SIN_RUNAS: Mensaje de formamagia imposible o cantidad no disponible detectado durante sin runas. Reseteando sesión.")
            # This reset is already handled above in the main reset checks, so we just continue
            continue

        kamas_finales = get_kamas.get_kamas()  # Get current kamas before logging
        print(f"DEBUG_SIN_RUNAS: Kamas actuales con posible fallo/sin runas: {kamas_finales}")
        Correo.send_mail(objeto_seleccionado, "Fallo: Sin runas / Actividad nula detectada.")

        if intentos > 0:  # Only log a fail if actual attempts were made before this stall
            # Use kamas_iniciales from the start of the current *session* and kamas_finales from now.
            Database.agregar_datos(objeto_seleccionado, intentos, kamas_iniciales, kamas_finales, "Fail",
                                   statistics.mean(tiempo_medio_intento) if tiempo_medio_intento else 0,
                                   modo_encadenado_activo)
            print("DEBUG_SIN_RUNAS: Fallo registrado en Database debido a 'Sin runas/Actividad nula'.")

        # Reset attempts and time for the next phase of magueo after this stall
        intentos = 0
        tiempo_medio_intento.clear()  # Clear individual attempt times
        tiempo_inicio = time.time()  # Reset timer for new attempts
        historial_valores = [None] * 8  # Reset history after the alert to re-fill

        sin_runas_ventana.mostrar_mensaje_sin_runas()  # This will pause the program until user clicks OK
        print("DEBUG_SIN_RUNAS: Mensaje 'Sin runas' mostrado y cerrado por el usuario. Continuando.")

        continue  # Skip the rest of the current loop iteration to re-evaluate after unpause

    # Asignación de estadísticas (Normal Magueo Logic)
    # Ensure current_stats_to_check is a list of integers, not a list of lists
    if isinstance(matriz_valores[0], list) and all(isinstance(x, int) for x in matriz_valores[0]):
        current_stats_to_check = matriz_valores[0]
    elif all(isinstance(x, int) for x in matriz_valores):
        current_stats_to_check = matriz_valores
    else:
        raise ValueError(f"Estructura inesperada en matriz_valores: {matriz_valores}")

    print(f"DEBUG_MAIN_LOGIC: Estadísticas actuales para verificar: {current_stats_to_check}")

    if stats_not_full.stats_not_full(current_stats_to_check, estadisticas_min):
        print("DEBUG_MAIN_LOGIC: Las estadísticas no están llenas o no cumplen el mínimo. Magueando...")
        valores_para_maguear = current_stats_to_check
        maguear.maguear(valores_para_maguear, estadisticas_min, estadisticas_objeto, estadisticas_max)
    else:
        print("DEBUG_MAIN_LOGIC: Las estadísticas cumplen el mínimo. Intentando meter PA...")
        # Lógica de "meter_pa" para PA/PM/AL
        pyautogui.moveTo(2480, 724)
        time.sleep(0.2)
        pyautogui.click(clicks=2, interval=0.1)
        time.sleep(0.5)
        pyautogui.moveTo(1722, 657)
        time.sleep(0.2)
        pyautogui.click()
        time.sleep(0.5)

        if verificar_exito.verificar_exito():
            print("DEBUG_MAIN_LOGIC: ¡La acción de PA ha tenido éxito!")
            exito_pa = True  # This flag is still used for the *current* item's PA success
            exos_conseguidos += 1  # Increment the counter for successful exos
            print(f"DEBUG_MAIN_LOGIC: ¡Exo {exos_conseguidos} de {cantidad_exos_deseados} conseguido!")

            kamas_finales = get_kamas.get_kamas()  # Get final kamas at success
            print(f"DEBUG_MAIN_LOGIC: Kamas finales al éxito: {kamas_finales}")
            print(f"DEBUG_MAIN_LOGIC: Inversión total para este exo (estimada): {kamas_iniciales - kamas_finales}")
            print(f"DEBUG_MAIN_LOGIC: Intentos totales para este exo: {intentos}")
            print(
                f"DEBUG_MAIN_LOGIC: Tiempo transcurrido para este exo (sesión actual): {time.time() - tiempo_inicio:.2f} segundos")

            # Asegúrate de que tiempo_medio_intento no esté vacío antes de calcular la media
            avg_time = statistics.mean(tiempo_medio_intento) if tiempo_medio_intento else 0
            print(f"DEBUG_MAIN_LOGIC: Tiempo medio por intento para este exo: {avg_time:.2f}")

            Database.agregar_datos(objeto_seleccionado, intentos, kamas_iniciales, kamas_finales, "Success",
                                   avg_time, modo_encadenado_activo)
            print("DEBUG_MAIN_LOGIC: Datos de éxito enviados a Database.")

            Correo.send_mail(objeto_seleccionado,
                             f"¡Éxito! Exo {exos_conseguidos} de {cantidad_exos_deseados} conseguido.")
            Guardar_exito.perform_dofus_sequence()  # Perform the Dofus sequence after a successful exo
            print("DEBUG_MAIN_LOGIC: Secuencia de guardado en Dofus ejecutada.")

            # Reset variables for the next exo, if any
            if exos_conseguidos < cantidad_exos_deseados:
                print(f"DEBUG_MAIN_LOGIC: Preparando para el siguiente exo (Exo {exos_conseguidos + 1})...")
                intentos = 0
                tiempo_medio_intento.clear()
                historial_valores = [None] * 8
                tiempo_inicio = time.time()  # Reset timer for the new exo attempt
                kamas_iniciales = get_kamas.get_kamas()  # Update initial kamas for the next exo
                exito_pa = False  # Reset success flag for the next exo
                print(f"DEBUG_MAIN_LOGIC: Variables de sesión reiniciadas para el siguiente exo.")
                print(f"DEBUG_MAIN_LOGIC: Nuevas kamas iniciales para el siguiente exo: {kamas_iniciales}")

                # Llama a resetear_sesion.restart_dofus_and_click_forge para asegurar que se está en el menú de forjamagia
                # y el objeto está seleccionado antes de intentar cambiar de objeto.
                print("DEBUG_MAIN_LOGIC: Reiniciando Dofus y clickeando forja para asegurar estado base.")
                resetear_sesion.restart_dofus_and_click_forge(objeto_seleccionado)

                if modo_encadenado_activo:
                    print(
                        f"DEBUG_MAIN_LOGIC: Modo encadenado activo. Cambiando al objeto para el exo número {exos_conseguidos + 1}...")
                    # Pasa el número de la casilla a la que debe cambiar, que es `exos_conseguidos`
                    # ya que se basa en el índice de la lista de objetos o posición de la casilla.
                    # Asumo que 0 es el primer objeto, 1 el segundo, etc.
                    # Si tu `cambio_objeto` espera el *número ordinal* del exo (1, 2, 3...)
                    # en lugar del índice (0, 1, 2...), entonces pasa `exos_conseguidos` directamente.
                    # Si espera cuántos objetos *restan* por hacer, sería `cantidad_exos_deseados - exos_conseguidos`.
                    # De acuerdo a tu comentario original, "Pasa el número de la siguiente casilla", que suele ser 1-indexed.
                    # Lo más seguro es que sea `exos_conseguidos` (el número de exo actual) si el módulo cuenta desde el primer exo.
                    # Si `cambio_objeto` maneja la selección del siguiente objeto, es posible que el parámetro
                    # deba ser `exos_conseguidos` (para seleccionar el item en la posición del *siguiente* exo)
                    # o incluso `None` si la lógica interna de `cambio_objeto` maneja la iteración.
                    # Por ahora, dejo `cantidad_exos_deseados - exos_conseguidos` como tú lo tenías.
                    Cambio_objeto.cambio_objeto(cantidad_exos_deseados - exos_conseguidos)

                    print("DEBUG_MAIN_LOGIC: Reset de historial y tiempos para el nuevo objeto encadenado.")
                    historial_valores = [None] * 8
                    tiempo_inicio_magueo_sesion = time.time()  # Reinicia el temporizador de la sesión
                    tiempo_inicio = time.time()  # Reinicia el temporizador del intento individual
                    kamas_iniciales = get_kamas.get_kamas()  # Obtiene las kamas iniciales para la nueva sesión

        else:
            print("DEBUG_MAIN_LOGIC: La acción ha sido un fallo.")
            intentos += 1
            print(f"DEBUG_MAIN_LOGIC: Intentos para este exo: {intentos}")
            if intentos % 10 == 0:
                print("DEBUG_MAIN_LOGIC: 10 intentos acumulados sin éxito. Enviando correo.")
                Correo.send_mail(objeto_seleccionado, "10 intentos acumulados sin éxito")

            current_attempt_duration = time.time() - tiempo_inicio
            tiempo_medio_intento.append(current_attempt_duration)
            tiempo_inicio = time.time()  # Reset timer for the next individual attempt
            print(
                f"DEBUG_MAIN_LOGIC: Duración del último intento: {current_attempt_duration:.2f}s. Tiempo medio por intento (acumulado): {statistics.mean(tiempo_medio_intento):.2f}s")

# Final summary after the loop ends
print("\n--- DEBUG_MAIN_SUMMARY: Bucle principal finalizado. ---")
if finalizarPrograma:
    print("DEBUG_MAIN_SUMMARY: Programa finalizado por el usuario.")
elif exos_conseguidos == cantidad_exos_deseados:
    print(f"DEBUG_MAIN_SUMMARY: ¡Objetivo alcanzado! Se han conseguido {cantidad_exos_deseados} exos exitosamente.")
    Correo.send_mail(objeto_seleccionado, f"¡Objetivo de {cantidad_exos_deseados} exos alcanzado!")