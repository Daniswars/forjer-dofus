import pyautogui
import pytesseract
import re
import pygetwindow as gw
from concurrent.futures import ThreadPoolExecutor
import os
from PIL import Image, ImageEnhance
import time
import io

# --- Configuración de Depuración ---
DEBUG_SAVE_IMAGES = False  # Desactivado para máxima velocidad
DEBUG_PRINT_OCR_RESULTS = True # Nuevo: Desactívalo para reducir la salida de consola en producción

# --- NUEVO: Función para activar/desactivar guardado de capturas de celdas ---
def set_save_cell_images(activar: bool):
    global DEBUG_SAVE_IMAGES
    DEBUG_SAVE_IMAGES = activar
    print(f"Guardado de capturas de celdas {'activado' if activar else 'desactivado'}.")


_count_texto_raro_consecutivo = 0
_last_objeto_seleccionado = "Objeto Desconocido"

UMBRAL_PORCENTAJE_TEXTO_RAR_RESET = 0.5
CONTEO_DE_COMPROBACIONES_DE_TEXTO_RARO = 3

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'

CARPETA_DEBUG = "capturas_debug"
if not os.path.exists(CARPETA_DEBUG):
    os.makedirs(CARPETA_DEBUG)


def preprocesar_imagen(imagen):
    imagen = imagen.convert("L")
    enhancer = ImageEnhance.Contrast(imagen)
    imagen = enhancer.enhance(2.5)
    imagen = imagen.point(lambda p: 255 if p > 150 else 0)
    return imagen


def procesar_celda(captura_celda, i, j):
    captura_celda_procesada = preprocesar_imagen(captura_celda)

    # --- NUEVO: Guardar la imagen de la celda si está activado ---
    if DEBUG_SAVE_IMAGES:
        carpeta_celdas = 'capturas_celdas'
        if not os.path.exists(carpeta_celdas):
            os.makedirs(carpeta_celdas)
        nombre_archivo = f"celda_{i}_{j}_{int(time.time()*1000)}.png"
        ruta_archivo = os.path.join(carpeta_celdas, nombre_archivo)
        captura_celda_procesada.save(ruta_archivo)

    with io.BytesIO() as f_img:
        captura_celda_procesada.save(f_img, format='PNG')
        f_img.seek(0)
        texto_celda = pytesseract.image_to_string(
            Image.open(f_img),
            lang='eng',
            config='--psm 6 --oem 3'
        ).strip()

    if DEBUG_PRINT_OCR_RESULTS:
        print(f"Celda ({i}, {j}): Texto detectado -> '{texto_celda}'")

    texto = texto_celda.lower().replace(' ', '')
    if texto in ["ode", "0de", "0", "o", "o de", "o de", "0de", "0de", "0de", "0de"]:
        return 0
    if texto in ["lale", "lalc", "linv", "linve", "lide", "1alc", "lalce", "dale", "Lal", "Alin", "‘Lin"]:
        return 1
    if texto in ["inv", "1 0%"]:
        return 0
    if "1inv" in texto:
        return 1
    if "sal" in texto:
        return 5
    if texto in ["é", "&", "éde", "é de", "é de", "é de", "é de", "re"]:
        return 6

    match = re.match(r'^(\d+)', texto)
    if match:
        return int(match.group(1))

    match_de = re.match(r'^(\d+)[a-z]*de', texto)
    if match_de:
        return int(match_de.group(1))

    match_num = re.search(r'(\d+)', texto)
    if match_num:
        return int(match_num.group(1))

    return 0


def log_configured_workers():
    """
    Imprime el número de workers que ThreadPoolExecutor utilizará
    y lo compara con el conteo de núcleos lógicos de la CPU.
    """
    actual_cpu_count = os.cpu_count()
    configured_workers = 10
    print(f"DEBUG: El sistema tiene {actual_cpu_count} núcleos lógicos de CPU. "
          f"ThreadPoolExecutor está configurado para usar {configured_workers} workers.")


def obtener_valores(nombre_ventana, columnas_x, filas_y, celdas_no_procesar, estadisticas_min, objeto_seleccionado_para_log="Objeto desconocido"):
    global _count_texto_raro_consecutivo, _last_objeto_seleccionado

    _last_objeto_seleccionado = objeto_seleccionado_para_log

    ventana_juego = gw.getWindowsWithTitle(nombre_ventana)[0]
    ventana_x, ventana_y, ventana_ancho, ventana_alto = ventana_juego.left, ventana_juego.top, ventana_juego.width, ventana_juego.height

    # La captura de pantalla en sí misma es una operación que toma tiempo.
    captura_ventana = pyautogui.screenshot(region=(ventana_x, ventana_y, ventana_ancho, ventana_alto))

    matriz_valores = []
    current_cycle_cell_results = []

    log_configured_workers()

    # --- CAMBIO CLAVE AQUÍ ---
    # Determinar el número de filas a leer basado en la longitud de estadisticas_min
    num_filas_a_leer = len(estadisticas_min)
    if num_filas_a_leer == 0:
        print("ADVERTENCIA: estadisticas_min está vacío, no se leerán estadísticas del objeto.")
        return [], False # No hay estadísticas que leer

    print(f"DEBUG: Se procesarán {num_filas_a_leer} filas (estadísticas) para el objeto '{objeto_seleccionado_para_log}'.")
    # Asegúrate de que filas_y tenga suficientes coordenadas para las filas que quieres leer
    if num_filas_a_leer > len(filas_y) - 1:
        print(f"ERROR: No hay suficientes coordenadas de filas ('filas_y') para leer {num_filas_a_leer} estadísticas. Max filas disponibles: {len(filas_y) - 1}.")
        # Podrías optar por un reseteo aquí o simplemente retornar vacío
        return [], True
    # --- FIN DEL CAMBIO CLAVE ---


    t0 = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Se empieza desde la columna 2 (índice 2) según tu uso habitual
        # El bucle ahora solo va hasta `num_filas_a_leer` para el índice `j`
        for i in range(2, len(columnas_x) - 1): # Bucle para las columnas
            row_results_futures = []
            # Bucle para las filas, limitado por num_filas_a_leer
            for j in range(num_filas_a_leer):
                if (i, j) not in celdas_no_procesar:
                    # Asegurarse de que los índices de filas_y y columnas_x sean válidos
                    if j + 1 < len(filas_y) and i + 1 < len(columnas_x):
                        captura_celda = captura_ventana.crop((columnas_x[i], filas_y[j], columnas_x[i+1], filas_y[j+1]))
                        future = executor.submit(procesar_celda, captura_celda, i, j)
                        row_results_futures.append(future)
                        current_cycle_cell_results.append(future)
                    else:
                        # Esto no debería ocurrir si las comprobaciones previas son correctas, pero es un seguro
                        print(f"ADVERTENCIA: Índices fuera de rango para celda ({i}, {j}). Omitiendo.")
                        row_results_futures.append(executor.submit(lambda: 0))
                else:
                    row_results_futures.append(executor.submit(lambda: 0))

            # Esperar los resultados de la fila actual y añadir a la matriz
            matriz_valores.append([f.result() for f in row_results_futures])
    t1 = time.time()
    print(f"Tiempo total de procesamiento OCR de celdas: {t1-t0:.2f} segundos")

    celdas_con_texto_raro = 0
    # current_cycle_cell_results contiene los Futures, necesitamos los resultados para comprobar
    processed_results = [f.result() for f in current_cycle_cell_results]
    total_celdas_procesadas_actual = len(processed_results) # Recuento real de celdas que se intentaron procesar

    # La lógica de "texto raro" debe basarse en si procesar_celda devuelve algo "inesperado" o si una celda crucial es 0.
    # Con la actual `procesar_celda` que siempre devuelve un int, `celdas_con_texto_raro` siempre será 0.
    # Si quieres detectar "texto raro", `procesar_celda` debería devolver un tipo diferente (ej. None o una string especial)
    # cuando no puede parsear un número, y luego contar esos casos aquí.
    # Por ahora, mantendremos la estructura, pero ten en cuenta esta limitación.
    # Por ejemplo:
    # if not isinstance(result, int): celdas_con_texto_raro += 1

    if total_celdas_procesadas_actual > 0:
        porcentaje_texto_raro = celdas_con_texto_raro / total_celdas_procesadas_actual
        print(f"DEBUG: Porcentaje de celdas con texto raro: {porcentaje_texto_raro:.2f} ({celdas_con_texto_raro} de {total_celdas_procesadas_actual})")

        if porcentaje_texto_raro >= UMBRAL_PORCENTAJE_TEXTO_RAR_RESET:
            _count_texto_raro_consecutivo += 1
            print(f"ALERTA: Texto raro detectado {_count_texto_raro_consecutivo}/{CONTEO_DE_COMPROBACIONES_DE_TEXTO_RARO} veces consecutivas.")
            if _count_texto_raro_consecutivo >= CONTEO_DE_COMPROBACIONES_DE_TEXTO_RARO:
                print("Reseteo de sesión debido a texto raro detectado.")
                _count_texto_raro_consecutivo = 0
                return [], True
        else:
            _count_texto_raro_consecutivo = 0
    else:
        # Esto ocurre si num_filas_a_leer es 0 o si todas las celdas están en celdas_no_procesar
        # y no se envió ninguna al executor. Esto es un caso problemático si se esperaban stats.
        _count_texto_raro_consecutivo += 1
        print(f"ALERTA: No se detectaron celdas procesables. Consecutivas: {_count_texto_raro_consecutivo}/{CONTEO_DE_COMPROBACIONES_DE_TEXTO_RARO}.")
        if _count_texto_raro_consecutivo >= CONTEO_DE_COMPROBACIONES_DE_TEXTO_RARO:
            print("Reseteo de sesión debido a falta de celdas procesables detectadas.")
            _count_texto_raro_consecutivo = 0
            return [], True

    return matriz_valores, False


def obtener_argumentos(nombre_ventana, columnas_x, filas_y, celdas_no_procesar, estadisticas_min, objeto_seleccionado_para_log="Objeto desconocido"):
    """
    Main entry point for data_runner.
    Returns the processed matrix of values, and a boolean indicating if a reset occurred.
    """
    matriz_valores, reset_happened = obtener_valores(nombre_ventana, columnas_x, filas_y, celdas_no_procesar, estadisticas_min, objeto_seleccionado_para_log)

    if reset_happened:
        return [], True

    # La lógica de "all(row == matriz_valores[0] for row in matriz_valores)"
    # asume que matriz_valores contendrá MÚLTIPLES filas de STATS,
    # pero en tu interfaz solo hay una columna de stats (la que se lee de Dofus).
    # Si `matriz_valores` siempre es una lista 1D de floats,
    # asumimos que la matriz que obtienes de Dofus también es una sola fila/columna de stats.
    if matriz_valores:
        # Si matriz_valores es [[stat1, stat2, ...]], queremos [stat1, stat2, ...]
        return matriz_valores[0], False # Asumimos que es una sola "fila" de resultados
    return [], False

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

# --- Bloque para pruebas manuales ---
if __name__ == "__main__":
    # Ejemplo de uso (ajusta los parámetros según tu pantalla y objeto)
    nombre_ventana = detectar_ventana_dofus()
    columnas_x = [0, 100, 200, 300, 400]  # Ejemplo, pon tus valores reales
    filas_y = [0, 50, 100, 150, 200]      # Ejemplo, pon tus valores reales
    celdas_no_procesar = set()
    estadisticas_min = [1, 2, 3]          # Ejemplo, pon tus stats reales
    objeto_seleccionado_para_log = "Objeto de prueba"

    print("Probando obtención de matriz de valores...")
    matriz, _ = obtener_valores(nombre_ventana, columnas_x, filas_y, celdas_no_procesar, estadisticas_min, objeto_seleccionado_para_log)
    print("Matriz de valores obtenida:")
    print(matriz)
