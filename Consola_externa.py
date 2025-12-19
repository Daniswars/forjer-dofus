import tkinter as tk

def mostrar_resultados(resultados):
    ventana = tk.Tk()
    ventana.title("Resultados")

    # Crear un widget de texto para mostrar los resultados
    text_widget = tk.Text(ventana)
    text_widget.pack()

    # Insertar los resultados en el widget de texto
    for resultado in resultados:
        text_widget.insert(tk.END, f"{resultado}\n")

    ventana.mainloop()