import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

time.sleep(2)

def dibujar_rectangulo():
    # Coordenadas de las columnas
    columnas_x = [1270, 1370, 1526, 1600, 2000, 2065, 2130, 2190]
    #columnas_x = [700, 750, 800, 1100, 1150, 1200, 1250]  # ~pantalla pocha
    # Coordenadas de las filas
    filas_y = [750, 820, 880, 955, 1015, 1090, 1150, 1220, 1290, 1360, 1430, 1500, 1560, 1630]
    #filas_y = [330, 370, 405, 445, 485, 525]  # pantalla pocha

    # Ajustar límites de las columnas
    columnas_x = [max(columnas_x[0], 700)] + columnas_x + [min(columnas_x[-1], 1250)]

    # Ajustar límites de las filas
    filas_y = [max(filas_y[0], 330)] + filas_y + [min(filas_y[-1], 525)]

    # Crear figura y ejes
    fig, ax = plt.subplots()

    # Recorrer los espacios de la matriz
    for i in range(len(columnas_x) - 1):
        for j in range(len(filas_y) - 1):
            x1, x2 = columnas_x[i], columnas_x[i + 1]
            y1, y2 = filas_y[j], filas_y[j + 1]

            # Dibujar rectángulo en cada celda de la matriz
            rect_celda = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=1, edgecolor='g', facecolor='none')
            ax.add_patch(rect_celda)


