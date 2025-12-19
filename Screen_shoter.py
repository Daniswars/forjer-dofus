import pygetwindow as gw
import pyautogui
import matplotlib.pyplot as plt
import Rectangle_drawer

def capturar_ventana(nombre_ventana):
    ventana_juego = gw.getWindowsWithTitle(nombre_ventana)[0]
    ventana_x, ventana_y, ventana_ancho, ventana_alto = ventana_juego.left, ventana_juego.top, ventana_juego.width, ventana_juego.height
    captura_ventana = pyautogui.screenshot(region=(ventana_x, ventana_y, ventana_ancho, ventana_alto))

    return captura_ventana

Rectangle_drawer.dibujar_rectangulo()
plt.imshow(capturar_ventana("tyma"))
plt.show()