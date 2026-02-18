import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

import numpy as np

time.sleep(0.2)

def _take_screenshot():
    """Intenta tomar una captura de pantalla y devuelve un PIL.Image (o None)."""
    if ImageGrab is not None:
        try:
            return ImageGrab.grab()
        except Exception:
            pass
    try:
        import pyautogui
        return pyautogui.screenshot()
    except Exception:
        return None

def dibujar_rectangulos(screenshot_background=True):
    # Lista de rectángulos: (x1, y1, x2, y2)
    general_x1 = 1554
    general_x2 = 1650
    rects = [
        (general_x1, 756, general_x2, 823),
        (general_x1, 823, general_x2, 891),
        (general_x1, 891, general_x2, 958),
        (general_x1, 958, general_x2, 1026),
        (general_x1, 1026, general_x2, 1097),
        (general_x1, 1097, general_x2, 1161),
        (general_x1, 1161, general_x2, 1235),
        (general_x1, 1235, general_x2, 1302),
        (general_x1, 1302, general_x2, 1367),
        (general_x1, 1367, general_x2, 1437),
        (general_x1, 1437, general_x2, 1506),
        (general_x1, 1506, general_x2, 1574),
        (general_x1, 1574, general_x2, 1644),
    ]

    fig, ax = plt.subplots(figsize=(10, 8))

    if screenshot_background:
        img = _take_screenshot()
        if img is not None:
            arr = np.array(img)
            h, w = arr.shape[:2]
            # mostrar la imagen con origen en la esquina superior izquierda y ajustar ejes
            ax.imshow(arr, origin='upper')
            ax.set_xlim(0, w)
            ax.set_ylim(h, 0)  # invertir eje Y para coordenadas de pantalla
        else:
            # Si no hay captura, ajustar ejes a las coordenadas de interés
            min_x = min(r[0] for r in rects)
            max_x = max(r[2] for r in rects)
            min_y = min(r[1] for r in rects)
            max_y = max(r[3] for r in rects)
            padding = 20
            ax.set_xlim(min_x - padding, max_x + padding)
            ax.set_ylim(max_y + padding, min_y - padding)

    # dibujar cada rectángulo y una etiqueta pequeña
    for idx, (x1, y1, x2, y2) in enumerate(rects, start=1):
        w = x2 - x1
        h = y2 - y1
        rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor='lime', facecolor='none')
        ax.add_patch(rect)
        ax.text(x1 + 6, y1 + 12, f"{idx}", color='yellow', fontsize=9, weight='bold',
                bbox=dict(facecolor='black', alpha=0.5, pad=1, edgecolor='none'))

    ax.set_aspect('equal')
    ax.set_title("Rectángulos sobre captura de pantalla")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    dibujar_rectangulos()
