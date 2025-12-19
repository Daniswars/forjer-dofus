import pyautogui
import time


def maguear(estadisticas_actuales, estadisticas_min, estadisticas_objeto, estadisticas_max):
    print(estadisticas_min)
    # Lista de estadísticas en orden de prioridad

    runas_tochas = ["pa", "pm", "al", "inv", "da", "cri"]
    runas_re_por = ["re_agua_por", "re_aire_por", "re_tierra_por", "re_fuego_por", "re_neu_por"]
    runas_re = ["re_agua", "re_aire", "re_tierra", "re_fuego", "re_neu", "re_cri"]
    runas_vi = ["vi"]
    runas_da = ["da_agua", "da_aire", "da_tierra", "da_fuego", "da_neu", "da_cri", "da_tram", "da_emp"]
    runas_sa = ["sa"]
    runas_cu = ["cu"]
    runas_pla_hui = ["pla", "hui"]
    runas_esquivas_retiras = ["ret_pa", "ret_pm", "es_pa", "es_pm"]
    runas_basic_stats = ["fo", "inte", "agi", "sue"]
    runas_potencia = ["pot"]
    runas_ini = ["ini"]
    runas_da_20 = ["da"]
    runa_prospe = ["prospe"]  # Moved to be a list for consistency

    # --- NUEVA LISTA PARA LA RESISTENCIA DE EMPUJE ---
    runas_re_emp = ["re_emp"]

    continuar_magueando = True

    # Coordenadas fijas para columnas y filas según lo indicado por el usuario
    columnas_x = [2054, 2117, 2189]  # X de los 3 huecos de la primera fila

    # Y de la primera fila y desnivel entre filas
    fila_y_inicial = 790
    fila_desnivel = 70

    # Generar las posiciones Y para las filas (por ejemplo, hasta 14 filas, but will be limited by len(estadisticas_min))
    filas_y = [fila_y_inicial + i * fila_desnivel for i in range(14)]

    bucles_while = 0
    while continuar_magueando:
        bucles_while += 1
        # print("bucles", bucles_while) # Uncomment for debugging loop count

        # Iterate only through the number of actual stats the object has
        for i in range(len(estadisticas_actuales)):
            # Ensure we don't go out of bounds for min/max stats if lists are inconsistent (shouldn't be with Interfaz_magueo fix)
            if i >= len(estadisticas_min) or i >= len(estadisticas_max) or i >= len(estadisticas_objeto):
                print(
                    f"ADVERTENCIA: Índice {i} fuera de rango para las listas de estadísticas (min/max/objeto). Deteniendo bucle de magueo.")
                continuar_magueando = False
                break

            # --- LÓGICA REVISADA: PRIOTIZAR RE_EMP SI BAJA DE 70 Y MAX ES ALTO ---
            if estadisticas_objeto[i] in runas_re_emp: # and estadisticas_max[i] >= 70:
                if estadisticas_actuales[i] <= estadisticas_min[i]:
                    celda_y = filas_y[i]
                    celda_x = columnas_x[1]  # Usar la runa más grande para subirlo rápidamente
                    click(celda_x, celda_y)
            '''
                    if estadisticas_actuales[i] <= 40:
                        print("chivato (re_emp): ¡VALOR CRÍTICO! Ha caído por debajo de 40. Subiendo a 70+...")
                    else:
                        print("chivato (re_emp): Valor bajo, subiendo a 70+ con runa grande...")

                    click(celda_x, celda_y)
                    time.sleep(0.25)
                    click(celda_x, celda_y)
                    time.sleep(0.25)
                    click(celda_x, celda_y)
                    continuar_magueando = True  # Asegura que el bucle se repite
                    break  # Sal del bucle 'for' para volver a chequear desde el principio
                else:
                    celda_y = filas_y[i]
                    celda_x = columnas_x[2]  # Usar la runa más grande para subirlo rápidamente
                    click(celda_x, celda_y)
                    '''
            # --- FIN LÓGICA REVISADA ---

            # Logic for when current stat is significantly below min (e.g., < 30% of min)
            if estadisticas_actuales[i] < estadisticas_min[i] * 0.3 and continuar_magueando:

                # Click on the cell corresponding to the stat that needs to increase
                celda_y = filas_y[i]

                # Adjust click column depending on the stat type and its value
                if estadisticas_objeto[i] in runas_tochas:
                    celda_x = columnas_x[0]
                    click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_re_por:
                    celda_x = columnas_x[0]
                    click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_da_20:
                    celda_x = columnas_x[0]
                    click(celda_x, celda_y)

                # --- LÓGICA REVISADA: PRIOTIZAR RE_EMP SI BAJA DE 70 Y MAX ES ALTO ---
                elif estadisticas_objeto[i] in runas_re_emp:  # and estadisticas_max[i] >= 70:
                    if estadisticas_actuales[i] <= estadisticas_min[i]:
                        celda_y = filas_y[i]
                        celda_x = columnas_x[1]  # Usar la runa más grande para subirlo rápidamente
                        click(celda_x, celda_y)

                '''
                        if estadisticas_actuales[i] <= 40:
                            print("chivato (re_emp): ¡VALOR CRÍTICO! Ha caído por debajo de 40. Subiendo a 70+...")
                        else:
                            print("chivato (re_emp): Valor bajo, subiendo a 70+ con runa grande...")

                        click(celda_x, celda_y)
                        time.sleep(0.25)
                        click(celda_x, celda_y)
                        time.sleep(0.25)
                        click(celda_x, celda_y)
                        continuar_magueando = True  # Asegura que el bucle se repite
                        break  # Sal del bucle 'for' para volver a chequear desde el principio
                    else:
                        celda_y = filas_y[i]
                        celda_x = columnas_x[2]  # Usar la runa más grande para subirlo rápidamente
                        click(celda_x, celda_y)
                 '''

                if estadisticas_objeto[i] in runas_sa:
                    if estadisticas_max[i] >= 35:
                        if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                            celda_x = columnas_x[2]
                            click(celda_x, celda_y)
                        else:
                            celda_x = columnas_x[1]
                            click(celda_x, celda_y)
                    else:
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_cu:
                    celda_x = columnas_x[0]
                    click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_esquivas_retiras:
                    print("chivato (esquivas/retiras)")  # Debug print
                    if estadisticas_actuales[i] + 1 <= estadisticas_max[i]:
                        celda_x = columnas_x[0]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_pla_hui:
                    print("chivato (placaje/huida)")  # Debug print
                    if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                        celda_x = columnas_x[0]
                        click(celda_x, celda_y)
                    else:
                        celda_x = columnas_x[0]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_re:
                    print("chivato (resistencias fijas)")  # Debug print
                    if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:  # Changed from < to <=
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)
                    else:
                        celda_x = columnas_x[0]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_da:
                    print("chivato (daños elementales)")  # Debug print
                    if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)
                    elif estadisticas_max[i] >= 20:  # This condition seems redundant if +3 logic is met
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)
                    else:
                        celda_x = columnas_x[0]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_vi:
                    print("chivato (vitalidad)")  # Debug print
                    if estadisticas_max[i] == 350:
                        if (estadisticas_actuales[i] >= 286 and estadisticas_actuales[i] <= 300) or (
                                estadisticas_actuales[i] + 50 <= 300):  # Check if +50 rune is viable
                            celda_x = columnas_x[2]  # Use the +50 rune
                            click(celda_x, celda_y)
                        else:
                            celda_x = columnas_x[1]  # Use the +10 rune
                            click(celda_x, celda_y)
                    else:  # For other max vitality values
                        if estadisticas_actuales[i] + 50 <= estadisticas_max[i]:
                            celda_x = columnas_x[2]  # Use the +50 rune
                            click(celda_x, celda_y)
                        else:
                            celda_x = columnas_x[1]  # Use the +10 rune
                            click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_ini:
                    print("chivato (iniciativa)")  # Debug print
                    if estadisticas_actuales[i] + 100 <= estadisticas_max[i]:
                        celda_x = columnas_x[2]
                        click(celda_x, celda_y)
                    else:
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)

                elif estadisticas_objeto[i] in runas_basic_stats:
                    print("chivato (stats basicos)")  # Debug print
                    if estadisticas_max[i] <= 60:
                        if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                            celda_x = columnas_x[2]  # Use the +10 rune
                            click(celda_x, celda_y)
                        else:
                            celda_x = columnas_x[1]  # Use the +3 rune
                            click(celda_x, celda_y)
                    else:  # For stats with max > 60
                        if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                            celda_x = columnas_x[2]  # Use the +10 rune
                            click(celda_x, celda_y)
                        else:
                            continue  # Don't click if +10 isn't viable and we're not severely deficient

                elif estadisticas_objeto[i] in runas_potencia:
                    print("chivato (potencia)")  # Debug print
                    if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                        celda_x = columnas_x[1]
                        click(celda_x, celda_y)

                # --- NEW LOGIC FOR PROSPE ---
                elif estadisticas_objeto[i] in runa_prospe:
                    print("chivato (prospección)")  # Debug print
                    # Check if current + 3 is still within the max
                    if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                        celda_x = columnas_x[1]  # Click the +3 rune (second position)
                        click(celda_x, celda_y)
                    else:
                        # If +3 would exceed max, try the smallest rune if available and needed
                        # Assuming the smallest rune is at columnas_x[0] and gives +1 (or similar small amount)
                        # This would be an edge case if min < current < max and +3 exceeds max.
                        # You might need to refine the exact logic based on rune values.
                        celda_x = columnas_x[0]  # Try the smallest rune
                        click(celda_x, celda_y)
                # --- END NEW LOGIC ---

            # Logic for when all stats are above 30% of their min, but some are still below min
            elif continuar_magueando:
                if todas_estadisticas_al_60(estadisticas_actuales, estadisticas_min):
                    if estadisticas_actuales[i] < estadisticas_min[i]:
                        # Click on the cell corresponding to the stat that needs to increase
                        celda_y = filas_y[i]

                        if estadisticas_objeto[i] in runas_tochas:
                            celda_x = columnas_x[0]
                            click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_re_por:
                            celda_x = columnas_x[0]
                            click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_da_20:
                            celda_x = columnas_x[0]
                            click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_sa:
                            if estadisticas_max[i] >= 35:
                                if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                                    celda_x = columnas_x[2]
                                    click(celda_x, celda_y)
                                else:
                                    celda_x = columnas_x[1]
                                    click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[
                                    2]  # Changed from columnas_x[1] to [2] assuming SA can have +10 at this stage
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_cu:
                            celda_x = columnas_x[0]
                            click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_esquivas_retiras:
                            print("chivato (esquivas/retiras - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 1 <= estadisticas_max[i]:
                                celda_x = columnas_x[0]
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_pla_hui:
                            print("chivato (placaje/huida - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                                celda_x = columnas_x[0]
                                click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[0]
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_re:
                            print("chivato (resistencias fijas - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:  # Changed from < to <=
                                celda_x = columnas_x[1]
                                click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[0]
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_da:
                            print("chivato (daños elementales - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                                celda_x = columnas_x[1]
                                click(celda_x, celda_y)
                            elif estadisticas_max[i] >= 20 and estadisticas_actuales >= 12:
                                celda_x = columnas_x[1]
                                click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[0]
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_vi:
                            print("chivato (vitalidad - 60%)")  # Debug print
                            if estadisticas_max[i] == 350:
                                if (estadisticas_actuales[i] >= 286 and estadisticas_actuales[i] <= 300) or \
                                        (estadisticas_actuales[i] + 50 <= 300):
                                    celda_x = columnas_x[2]
                                    click(celda_x, celda_y)
                                else:
                                    celda_x = columnas_x[1]
                                    click(celda_x, celda_y)
                            else:
                                if estadisticas_actuales[i] + 50 <= estadisticas_max[i]:
                                    celda_x = columnas_x[2]
                                    click(celda_x, celda_y)
                                else:
                                    celda_x = columnas_x[1]
                                    click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_potencia:
                            print("chivato (potencia - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                                celda_x = columnas_x[1]
                                click(celda_x, celda_y)

                        elif estadisticas_objeto[i] in runas_basic_stats:
                            print("chivato (stats basicos - 60%)")  # Debug print
                            if estadisticas_max[i] <= 60:
                                if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                                    celda_x = columnas_x[2]
                                    click(celda_x, celda_y)
                                else:
                                    celda_x = columnas_x[1]
                                    click(celda_x, celda_y)
                            else:
                                if estadisticas_actuales[i] + 10 <= estadisticas_max[i]:
                                    celda_x = columnas_x[2]
                                    click(celda_x, celda_y)
                                else:
                                    continue
                        elif estadisticas_objeto[i] in runas_ini:
                            print("chivato (iniciativa - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 100 <= estadisticas_max[i]:
                                celda_x = columnas_x[2]
                                click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[1]
                                click(celda_x, celda_y)

                        # --- NEW LOGIC FOR PROSPE (SECOND PHASE) ---
                        elif estadisticas_objeto[i] in runa_prospe:
                            print("chivato (prospección - 60%)")  # Debug print
                            if estadisticas_actuales[i] + 3 <= estadisticas_max[i]:
                                celda_x = columnas_x[1]  # Click the +3 rune (second position)
                                click(celda_x, celda_y)
                            else:
                                celda_x = columnas_x[0]  # Try the smallest rune
                                click(celda_x, celda_y)
                        # --- END NEW LOGIC ---
        continuar_magueando = False  # Exit after one full pass if no low stats found
        break  # Exit the while loop after one full pass


def todas_estadisticas_al_60(estadisticas_actuales, estadisticas_min):
    # This function name is a bit misleading as it checks for 30% of min, not 60.
    # Consider renaming it to something like 'all_stats_above_threshold' for clarity.
    for i in range(len(estadisticas_actuales)):
        # Ensure index is within bounds for estadisticas_min
        if i >= len(estadisticas_min):
            print(f"ADVERTENCIA: Índice {i} fuera de rango para estadisticas_min en 'todas_estadisticas_al_60'.")
            return False  # Or handle as an error

        # print(f"Checking stat {i}: Actual={estadisticas_actuales[i]}, Min={estadisticas_min[i]}") # Uncomment for debug
        if estadisticas_actuales[i] < estadisticas_min[i] * 0.3:
            return False
    return True


def click(celda_x, celda_y):
    # Perform the click
    pyautogui.click(x=celda_x, y=celda_y)
    time.sleep(0.25)  # Short delay after each click
