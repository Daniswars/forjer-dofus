import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *

# Lista de objetos disponibles para magueo (puedes modificarla según tus necesidades)
objetos_magueo = [
    "Anillo inestable",
    "Anillo Anillo XLII",
    "Selecciona objeto",
    "Anillo de Gwen astarde",
    "Anillo kukoloide",
    "Anillo glacial",
    "Alianza de corrupción",
    "Alianza de Elya Wood",
    "Alianza de Pandamonium",
    "Alianza golosona",
    "Alianza Natomia",
    "Alianza quemaalmas",
    "Amargura de Belladona",
    "Anillo Ancestral",
    "Anillo brus",
    "Anillo Colette",
    "Anillo corrupción",
    "Anillo de allister",
    "Anillo de Grithril",
    "Anillo de lario",
    "Anillo de micholobo",
    "Anillo de styx",
    "Anillo del conde kontatras",
    "Anillo noai",
    "Anillo poseído",
    "Anillo Rtografiko",
    "Anillo vueloceronte",
    "Anillidon",
    "Brazalete melenutrof",
    "Cesto de devastador",
    "Cinturón de Grithril",
    "Crueldad de Belladona",
    "Gelanillo",
    "Anillo Ghulanillo",
    "Guantes sota afortunada",
    "Kralanillo",
    "Lanza de guerra",
    "Negruraro",
    "Ternura de Belladona",
    "Collar Lunar",
    "Escudo de kukoloide",
    "Anillo rey jugador",
    "Anillo momistianillo",
    "Anillo Brazalete fondos marinos",
    "Anillo crustico",
    "Anillo lunar",
    "Anillo de nidas",
    "Capa Ordiosera",
    "Anillo rey Stropajo",
    "Escudo ilyzaelle",
    "Anillo criocrono",
    "Anillo alianza inestable",
    "Anillo pikanillo",
    "Anillo alianza fiedad",
    "Anillo Ceano",
    "Anillo alianza levitrof",
    "Escudo Solar",
    "Anillo Codicia de Miseria",
    "Escudo Ariete de Gargandias"
]

# Variables globales para almacenar las estadísticas y las referencias a las etiquetas
estadisticas_objeto = []
estadisticas_min = []
estadisticas_max = []
estadisticas_labels_min = []
estadisticas_labels_max = []

# Variable para almacenar los resultados a devolver, ahora incluye cantidad_exos
# (objeto, stats_obj, celdas_no_procesar, min, max, cantidad_exos)
resultado_magueo = (None, [], [], [], [], 1)

# Declarar combo_objetos y entry_busqueda como globales aquí para evitar errores de ámbito
combo_objetos = None
entry_busqueda = None
root = None
frame_estadisticas = None
entry_cantidad_exos = None  # Nueva variable global para el Entry de cantidad de exos


# --- Funciones de la interfaz ---

def actualizar_lista(event):
    """
    Actualiza la lista del Combobox basada en el texto de búsqueda.
    """
    global combo_objetos, entry_busqueda
    if combo_objetos and entry_busqueda:
        texto_busqueda = entry_busqueda.get().lower()
        objetos_filtrados = [obj for obj in objetos_magueo if texto_busqueda in obj.lower()]
        combo_objetos['values'] = objetos_filtrados
        if objetos_filtrados:
            combo_objetos.current(0)


def disminuir_min(i):
    """
    Disminuye el valor mínimo de una estadística y actualiza su etiqueta.
    """
    estadisticas_min[i] -= 1
    estadisticas_labels_min[i].config(text=str(estadisticas_min[i]))


def aumentar_min(i):
    """
    Aumenta el valor mínimo de una estadística y actualiza su etiqueta.
    """
    estadisticas_min[i] += 1
    estadisticas_labels_min[i].config(text=str(estadisticas_min[i]))


def disminuir_max(i):
    """
    Disminuye el valor máximo de una estadística y actualiza su etiqueta.
    """
    estadisticas_max[i] -= 1
    estadisticas_labels_max[i].config(text=str(estadisticas_max[i]))


def aumentar_max(i):
    """
    Aumenta el valor máximo de una estadística y actualiza su etiqueta.
    """
    estadisticas_max[i] += 1
    estadisticas_labels_max[i].config(text=str(estadisticas_max[i]))


def mostrar_controles_estadisticas():
    """
    Muestra los controles de estadísticas para el objeto seleccionado en el frame.
    Limpia los controles anteriores antes de mostrar los nuevos.
    """
    for widget in frame_estadisticas.winfo_children():
        widget.destroy()

    global estadisticas_labels_min, estadisticas_labels_max
    estadisticas_labels_min = []
    estadisticas_labels_max = []

    if not estadisticas_objeto:
        ttk.Label(frame_estadisticas, text="Selecciona un objeto para ver sus estadísticas.").grid(row=0, column=0,
                                                                                                   columnspan=3, padx=5,
                                                                                                   pady=5,
                                                                                                   sticky="nsew")
        frame_estadisticas.grid_columnconfigure(0, weight=1)
        return

    frame_estadisticas.grid_columnconfigure(0, weight=1)

    for i, stat in enumerate(estadisticas_objeto):
        ttk.Label(frame_estadisticas, text=stat).grid(row=i, column=0, padx=(5, 0), pady=2, sticky="w")

        min_controls_frame = ttk.Frame(frame_estadisticas)
        min_controls_frame.grid(row=i, column=1, padx=(0, 5), pady=2, sticky="e")

        ttk.Button(min_controls_frame, text="-", command=lambda idx=i: disminuir_min(idx), width=2).pack(side=tk.LEFT,
                                                                                                         padx=1)

        label_min = ttk.Label(min_controls_frame, text=f"{estadisticas_min[i]}", width=4, anchor="center")
        label_min.pack(side=tk.LEFT, padx=1)
        estadisticas_labels_min.append(label_min)

        ttk.Button(min_controls_frame, text="+", command=lambda idx=i: aumentar_min(idx), width=2).pack(side=tk.LEFT,
                                                                                                        padx=1)

        ttk.Label(frame_estadisticas, text=" - ").grid(row=i, column=2, padx=(0, 0), pady=2)

        max_controls_frame = ttk.Frame(frame_estadisticas)
        max_controls_frame.grid(row=i, column=3, padx=(5, 5), pady=2, sticky="w")

        ttk.Button(max_controls_frame, text="-", command=lambda idx=i: disminuir_max(idx), width=2).pack(side=tk.LEFT,
                                                                                                         padx=1)

        label_max = ttk.Label(max_controls_frame, text=f"{estadisticas_max[i]}", width=4, anchor="center")
        label_max.pack(side=tk.LEFT, padx=1)
        estadisticas_labels_max.append(label_max)

        ttk.Button(max_controls_frame, text="+", command=lambda idx=i: aumentar_max(idx), width=2).pack(side=tk.LEFT,
                                                                                                        padx=1)


def cargar_estadisticas_iniciales():
    """
    Carga las estadísticas del objeto seleccionado en las variables globales
    y luego llama a mostrar_controles_estadisticas para actualizar la GUI.
    """
    objeto_seleccionado_str = combo_objetos.get()
    print(f"Objeto seleccionado: {objeto_seleccionado_str}")

    global estadisticas_objeto, estadisticas_min, estadisticas_max

    # --- FIX: Clear the lists before loading new stats ---
    estadisticas_objeto = []
    estadisticas_min = []
    estadisticas_max = []
    # --- END FIX ---

    objeto_stats = {
        "Anillo vueloceronte": {
            "min": [236, 91, 4, 16, 10],
            "max": [250, 100, 5, 20, 10],
            "obj": ["vi", "sue", "cri", "da_agua", "re_agua_por"]
        },
        "Anillo Alianza de Pandamonium": {
            "min": [236, 55, 14, 1, 8, 8, 240, 7, 6, 7, 11],
            "max": [250, 60, 20, 1, 8, 8, 300, 7, 8, 10, 15],
            "obj": ["vi", "fo", "sa", "inv", "da_neu", "da_tierra", "ini", "re_tierra_por", "hui", "es_pa", "re_emp"]
        },
        "Anillo corrupción": {
            "min": [245, 55, 16, 7, 12, 11, 10, 0, 9],
            "max": [250, 60, 20, 7, 12, 12, 10, 5, 10],
            "obj": ["vi", "fo", "sa", "cri", "da_neu", "da_tierra", "re_agua_por", "es_pa", "da_cri"]
        },
        "Anillo de allister": {
            "min": [236, 66, 28, 5, 1, 13, 0, 4, 11],
            "max": [250, 75, 45, 5, 1, 15, 15, 6, 15],
            "obj": ["vi", "agi", "sa", "cri", "inv", "da_aire", "prospe", "es_pa", "re_cri"]
        },
        "Anillo Ternura de Belladona": {
            "min": [336, 23, 28, 5, 5, 8, 0, 16, 8],
            "max": [350, 30, 30, 5, 5, 10, 10, 20, 10],
            "obj": ["vi", "sa", "pot", "re_tierra_por", "re_fuego_por", "pla", "hui", "es_pa", "re_cri"]
        },
        "Anillo Anillo XLII": {
            "min": [186, 38, 38, 20, 3, 5, 5, 7, 5, 9],
            "max": [200, 40, 40, 25, 3, 6, 6, 6, 7, 12],
            "obj": ["vi", "fo", "agi", "sa", "cri", "da_tierra", "da_aire", "re_neu_por", "pla", "re_cri"]
        },
        "Anillo Amargura de Belladona": {
            "min": [236, 40, 25, 5, 5, 7, 0, 17, 6],
            "max": [250, 45, 30, 5, 5, 10, 10, 20, 10],
            "obj": ["vi", "sa", "pot", "re_agua_por", "re_aire_por", "hui", "pla", "ret_pa", "re_cri"]
        },
        "Anillo Colette": {
            "min": [136, 45, 25, 1, 1, 0, 10, 6, 6, 6, 16],
            "max": [150, 50, 40, 1, 5, 20, 10, 10, 10, 6, 20],
            "obj": ["vi", "agi", "sa", "al", "da", "prospe", "re_agua_por", "re_neu", "re_tierra", "re_agua", "da_tram"]
        },
        "Anillo Alianza de corrupción": {
            "min": [286, 48, 16, 3, 1, 1, 7, 7, 5],
            "max": [300, 50, 30, 3, 1, 1, 7, 7, 7],
            "obj": ["vi", "fo", "sa", "cri", "al", "inv", "re_tierra_por", "re_aire_por", "ret_pm"]
        },
        "Anillo Negruraro": {
            "min": [286, 65, 4, 8, 7, 7, 0, 4, 23],
            "max": [300, 75, 4, 8, 7, 7, 0, 8, 25],
            "obj": ["vi", "agi", "cri", "da_aire", "re_tierra_por", "re_aire_por", "hui", "es_pm", "da_emp"]
        },
        "Anillo Ghulanillo": {
            "min": [236, 35, 35, 35, 23, 6, 6, 6, 6, 10, 22],
            "max": [250, 40, 40, 40, 30, 7, 7, 7, 7, 10, 25],
            "obj": ["vi", "fo", "inte", "sue", "sa", "da_neu", "da_tierra", "da_fuego", "da_agua", "re_tierra_por",
                    "re_cri"]
        },
        "Anillo Alianza Natomia": {
            "min": [336, 66, 21, 1, 13, 11, 6],
            "max": [350, 75, 40, 1, 15, 15, 8],
            "obj": ["vi", "inte", "sa", "al", "da_fuego", "pla", "ret_pm"]
        },
        "Anillo brus": {
            "min": [286, 65, 16, 1, 13, 13, 10, 3, 4],
            "max": [300, 71, 30, 1, 15, 15, 10, 5, 7],
            "obj": ["vi", "fo", "sa", "al", "da_neu", "da_tierra", "re_fuego_por", "hui", "es_pm"]
        },
        "Anillo Rtografiko": {
            "min": [286, 55, 55, 55, 3, 1, 7, 7, 7, 3, 3, 3, 4, 7],
            "max": [300, 60, 60, 60, 3, 1, 9, 9, 9, 3, 3, 3, 6, 7],
            "obj": ["vi", "inte", "sue", "agi", "cri", "al", "da_fuego", "da_agua", "da_aire", "re_fuego_por",
                    "re_agua_por", "re_aire_por", "hui"]
        },
        "Anillo Guantes sota afortunada": {
            "min": [286, 55, 25, 1, 13, 0, 10, 4, 12],
            "max": [300, 60, 40, 1, 15, 12, 10, 6, 15],
            "obj": ["vi", "agi", "sa", "al", "da_aire", "prospe", "re_tierra_por", "es_pm", "re_emp"]
        },
        "Anillo poseído": {
            "min": [236, 55, 55, 2, 1, 7, 7, 7, 7, 7, 6],
            "max": [250, 60, 60, 2, 1, 7, 7, 7, 7, 7, 6],
            "obj": ["vi", "fo", "agi", "cri", "al", "da_neu", "da_tierra", "da_aire", "re_neu_por", "re_aire_por",
                    "ret_pm"]
        },
        "Anillo noai": {
            "min": [86, 55, 55, 21, 6, 1, 1, 6, 6, 8, 3, 3, 11],
            "max": [100, 60, 60, 40, 6, 1, 1, 6, 6, 8, 10, 10, 11],
            "obj": ["vi", "inte", "agi", "sa", "cri", "al", "inv", "da_fuego", "da_aire", "re_agua_por", "re_tierra",
                    "re_aire", "da_cri"]
        },
        "Anillo Crueldad de Belladona": {
            "min": [286, 21, 55, 8, 8, 8, 9, 450, 10, 0, 0, 8],
            "max": [300, 30, 60, 10, 10, 10, 10, 500, 10, 0, 0, 10],
            "obj": ["vi", "sa", "pot", "da_tierra", "da_fuego", "da_agua", "da_aire", "ini", "re_neu_por", "pla", "hui",
                    "re_cri"]
        },
        "Anillo Brazalete melenutrof": {
            "min": [286, 45, 4, 2, 8, 8, 8, 10],
            "max": [300, 50, 4, 2, 10, 10, 10, 10],
            "obj": ["vi", "pot", "cri", "al", "da_neu", "da_tierra", "da_agua", "re_neu_por"]
        },
        "Anillo Alianza quemaalmas": {
            "min": [286, 55, 55, 53, 16, 6, 6, 6, 6, 7, 7],
            "max": [300, 60, 60, 55, 30, 6, 6, 6, 6, 7, 7],
            "obj": ["vi", "fo", "inte", "agi", "sa", "da_neu", "da_tierra", "da_fuego", "da_aire", "re_agua_por",
                    "re_aire_por"]
        },
        "Anillo Lanza de guerra": {
            "min": [336, 55, 14, 3, 8, 0, 7, 7, 13],
            "max": [350, 60, 30, 3, 8, 0, 7, 7, 13],
            "obj": ["vi", "inte", "sa", "cri", "da_fuego", "cu", "re_tierra_por", "re_aire_por", "da_cri"]
        },
        "Anillo de styx": {
            "min": [186, 58, 30, 3, 9, 280, 10, 0, 8],
            "max": [200, 60, 40, 3, 10, 350, 10, 0, 15],
            "obj": ["vi", "sue", "sa", "cri", "da_agua", "ini", "re_agua_por", "re_fuego_por", "re_agua"]
        },
        "Anillo Alianza golosona": {
            "min": [236, 55, 55, 30, 1, 11, 11, 0, 330, 7, 7, 7, 4],
            "max": [250, 60, 60, 40, 1, 12, 12, 10, 400, 7, 7, 7, 5],
            "obj": ["vi", "sue", "agi", "sa", "al", "da_agua", "da_aire", "prospe", "ini", "re_neu_por",
                    "re_tierra_por", "re_fuego_por", "pla"]
        },
        "Anillo Gelanillo": {
            "min": [0],
            "max": [1],
            "obj": ["pa"]
        },
        "Anillo de Grithril": {
            "min": [236, 46, 46, 22, 3, 7, 7, 7, 10, 5, 11],
            "max": [250, 50, 50, 40, 3, 8, 8, 8, 10, 7, 15],
            "obj": ["vi", "fo", "sue", "sa", "cri", "da_neu", "da_tierra", "da_agua", "re_agua_por", "pla", "re_cri"]
        },
        "Anillo Alianza de Elya Wood": {
            "min": [86, 32, 4, 0, 10, 10, 10, 10],
            "max": [100, 35, 6, 0, 10, 10, 12, 12],
            "obj": ["vi", "inte", "cu", "prospe", "re_tierra_por", "re_fuego_por", "re_tierra", "re_fuego"]
        },
        "Anillo Cesto de devastador": {
            "min": [240, 55, 55, 2, 7, 9, 7, 7, 6, 9],
            "max": [255, 60, 60, 2, 7, 9, 7, 7, 8, 9],
            "obj": ["vi", "sue", "agi", "cri", "da_agua", "da_aire", "re_fuego_por", "re_aire_por", "es_pm", "da_emp"]
        },
        "Anillo del conde kontatras": {
            "min": [336, 45, 29, 7, 13, 13, 17, 0],
            "max": [350, 50, 45, 7, 13, 13, 25, 0],
            "obj": ["vi", "fo", "sa", "cri", "da_neu", "da_tierra", "re_cri", "ini"]
        },
        "Anillo de lario": {
            "min": [136, 35, 25, 21, 3, 6, 6, 6, 0, 150, 2, 8],
            "max": [150, 40, 30, 30, 3, 7, 7, 7, 0, 200, 3, 12],
            "obj": ["vi", "fo", "agi", "sa", "cri", "da_neu", "da_tierra", "da_aire", "prospe", "ini", "pla", "re_cri"]
        },
        "Anillo Anillidon": {
            "min": [236, 55, 21, 2, 1, 8, 8, 4, 4, 12],
            "max": [250, 60, 30, 2, 1, 10, 10, 5, 5, 15],
            "obj": ["vi", "fo", "sa", "cri", "inv", "da_neu", "da_tierra", "da_aire", "hui", "es_pa", "re_cri"]
        },
        "Anillo Ancestral": {
            "min": [116, 28, 38, 21, 0, 6, 6],
            "max": [130, 30, 40, 35, 0, 6, 6],
            "obj": ["vi", "fo", "sue", "sa", "prospe", "re_tierra_por", "re_agua_por"]
        },
        "Anillo Kralanillo": {
            "min": [186, 46, 46, 34, 3, 1, 4, 8, 0, 10, 6],
            "max": [200, 50, 50, 50, 3, 1, 6, 10, 0, 10, 10],
            "obj": ["vi", "inte", "agi", "sa", "cri", "al", "da", "cu", "prospe", "re_neu_por", "re_neu"]
        },
        "Anillo de micholobo": {
            "min": [186, 35, 35, 16, 1, 8, 8, 8, 4, 8],
            "max": [200, 40, 40, 25, 1, 8, 8, 8, 4, 8],
            "obj": ["vi", "fo", "sue", "sa", "inv", "da_neu", "da_tierra", "da_agua", "ret_pm", "da_cri"]
        },
        "Cinturón de Grithril": {
            "min": [386, 55, 55, 30, 4, 12, 12, 3, 15, 5, 25],
            "max": [451, 60, 60, 40, 4, 12, 12, 12, 15, 7, 25],
            "obj": ["vi", "fo", "sue", "sa", "cri", "da_neu", "da_tierra", "da_agua", "re_aire_por", "pla", "re_cri"]
        },
        "Collar Lunar": {
            "min": [285, 35, 65, 1, 18, 18, 0, 180, 9, 10],
            "max": [300, 40, 70, 1, 18, 18, 0, 250, 10, 10],
            "obj": ["vi", "sa", "pot", "pa", "da_neu", "da_aire", "prospe", "ini", "hui", "ret_pm"]
        },
        "Anillo glacial": {
            "min": [236, 55, 25, 4, 13, 7, 4, 16],
            "max": [250, 60, 40, 4, 15, 15, 8, 20],
            "obj": ["vi", "sue", "sa", "cri", "da_agua", "prospe", "hui", "re_cri"]
        },
        "Anillo kukoloide": {
            "min": [286, 38, 38, 38, 9, 9, 9, 9, 201, 8, 3],
            "max": [300, 40, 40, 40, 9, 9, 9, 9, 300, 8, 6],
            "obj": ["vi", "fo", "inte", "agi", "da_neu", "da_tierra", "da_fuego", "da_agua", "ini", "re_agua_por", "pla"]
        },
        "Escudo de kukoloide": {
            "min": [236, 55, 55, 55, 21, 6, 8, 6, 4, 4],
            "max": [250, 60, 60, 60, 40, 6, 8, 6, 4, 10],
            "obj": ["vi", "fo", "inte", "agi", "sa", "cri", "re_tierra_por", "re_fuego_por", "re_aire_por", "pla"]
        },
        "Anillo inestable": {
            "min": [186, 40, 3, 3, 3, 3, 3, 11, 8, 31],
            "max": [200, 50, 5, 5, 5, 5, 5, 15, 12, 40],
            "obj": ["vi", "sa", "re_neu", "re_tierra", "re_fuego", "re_agua", "re_aire", "hui", "es_pm", "re_emp"]
        },
        "Anillo rey jugador": {
            "min": [236, 45, 45, 21, 3, 1, 11, 11, 11, 6, 10, 4],
            "max": [250, 50, 50, 40, 3, 1, 11, 11, 11, 10, 10, 6],
            "obj": ["vi", "fo", "inte", "sa", "cri", "al", "da_neu", "da_tierra", "da_fuego", "prospe", "re_fuego_por", "ret_pm"]
        },
        "Anillo momistianillo": {
            "min": [286, 35, 35, 21, 4, 1, 6, 6, 6, 8, 7, 25],
            "max": [300, 40, 40, 40, 4, 1, 7, 7, 7, 10, 7, 30],
            "obj": ["vi", "fo", "inte", "sa", "cri", "al", "da_neu", "da_tierra", "da_fuego", "cu", "re_agua_por", "re_cri"]
        },
        "Anillo Brazalete fondos marinos": {
            "min": [236, 55, 25, 3, 1, 11, 10, 6, 4],
            "max": [250, 60, 50, 3, 1, 12, 10, 10, 5],
            "obj": ["vi", "sue", "sa", "cri", "al", "da_agua", "re_fuego_por", "pla", "es_pm"]
        },
        "Anillo crustico": {
            "min": [336, 71, 21, 2, 11, 11, 7, 7, 6],
            "max": [350, 80, 40, 2, 12, 12, 7, 10, 10],
            "obj": ["vi", "fo", "sa", "cri", "da_neu", "da_tierra", "re_agua_por", "pla", "ret_pa"]
        },
        "Anillo lunar": {
            "min": [236, 21, 41, 1, 13, 6, 101, 8],
            "max": [250, 30, 50, 1, 15, 15, 150, 10],
            "obj": ["vi", "sa", "pot", "inv", "da_tierra", "prospe", "ini", "ret_pa"]
        },
        "Anillo de nidas": {
            "min": [236, 38, 40, 1, 11, 8, 10, 8, 4],
            "max": [250, 40, 50, 1, 11, 10, 10, 10, 4],
            "obj": ["vi", "inte", "sa", "inv", "da_fuego", "cu", "re_tierra_por", "hui", "ret_pm"]
        },
        "Capa Ordiosera": {
            "min": [390, 57, 57, 30, 5, 13, 16, 16, 350, 10, 14],
            "max": [440, 60, 60, 50, 5, 16, 16, 16, 400, 10, 20],
            "obj": ["vi", "fo", "sue", "sa", "cri", "da_neu", "da_tierra", "da_agua", "ini", "re_neu_por", "re_fuego"]
        },
        "Anillo rey Stropajo": {
            "min": [136, 38, 38, 21, 1, 5, 10, 7, 8, 8],
            "max": [150, 40, 40, 35, 1, 7, 15, 7, 10, 10],
            "obj": ["vi", "sue", "agi", "sa", "al", "da", "prospe", "re_tierra_por", "re_tierra", "re_agua"]
        },
        "Anillo de Gwen astarde": {
            "min": [55, 55, 21, 5, 2, 13, 13, 13, 6, 301, 8, 11],
            "max": [60, 60, 30, 5, 2, 15, 15, 15, 10, 400, 10, 15],
            "obj": ["fo", "sue", "sa", "cri", "inv", "da_neu", "da_tierra", "da_agua", "prospe", "ini", "ret_pa", "da_emp"]
        },
        "Escudo ilyzaelle": {
            "min": [236, 61, 61, 25, 5, 10, 10, 7],
            "max": [250, 70, 70, 40, 5, 10, 10, 10],
            "obj": ["vi", "sue", "agi", "sa", "re_neu_por", "re_agua_por", "re_aire_por", "es_pm"]
        },
        "Anillo criocrono": {
            "min": [286, 38, 38, 25, 1, 11, 11, 8, 8],
            "max": [300, 40, 40, 30, 1, 11, 11, 10, 10],
            "obj": ["vi", "inte", "sue", "sa", "al", "da_fuego", "da_agua", "cu", "da_cri"]
        },
        "Anillo alianza inestable": {
            "min": [186, 41, 4, 4, 4, 4, 4, 11, 10, 33],
            "max": [200, 50, 5, 5, 5, 5, 5, 15, 12, 40],
            "obj": ["vi", "sa", "da_neu", "da_tierra", "da_fuego", "da_aire", "da_agua", "pla", "es_pa", "da_emp"]
        },
        "Anillo pikanillo": {
            "min": [236, 28, 28, 20, 13, 5, 1, 11, 11, 11, 7, 7, 5],
            "max": [250, 30, 30, 25, 15, 5, 1, 11, 11, 11, 7, 7, 5],
            "obj": ["vi", "fo", "sue", "sa", "pot", "cri", "inv", "da_neu", "da_tierra", "da_agua", "re_fuego_por", "re_aire_por", "ret_pm"]
        },
        "Anillo alianza fiedad": {
            "min": [186, 30, 45, 4, 5, 6],
            "max": [200, 40, 50, 4, 15, 10],
            "obj": ["vi", "sa", "pot", "cri", "prospe", "re_emp"]
        },
        "Anillo Ceano": {
            "min": [286, 45, 21, 3, 1, 8, 5, 5, 11, 10, 10, 4, 25],
            "max": [300, 50, 30, 3, 1, 10, 6, 6, 25, 10, 10, 5, 30],
            "obj": ["vi", "inte", "sa", "cri", "al", "da_fuego", "da_agua", "da_aire", "prospe", "re_agua_por", "re_aire_por", "pla", "re_emp"]
        },
        "Anillo alianza levitrof": {
            "min": [236, 38, 38, 38, 25, 1, 9, 9, 9, 9, 201, 6],
            "max": [250, 40, 40, 40, 40, 1, 9, 9, 9, 9, 300, 6],
            "obj": ["vi", "fo", "inte", "sue", "sa", "inv", "da_neu", "da_tierra", "da_fuego", "da_agua", "ini", "re_fuego_por"]
        },
        "Escudo Solar": {
            "min": [236, 61, 61, 7, 7, 7, 45],
            "max": [250, 70, 70, 7, 7, 7, 80],
            "obj": ["vi", "fo", "inte", "re_neu_por", "re_tierra_por", "re_fuego_por", "re_emp"]
        },
        "Anillo Codicia de Miseria": {
            "min": [286, 48, 48, 20, 3, 8, 8, 10, 8, 8],
            "max": [300, 50, 50, 30, 3, 10, 10, 10, 10, 10],
            "obj": ["vi", "sue", "agi", "sa", "cri", "da_agua", "da_aire", "re_aire_por", "es_pa", "da_cri"]
        },


        "Escudo Ariete de Gargandias": {
            "min": [220, 40, 400, 4, 4, 4, 4, 4, 25, 49, 5],
            "max": [250, 50, 500, 5, 5, 5, 5, 5, 30, 60, 5],
            "obj": ["vi", "sa", "ini", "re_neu_por", "re_tierra_por", "re_fuego_por", "re_agua_por", "re_aire_por", "da_emp", "re_emp", "re_fuego_por"]
        }
    }

    if objeto_seleccionado_str in objeto_stats:
        stats = objeto_stats[objeto_seleccionado_str]
        estadisticas_min.extend(stats["min"])
        estadisticas_max.extend(stats["max"])
        estadisticas_objeto.extend(stats["obj"])
    else:
        print("Objeto no encontrado o no seleccionado.")

    mostrar_controles_estadisticas()

    root.update_idletasks()
    root.geometry('{}x{}'.format(root.winfo_width(), root.winfo_height()))


def confirmar_y_salir():
    """
    Guarda las estadísticas actuales y la cantidad de exos en la variable global de resultado
    y cierra la ventana.
    """
    global resultado_magueo, entry_cantidad_exos
    objeto_actual = combo_objetos.get()

    # Obtener la cantidad de exos del input
    try:
        cantidad_exos = int(entry_cantidad_exos.get())
        if cantidad_exos <= 0:
            tk.messagebox.showerror("Error de Entrada", "La cantidad de exos debe ser un número positivo.")
            return  # No cerrar la ventana
    except ValueError:
        tk.messagebox.showerror("Error de Entrada", "Por favor, introduce un número válido para la cantidad de exos.")
        return  # No cerrar la ventana

    # celdas_no_procesar should ideally be dynamically generated based on the actual stats shown,
    # or passed as part of the object_stats dictionary if fixed per item.
    # For now, it's a fixed list, so it remains as is.
    celdas_no_procesar = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12),
        (0, 13),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12),
        (1, 13),

        (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12),
        (4, 13),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12),
        (5, 13),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12),
        (6, 13),
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12),
        (7, 13)
    ]

    # Actualizar resultado_magueo con la nueva cantidad de exos
    # The global lists estadisticas_objeto, estadisticas_min, estadisticas_max
    # should now correctly contain only the stats for the currently selected object.
    resultado_magueo = (objeto_actual, estadisticas_objeto, celdas_no_procesar, estadisticas_min, estadisticas_max,
                        cantidad_exos)
    root.quit()
    root.destroy()


def recoger_nuevas_estadisticas_y_terminar():
    """
    Función principal que lanza la interfaz y espera a que el usuario confirme.
    Retorna las estadísticas seleccionadas, ajustadas y la cantidad de exos deseados.
    """
    global root, entry_busqueda, combo_objetos, frame_estadisticas, entry_cantidad_exos

    style = Style(theme="darkly")
    root = style.master
    root.geometry("900x1200")
    root.title("Dofus Automatizar Forjamagia")

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    search_frame = ttk.LabelFrame(main_frame, text="Buscar y Seleccionar Objeto", padding="10")
    search_frame.pack(pady=10, fill=tk.X)

    ttk.Label(search_frame, text="Buscar objeto:").pack(pady=2, anchor="w")
    entry_busqueda = ttk.Entry(search_frame)
    entry_busqueda.pack(pady=2, fill=tk.X)
    entry_busqueda.bind("<KeyRelease>", actualizar_lista)

    ttk.Label(search_frame, text="Selecciona el objeto a maguear:").pack(pady=5, anchor="w")
    combo_objetos = ttk.Combobox(search_frame, values=objetos_magueo,
                                 state="readonly")
    combo_objetos.pack(pady=2, fill=tk.X)
    combo_objetos.current(0)

    ttk.Button(search_frame, text="Cargar Estadísticas Iniciales", command=cargar_estadisticas_iniciales).pack(pady=10)

    # --- Sección para la cantidad de exos ---
    exos_frame = ttk.LabelFrame(main_frame, text="Modo de Múltiples Exos", padding="10")
    exos_frame.pack(pady=10, fill=tk.X)

    ttk.Label(exos_frame, text="Cantidad de exos deseados (1 para magueo único):").pack(pady=2, anchor="w")
    entry_cantidad_exos = ttk.Entry(exos_frame)
    entry_cantidad_exos.pack(pady=2, fill=tk.X)
    entry_cantidad_exos.insert(0, "1")  # Valor por defecto de 1
    # --- Fin de la sección para la cantidad de exos ---

    frame_estadisticas = ttk.LabelFrame(main_frame, text="Estadísticas del Objeto",
                                        padding="10")
    frame_estadisticas.pack(pady=10, fill=tk.BOTH, expand=True)

    mostrar_controles_estadisticas()

    boton_confirmar = ttk.Button(main_frame, text="Confirmar Estadísticas e Iniciar Magueo", command=confirmar_y_salir)
    boton_confirmar.pack(pady=15)

    root.mainloop()

    # Retorna el resultado_magueo que ahora incluye la cantidad de exos
    return resultado_magueo


# --- Para probar Interfaz_magueo.py de forma independiente ---
if __name__ == "__main__":
    objeto, stats_obj, celdas_no_procesar, min_stats, max_stats, cantidad_exos = recoger_nuevas_estadisticas_y_terminar()
    print("\n--- Estadísticas Finales Seleccionadas ---")
    print("Objeto:", objeto)
    print("Nombres de Stats:", stats_obj)
    print("Celdas a no procesar:", celdas_no_procesar)
    print("Valores Mínimos Ajustados:", min_stats)
    print("Valores Máximos Ajustados:", max_stats)
    print("Cantidad de Exos Deseados:", cantidad_exos)