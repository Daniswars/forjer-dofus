import tkinter as tk

# Función para mostrar el mensaje de "Sin runas" con el botón "Continuar"
def mostrar_mensaje_sin_runas():
    # Crea una ventana emergente
    mensaje_window = tk.Toplevel()
    mensaje_window.title("Sin Runas")

    # Crea una etiqueta con el mensaje
    mensaje_label = tk.Label(mensaje_window, text="Sin runas")
    mensaje_label.pack()

    # Función para continuar el programa al presionar el botón "Continuar"
    def continuar_programa():
        mensaje_window.destroy()  # Cierra la ventana emergente
        # Aquí puedes agregar el código que deseas ejecutar después de presionar "Continuar"

    # Crea un botón "Continuar" que llamará a la función para continuar el programa
    continuar_button = tk.Button(mensaje_window, text="Continuar", command=continuar_programa)
    continuar_button.pack()

    mensaje_window.mainloop()