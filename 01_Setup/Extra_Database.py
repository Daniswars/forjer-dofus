import openpyxl
from datetime import datetime
import tkinter as tk
from tkinter import ttk, simpledialog


def agregar_datos(objeto_seleccionado, intentos, kamas_iniciales, kamas_finales, exito,
                  tiempo_medio_intento=None, modo_encadenado_activo=False,
                  precio_objeto_base=None, precio_venta_objeto_final=None, tipo_exo=None):
    """
    Agrega datos de forjamagia a un archivo Excel, gestionando resultados de Success y fallo
    en hojas separadas. Cuando se registra un "Success", los fallos previos del mismo
    objeto en la hoja de fallos son eliminados.

    Args:
        objeto_seleccionado (str): Nombre del objeto que se está forjamagueando.
        intentos (int): Número de intentos realizados en esta sesión.
        kamas_iniciales (int): Cantidad de kamas al inicio de la sesión.
        kamas_finales (int): Cantidad de kamas al final de la sesión.
        exito (str): Resultado de la sesión ("Success" o "Fail").
        tiempo_medio_intento (float, optional): Tiempo medio por intento en segundos. Por defecto, None.
        modo_encadenado_activo (bool): True si se están realizando múltiples exos encadenados (2 o más). Por defecto, False.
        precio_objeto_base (int, optional): Precio del objeto cuando fue comprado/crafteado. Requiere para "Success" si no es modo encadenado.
        precio_venta_objeto_final (int, optional): Precio de venta del objeto exomagueado. Requiere para "Success" si no es modo encadenado.
        tipo_exo (str, optional): Tipo de exo ("PA", "PM", "AL", "NINGUNO"). Requiere para "Success" si no es modo encadenado.
    """

    # --- Configuración ---
    # Archivo pedido por el usuario
    ruta_archivo_excel = r"C:\Users\danis\OneDrive\Desktop\Forjamagia\20260213_Dofus3_Mage_Database.xlsx"

    nombre_hoja_fallos = "Fallos Forjamagia"
    nombre_hoja_exitos = "Exitos Forjamagia"

    COLUMNAS_FALLOS = {
        "Fecha": 1,
        "Objeto": 2,
        "Intentos": 3,
        "Kamas Iniciales": 4,  # Kamas al inicio de esa sesión de fallo
        "Kamas Finales": 5,  # Kamas al final de esa sesión de fallo
        "Inversion": 6,  # (Kamas Iniciales - Kamas Finales) de esa sesión
        "Tiempo Medio por Intento (s)": 7,
        "Kamas por Intento": 8,
        "Resultado": 9
    }

    COLUMNAS_EXITOS = {
        "Fecha": 1,
        "Objeto": 2,
        "Intentos Totales": 3,
        "Kamas Iniciales (acum.)": 4,  # Kamas iniciales más bajas de toda la cadena de intentos
        "Kamas Finales": 5,  # Kamas finales del último intento (el exitoso)
        "Inversion Total": 6,  # Suma de todas las inversiones (inicial - final) de todos los intentos
        "Tiempo Medio por Intento (s)": 7,  # Promedio de tiempo por intento de toda la cadena
        "Kamas por Intento (promedio)": 8,  # Promedio de kamas gastadas por intento de toda la cadena
        "Resultado": 9,
        "Precio Objeto Base": 10,  # Precio al que compraste/crafteaste el objeto (antes de empezar magueo)
        "Precio Venta Objeto Final": 11,  # Precio al que vendes el objeto ya exomagueado
        "Tipo Exo": 12,
        "Gasto en 80 intentos": 13,
        "Rentabilidad Kamas/hora": 14
    }

    # --- Pre-procesamiento de datos ---
    print(f"\n--- Inicia agregar_datos para '{objeto_seleccionado}', Exito: '{exito}' ---")
    print(f"DEBUG_INPUT: Intentos: {intentos}, Kamas Iniciales: {kamas_iniciales}, Kamas Finales: {kamas_finales}")
    print(f"DEBUG_INPUT: Tiempo Medio Intento: {tiempo_medio_intento}, Modo Encadenado: {modo_encadenado_activo}")

    try:
        # Ensure these are integers from the start, as they are direct inputs
        intentos = int(intentos)
        kamas_iniciales = int(kamas_iniciales)
        kamas_finales = int(kamas_finales)
    except (ValueError, TypeError) as e:  # Added TypeError in case None is passed unexpectedly
        print(
            f"ERROR: Los valores de 'intentos', 'kamas_iniciales' o 'kamas_finales' no son números válidos. Detalles: {e}")
        return

    # --- Cargar o crear el archivo y las hojas de Excel ---
    try:
        libro_excel = openpyxl.load_workbook(ruta_archivo_excel)
        print(f"DEBUG_EXCEL: Archivo '{ruta_archivo_excel}' cargado exitosamente.")
    except FileNotFoundError:
        print(f"Advertencia: El archivo '{ruta_archivo_excel}' no se encontró. Creando uno nuevo.")
        libro_excel = openpyxl.Workbook()
        if "Sheet" in libro_excel.sheetnames:
            libro_excel.remove(libro_excel["Sheet"])
        print(f"DEBUG_EXCEL: Archivo '{ruta_archivo_excel}' creado.")

    # Ensure "Fallos Forjamagia" sheet exists and has headers
    if nombre_hoja_fallos not in libro_excel.sheetnames:
        hoja_fallos = libro_excel.create_sheet(nombre_hoja_fallos)
        for col_name, col_idx in COLUMNAS_FALLOS.items():
            hoja_fallos.cell(row=1, column=col_idx, value=col_name)
        print(f"DEBUG_EXCEL: Hoja '{nombre_hoja_fallos}' creada y cabeceras añadidas.")
    else:
        hoja_fallos = libro_excel[nombre_hoja_fallos]
        if not hoja_fallos.cell(1, COLUMNAS_FALLOS["Fecha"]).value:  # Check if header row is empty
            for col_name, col_idx in COLUMNAS_FALLOS.items():
                hoja_fallos.cell(row=1, column=col_idx, value=col_name)
            print(f"DEBUG_EXCEL: Cabeceras añadidas a la hoja existente '{nombre_hoja_fallos}'.")
        else:
            print(f"DEBUG_EXCEL: Hoja '{nombre_hoja_fallos}' ya existe con cabeceras.")

    # Ensure "Exitos Forjamagia" sheet exists and has headers
    if nombre_hoja_exitos not in libro_excel.sheetnames:
        hoja_exitos = libro_excel.create_sheet(nombre_hoja_exitos)
        for col_name, col_idx in COLUMNAS_EXITOS.items():
            hoja_exitos.cell(row=1, column=col_idx, value=col_name)
        print(f"DEBUG_EXCEL: Hoja '{nombre_hoja_exitos}' creada y cabeceras añadidas.")
    else:
        hoja_exitos = libro_excel[nombre_hoja_exitos]
        if not hoja_exitos.cell(1, COLUMNAS_EXITOS["Fecha"]).value:  # Check if header row is empty
            for col_name, col_idx in COLUMNAS_EXITOS.items():
                hoja_exitos.cell(row=1, column=col_idx, value=col_name)
            print(f"DEBUG_EXCEL: Cabeceras añadidas a la hoja existente '{nombre_hoja_exitos}'.")
        else:
            print(f"DEBUG_EXCEL: Hoja '{nombre_hoja_exitos}' ya existe con cabeceras.")

    # --- Variables comunes para la sesión actual ---
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    # Inversion for this specific session: (Kamas_iniciales - Kamas_finales)
    # A positive value means spending, a negative value means gaining.
    inversion_actual_sesion = kamas_iniciales - kamas_finales
    kamas_por_intento_actual_sesion = inversion_actual_sesion / intentos if intentos > 0 else 0
    tiempo_por_intento_actual_sesion = tiempo_medio_intento if tiempo_medio_intento is not None else 0.0  # Ensure float

    print(f"DEBUG_CALC: Inversion de la sesión actual: {inversion_actual_sesion}")
    print(f"DEBUG_CALC: Kamas por intento de la sesión actual: {kamas_por_intento_actual_sesion:.2f}")
    print(f"DEBUG_CALC: Tiempo por intento de la sesión actual: {tiempo_por_intento_actual_sesion:.2f}")

    # --- Lógica de inserción/actualización ---
    if exito == "Fail":
        print(f"DEBUG_FLOW: Resultado es 'Fail'. Añadiendo a la hoja '{nombre_hoja_fallos}'.")
        fila_destino = hoja_fallos.max_row + 1

        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Fecha"], value=fecha_hoy)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Objeto"], value=objeto_seleccionado)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Intentos"], value=intentos)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Kamas Iniciales"], value=kamas_iniciales)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Kamas Finales"], value=kamas_finales)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Inversion"], value=inversion_actual_sesion)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Tiempo Medio por Intento (s)"],
                         value=tiempo_por_intento_actual_sesion)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Kamas por Intento"],
                         value=kamas_por_intento_actual_sesion)
        hoja_fallos.cell(row=fila_destino, column=COLUMNAS_FALLOS["Resultado"], value=exito)
        print(f"DEBUG_FLOW: Registro de fallo para '{objeto_seleccionado}' agregado a '{nombre_hoja_fallos}'.")

    elif exito == "Success":
        print(f"DEBUG_FLOW: Resultado es 'Success'. Procesando para la hoja '{nombre_hoja_exitos}'.")

        # Handle inputs for Success based on modo_encadenado_activo
        if modo_encadenado_activo:
            print(
                "DEBUG_INPUT_SUCCESS: Modo encadenado activo: Se omiten las preguntas de precio del objeto y tipo de exo.")
            precio_objeto_base = precio_objeto_base if precio_objeto_base is not None else 0
            precio_venta_objeto_final = precio_venta_objeto_final if precio_venta_objeto_final is not None else 0
            tipo_exo = tipo_exo if tipo_exo is not None else "N/A (Encadenado)"
            print(
                f"DEBUG_INPUT_SUCCESS: Valores asignados (Encadenado): Precio Base: {precio_objeto_base}, Precio Venta: {precio_venta_objeto_final}, Tipo Exo: {tipo_exo}")
        else:  # Not in chained mode, so ask if values are missing
            if precio_objeto_base is None or precio_venta_objeto_final is None or tipo_exo is None:
                print(
                    "DEBUG_INPUT_SUCCESS: Faltan datos para el registro de Success (no encadenado). Abriendo pop-ups...")
                root_tk = tk.Tk()
                root_tk.withdraw()  # Hide the main window

                # Use simpledialog for quick input
                temp_precio_base = simpledialog.askinteger("Input Necesario", "Precio Objeto Base:", parent=root_tk)
                temp_precio_venta = simpledialog.askinteger("Input Necesario", "Precio Venta Objeto Final:",
                                                            parent=root_tk)
                temp_tipo_exo = simpledialog.askstring("Input Necesario",
                                                       "Tipo de Exo (PA, PM, AL, NINGUNO, u otro):", parent=root_tk)

                root_tk.destroy()  # Destroy the hidden window

                if temp_precio_base is None or temp_precio_venta is None or temp_tipo_exo is None:
                    print("ERROR: Datos incompletos para el registro de 'Success'. Operación cancelada.")
                    return

                precio_objeto_base = temp_precio_base
                precio_venta_objeto_final = temp_precio_venta
                tipo_exo = temp_tipo_exo
                print(
                    f"DEBUG_INPUT_SUCCESS: (Usuario) Precio Base: {precio_objeto_base}, Precio Venta: {precio_venta_objeto_final}, Tipo Exo: {temp_tipo_exo}")
            else:
                print(
                    f"DEBUG_INPUT_SUCCESS: Todos los datos para Success (no encadenado) ya proporcionados: Precio Base: {precio_objeto_base}, Precio Venta: {precio_venta_objeto_final}, Tipo Exo: {tipo_exo}")

        # Initialize cumulative values with the current session's data
        total_intentos_acumulados = intentos
        total_tiempo_acumulado = tiempo_por_intento_actual_sesion * intentos
        inversion_acumulada = inversion_actual_sesion
        kamas_iniciales_acumuladas_para_exo = kamas_iniciales  # This will track the *earliest* initial kamas for the chain

        print(f"\n--- DEBUG_ACUMULACIÓN: Inicia cálculo acumulativo para '{objeto_seleccionado}' ---")
        print(f"DEBUG_ACUM: Valores iniciales de la sesión de éxito:")
        print(f"DEBUG_ACUM:   Intentos: {total_intentos_acumulados}")
        print(f"DEBUG_ACUM:   Inversion: {inversion_acumulada}")
        print(f"DEBUG_ACUM:   Kamas Iniciales acumuladas (base): {kamas_iniciales_acumuladas_para_exo}")
        print(f"DEBUG_ACUM:   Tiempo acumulado: {total_tiempo_acumulado:.2f}")

        # Iterate in reverse to avoid issues when deleting rows
        for fila_num in range(hoja_fallos.max_row, 1, -1):  # Start from max_row down to 2 (after headers)
            # Ensure the row has enough cells to avoid IndexError
            if hoja_fallos.cell(row=fila_num, column=COLUMNAS_FALLOS["Objeto"]).value == objeto_seleccionado and \
                    hoja_fallos.cell(row=fila_num, column=COLUMNAS_FALLOS["Resultado"]).value == "Fail":

                print(f"DEBUG_ACUM: Encontrado fallo previo para '{objeto_seleccionado}' en fila {fila_num}.")

                # Read values from the fail row and convert them safely
                current_fail_attempts_val = hoja_fallos.cell(row=fila_num, column=COLUMNAS_FALLOS["Intentos"]).value
                inversion_fail_val = hoja_fallos.cell(row=fila_num, column=COLUMNAS_FALLOS["Inversion"]).value
                tiempo_medio_intento_fail_val = hoja_fallos.cell(row=fila_num, column=COLUMNAS_FALLOS[
                    "Tiempo Medio por Intento (s)"]).value
                kamas_iniciales_fail_val = hoja_fallos.cell(row=fila_num,
                                                            column=COLUMNAS_FALLOS["Kamas Iniciales"]).value
                kamas_finales_fail_val = hoja_fallos.cell(row=fila_num,
                                                          column=COLUMNAS_FALLOS["Kamas Finales"]).value

                print(
                    f"DEBUG_ACUM_READ: Fila {fila_num} -> Intentos: '{current_fail_attempts_val}', Inversion: '{inversion_fail_val}', Tiempo Medio: '{tiempo_medio_intento_fail_val}', Kamas Iniciales: '{kamas_iniciales_fail_val}'")

                # Acumular intentos
                if current_fail_attempts_val is not None:
                    try:
                        val_intentos = int(current_fail_attempts_val)
                        total_intentos_acumulados += val_intentos
                        print(
                            f"DEBUG_ACUM: Sumando intentos de fallo: {val_intentos}. Total intentos acumulados: {total_intentos_acumulados}")
                    except (ValueError, TypeError):
                        print(
                            f"Advertencia: 'Intentos' '{current_fail_attempts_val}' en fila {fila_num} de fallos no es numérico. Ignorado en acumulación.")

                # Acumular inversión
                if inversion_fail_val is not None:
                    try:
                        val_inversion = float(inversion_fail_val)  # Use float for investment as it can be negative
                        inversion_acumulada += val_inversion
                        print(
                            f"DEBUG_ACUM: Sumando inversión de fallo: {val_inversion:.2f}. Total inversión acumulada: {inversion_acumulada:.2f}")
                    except (ValueError, TypeError):
                        print(
                            f"Advertencia: 'Inversion' '{inversion_fail_val}' en fila {fila_num} de fallos no es numérico. Ignorado en acumulación.")

                # Acumular tiempo (usando intentos del registro de fallo)
                if tiempo_medio_intento_fail_val is not None and current_fail_attempts_val is not None:
                    try:
                        val_tiempo_medio = float(tiempo_medio_intento_fail_val)
                        val_intentos_para_tiempo = int(current_fail_attempts_val)
                        total_tiempo_acumulado += (val_tiempo_medio * val_intentos_para_tiempo)
                        print(
                            f"DEBUG_ACUM: Sumando tiempo de fallo: {val_tiempo_medio * val_intentos_para_tiempo:.2f} (de {val_intentos_para_tiempo} intentos a {val_tiempo_medio:.2f} s/int). Total tiempo acumulado: {total_tiempo_acumulado:.2f}")
                    except (ValueError, TypeError):
                        print(
                            f"Advertencia: 'Tiempo Medio por Intento' o 'Intentos' en fila {fila_num} de fallos no es numérico para cálculo de tiempo. Ignorado.")

                # Actualizar las kamas iniciales más tempranas de toda la cadena
                if kamas_iniciales_fail_val is not None:
                    try:
                        val_kamas_iniciales_fail = int(kamas_iniciales_fail_val)
                        kamas_iniciales_acumuladas_para_exo = min(kamas_iniciales_acumuladas_para_exo,
                                                                  val_kamas_iniciales_fail)
                        print(
                            f"DEBUG_ACUM: Kamas Iniciales de fallo: {val_kamas_iniciales_fail}. Kamas Iniciales acumuladas (mínimo): {kamas_iniciales_acumuladas_para_exo}")
                    except (ValueError, TypeError):
                        print(
                            f"Advertencia: 'Kamas Iniciales' '{kamas_iniciales_fail_val}' en fila {fila_num} de fallos no es numérico. Ignorado en acumulación.")

                # Delete the fail row
                hoja_fallos.delete_rows(fila_num)
                print(f"DEBUG_LIMPIEZA: Fila {fila_num} eliminada de '{nombre_hoja_fallos}'.")
                print(
                    f"DEBUG_ACUM: Estado acumulado después de procesar y eliminar fila {fila_num}: Intentos={total_intentos_acumulados}, Inversion={inversion_acumulada:.2f}, KamasInicialesAcum={kamas_iniciales_acumuladas_para_exo}, TiempoAcum={total_tiempo_acumulado:.2f}")

        print(f"DEBUG_LIMPIEZA: Procesamiento de fallos para '{objeto_seleccionado}' completado.")

        # Recalculate averages after accumulating from all fails and the current success
        total_tiempo_por_intento_acumulado = total_tiempo_acumulado / total_intentos_acumulados if total_intentos_acumulados > 0 else 0
        kamas_por_intento_acumulado = inversion_acumulada / total_intentos_acumulados if total_intentos_acumulados > 0 else 0

        print(f"\n--- DEBUG RESULTADO FINAL para '{objeto_seleccionado}' (Success) ---")
        print(f"DEBUG_FINAL: Total Intentos Acumulados: {total_intentos_acumulados}")
        print(f"DEBUG_FINAL: Inversion Total Acumulada: {inversion_acumulada:.2f}")
        print(f"DEBUG_FINAL: Tiempo Medio por Intento (promedio total): {total_tiempo_por_intento_acumulado:.2f} s/int")
        print(f"DEBUG_FINAL: KAMAS POR INTENTO (PROMEDIO FINAL): {kamas_por_intento_acumulado:.2f} Kamas/int")
        print(f"DEBUG_FINAL: Kamas Iniciales más tempranas (acum.): {kamas_iniciales_acumuladas_para_exo}")

        # Add to "Exitos Forjamagia" sheet
        fila_destino = hoja_exitos.max_row + 1

        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Fecha"], value=fecha_hoy)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Objeto"], value=objeto_seleccionado)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Intentos Totales"], value=total_intentos_acumulados)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Kamas Iniciales (acum.)"],
                         value=kamas_iniciales_acumuladas_para_exo)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Kamas Finales"],
                         value=kamas_finales)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Inversion Total"], value=inversion_acumulada)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Tiempo Medio por Intento (s)"],
                         value=total_tiempo_por_intento_acumulado)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Kamas por Intento (promedio)"],
                         value=kamas_por_intento_acumulado)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Resultado"], value=exito)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Precio Objeto Base"], value=precio_objeto_base)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Precio Venta Objeto Final"],
                         value=precio_venta_objeto_final)
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Tipo Exo"], value=tipo_exo)

        # NUEVAS COLUMNAS
        gasto_80 = kamas_por_intento_acumulado * 80
        hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Gasto en 80 intentos"], value=gasto_80)
        print(f"DEBUG_FINAL: Gasto en 80 intentos (calculado): {gasto_80:.2f}")

        # --- MODIFICACIÓN CLAVE AQUÍ ---
        # Lógica para la Rentabilidad Kamas/hora: copiar de la celda superior si el objeto es el mismo.
        rentabilidad_copiada = None
        for fila_num in range(hoja_exitos.max_row - 1, 1, -1):
            objeto_en_fila_anterior = hoja_exitos.cell(row=fila_num, column=COLUMNAS_EXITOS["Objeto"]).value
            if objeto_en_fila_anterior == objeto_seleccionado:
                rentabilidad_copiada = hoja_exitos.cell(row=fila_num,
                                                        column=COLUMNAS_EXITOS["Rentabilidad Kamas/hora"]).value
                print(
                    f"DEBUG_FINAL: Objeto '{objeto_seleccionado}' encontrado en la fila superior ({fila_num}). Copiando valor de Rentabilidad: '{rentabilidad_copiada}'")
                break

        if rentabilidad_copiada is not None:
            hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Rentabilidad Kamas/hora"],
                             value=rentabilidad_copiada)
        else:
            print(
                f"DEBUG_FINAL: Primer 'Success' para el objeto '{objeto_seleccionado}'. Dejando la celda de Rentabilidad vacía para el cálculo manual.")
            # Opcional: podrías dejar la celda vacía o poner un valor por defecto.
            # Aquí la dejo vacía para indicar que no hay un valor previo para copiar.
            hoja_exitos.cell(row=fila_destino, column=COLUMNAS_EXITOS["Rentabilidad Kamas/hora"], value=None)

        print(f"DEBUG_FLOW: Registro de Success para '{objeto_seleccionado}' agregado a '{nombre_hoja_exitos}'.")

    # --- Guardar el archivo Excel ---
    try:
        libro_excel.save(ruta_archivo_excel)
        print(f"DEBUG_SAVE: Datos guardados exitosamente en '{ruta_archivo_excel}'.")
    except Exception as e:
        print(f"ERROR_SAVE: Error al guardar el archivo Excel: {e}")
        # Intento fallback: guardar con sufijo timestamp para no perder datos
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_path = ruta_archivo_excel.replace(".xlsx", f".{ts}.xlsx")
            libro_excel.save(fallback_path)
            print(f"DEBUG_SAVE: Fallback guardado en '{fallback_path}'. Revisa y renombra manualmente si es necesario.")
        except Exception as e2:
            print(f"ERROR_SAVE: Fallback también falló: {e2}")
            print("ERROR_SAVE: Asegúrate de que el archivo no esté abierto en otra aplicación (como Excel).")
    print(f"--- Finaliza agregar_datos para '{objeto_seleccionado}' ---\n")


if __name__ == "__main__":
    print("--- Iniciando pruebas manuales ---")

    # --- PRUEBA DE INTEGRACIÓN: Fail -> Success con Acumulación ---
    # Este test verifica que los registros de "Fail" se acumulan y eliminan correctamente
    # cuando un "Success" se registra para el mismo objeto.
    print("\n" + "=" * 80)
    print(">>> PRUEBA DE INTEGRACIÓN: Acumulación de Fallos y Éxito para 'Anillo de los Cielos'")
    print(">>> Se registrarán 3 fallos y luego 1 éxito. Se espera un solo registro de éxito.")
    print("=" * 80)

    # Paso 1: Añadir el primer fallo
    print("\n>>> Añadiendo primer 'Fail' para 'Anillo de los Cielos'...")
    agregar_datos(
        objeto_seleccionado="Anillo de los Cielos",
        intentos=5,
        kamas_iniciales=200000,
        kamas_finales=190000,
        exito="Fail",
        tiempo_medio_intento=10.0,
        modo_encadenado_activo=False
    )
    # Estado esperado después de este paso:
    # - Hoja 'Fallos': 1 fila para "Anillo de los Cielos" con 5 intentos y 10000 de inversión.
    # - Hoja 'Exitos': Sin cambios.

    # Paso 2: Añadir el segundo fallo
    print("\n>>> Añadiendo segundo 'Fail' para 'Anillo de los Cielos'...")
    agregar_datos(
        objeto_seleccionado="Anillo de los Cielos",
        intentos=8,
        kamas_iniciales=190000,
        kamas_finales=178000,
        exito="Fail",
        tiempo_medio_intento=11.5,
        modo_encadenado_activo=False
    )
    # Estado esperado después de este paso:
    # - Hoja 'Fallos': 2 filas para "Anillo de los Cielos" (la nueva tendrá 8 intentos y 12000 de inversión).
    # - Hoja 'Exitos': Sin cambios.

    # Paso 3: Añadir el tercer y último fallo
    print("\n>>> Añadiendo tercer 'Fail' para 'Anillo de los Cielos'...")
    agregar_datos(
        objeto_seleccionado="Anillo de los Cielos",
        intentos=3,
        kamas_iniciales=178000,
        kamas_finales=175000,
        exito="Fail",
        tiempo_medio_intento=9.0,
        modo_encadenado_activo=False
    )
    # Estado esperado después de este paso:
    # - Hoja 'Fallos': 3 filas para "Anillo de los Cielos".
    # - Hoja 'Exitos': Sin cambios.

    # Paso 4: Añadir el registro de 'Success'. Este paso debería consolidar.
    print("\n>>> Añadiendo 'Success' para 'Anillo de los Cielos'. Esto debería consolidar todo.")
    # Se simula que el usuario ha comprado el objeto base a 50.000 kamas y lo vende a 300.000.
    # No se usa modo encadenado, por lo que se pide manualmente los precios.
    # Si el objeto ya existía en la hoja de éxitos, la rentabilidad se copiaría (pero en este caso es el primer éxito).
    # Para el test, vamos a pasar los valores directamente para evitar el pop-up.
    agregar_datos(
        objeto_seleccionado="Anillo de los Cielos",
        intentos=4,  # Intentos de esta última sesión de éxito
        kamas_iniciales=175000,
        kamas_finales=165000,
        exito="Success",
        tiempo_medio_intento=10.0,
        modo_encadenado_activo=False,
        precio_objeto_base=50000,
        precio_venta_objeto_final=300000,
        tipo_exo="PA"
    )

    # --- Verificaciones del Test ---
    # Fallo 1: 5 intentos, inversión 10.000, tiempo total 50s
    # Fallo 2: 8 intentos, inversión 12.000, tiempo total 92s
    # Fallo 3: 3 intentos, inversión 3.000, tiempo total 27s
    # Éxito:   4 intentos, inversión 10.000, tiempo total 40s
    # TOTALES ESPERADOS:
    # - Intentos Totales: 5 + 8 + 3 + 4 = 20
    # - Inversión Total: 10000 + 12000 + 3000 + 10000 = 35000
    # - Kamas Iniciales (acum.): min(200000, 190000, 178000, 175000) = 175000
    # - Kamas Finales (acum.): 165000 (de la sesión de éxito)
    # - Tiempo Total: (5*10) + (8*11.5) + (3*9) + (4*10) = 50 + 92 + 27 + 40 = 209s
    # - Tiempo Medio por Intento: 209 / 20 = 10.45s
    # - Kamas por Intento (promedio): 35000 / 20 = 1750

    print("\n" + "=" * 80)
    print(">>> FIN DE LA PRUEBA DE INTEGRACIÓN")
    print(">>> Por favor, revisa tu Excel: ")
    print(">>> - La hoja 'Fallos Forjamagia' NO debe tener filas para 'Anillo de los Cielos'.")
    print(">>> - La hoja 'Exitos Forjamagia' debe tener UNA ÚNICA fila para 'Anillo de los Cielos'.")
    print(">>>   Verifica que los valores de esa fila correspondan con los totales esperados:")
    print(">>>   - 'Intentos Totales': 20")
    print(">>>   - 'Inversion Total': 35000")
    print(">>>   - 'Kamas Iniciales (acum.)': 175000 (o el valor de la primera sesión, dependiendo de tu lógica)")
    print(">>>   - 'Kamas por Intento (promedio)': 1750.0")
    print(">>>   - 'Tiempo Medio por Intento (s)': 10.45")
    print(
        ">>>   - 'Rentabilidad Kamas/hora': vacía (o calculada si ya tenías una fórmula).")  # Ajusta según tu lógica actual
    print("=" * 80)

