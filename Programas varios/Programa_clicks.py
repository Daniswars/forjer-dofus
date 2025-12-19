
#Programa para capturar las coordenadas de los clics del ratón.
import pynput
import time

def on_click(x, y, button, pressed):
    """
    Esta función se llama cada vez que se presiona o suelta un botón del ratón.
    """
    global click_count
    if pressed:  # Solo nos interesa cuando el botón es presionado
        click_count += 1
        print(f"{click_count}: X={x}, Y={y}")

# Contador global para numerar los clics
click_count = 0

print("--- Capturador de Coordenadas de Clics ---")
print("Haz clic en cualquier parte de la pantalla para obtener las coordenadas.")
print("Presiona Ctrl+C en la consola para detener el programa.")
print("-" * 35)

# Configura el listener del ratón
# El 'with' asegura que el listener se detenga correctamente al salir
with pynput.mouse.Listener(on_click=on_click) as listener:
    try:
        listener.join() # Mantiene el programa ejecutándose hasta que el listener se detiene
    except KeyboardInterrupt:
        # Esto capturará Ctrl+C para una salida limpia
        print("\nPrograma detenido por el usuario.")

print("--- Fin del Capturador ---")

