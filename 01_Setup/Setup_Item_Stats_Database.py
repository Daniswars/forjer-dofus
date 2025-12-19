"""
Módulo de solo base de datos: dado el nombre de un anillo devuelve sus estadísticas.
Funciones públicas:
- get_item_stats(name) -> dict | None
- list_items() -> list[str]
"""

ITEM_STATS = {
    "Anillo de vueloceronte": {
        "min": [236, 91, 4, 16, 10],
        "max": [250, 100, 5, 20, 10],
        "obj": ["vi", "sue", "cri", "da_agua", "re_agua_por"]
    },
    "Alianza de Pandamonium": {
        "min": [236, 55, 14, 1, 8, 8, 240, 7, 6, 7, 11],
        "max": [250, 60, 20, 1, 8, 8, 300, 7, 8, 10, 15],
        "obj": ["vi", "fo", "sa", "inv", "da_neu", "da_tierra", "ini", "re_tierra_por", "hui", "es_pa", "re_emp"]
    },
    "Anillo corrupcion": {
        "min": [245, 55, 16, 7, 12, 11, 10, 0, 9],
        "max": [250, 60, 20, 7, 12, 12, 10, 5, 10],
        "obj": ["vi", "fo", "sa", "cri", "da_neu", "da_tierra", "re_agua_por", "es_pa", "da_cri"]
    },
    "Anillo de allister": {
        "min": [236, 66, 28, 5, 1, 13, 0, 4, 11],
        "max": [250, 75, 45, 5, 1, 15, 15, 6, 15],
        "obj": ["vi", "agi", "sa", "cri", "inv", "da_aire", "prospe", "es_pa", "re_cri"]
    },
    "Ternura de Belladona": {
        "min": [336, 23, 28, 5, 5, 8, 0, 16, 8],
        "max": [350, 30, 30, 5, 5, 10, 10, 20, 10],
        "obj": ["vi", "sa", "pot", "re_tierra_por", "re_fuego_por", "pla", "hui", "es_pa", "re_cri"]
    },
    "Anillo XLII": {
        "min": [186, 38, 38, 20, 3, 5, 5, 7, 5, 9],
        "max": [200, 40, 40, 25, 3, 6, 6, 6, 7, 12],
        "obj": ["vi", "fo", "agi", "sa", "cri", "da_tierra", "da_aire", "re_neu_por", "pla", "re_cri"]
    },
    "Amargura de Belladona": {
        "min": [236, 40, 25, 5, 5, 7, 0, 17, 6],
        "max": [250, 45, 30, 5, 5, 10, 10, 20, 10],
        "obj": ["vi", "sa", "pot", "re_agua_por", "re_aire_por", "hui", "pla", "ret_pa", "re_cri"]
    },
    "Anillo Colette": {
        "min": [136, 45, 25, 1, 1, 0, 10, 6, 6, 6, 16],
        "max": [150, 50, 40, 1, 5, 20, 10, 10, 10, 6, 20],
        "obj": ["vi", "agi", "sa", "al", "da", "prospe", "re_agua_por", "re_neu", "re_tierra", "re_agua", "da_tram"]
    },
    "Alianza de corrupción": {
        "min": [286, 48, 16, 3, 1, 1, 7, 7, 5],
        "max": [300, 50, 30, 3, 1, 1, 7, 7, 7],
        "obj": ["vi", "fo", "sa", "cri", "al", "inv", "re_tierra_por", "re_aire_por", "ret_pm"]
    },
    "Negruraro": {
        "min": [286, 65, 4, 8, 7, 7, 0, 4, 23],
        "max": [300, 75, 4, 8, 7, 7, 0, 8, 25],
        "obj": ["vi", "agi", "cri", "da_aire", "re_tierra_por", "re_aire_por", "hui", "es_pm", "da_emp"]
    },
    "Ghulanillo": {
        "min": [236, 35, 35, 35, 23, 6, 6, 6, 6, 10, 22],
        "max": [250, 40, 40, 40, 30, 7, 7, 7, 7, 10, 25],
        "obj": ["vi", "fo", "inte", "sue", "sa", "da_neu", "da_tierra", "da_fuego", "da_agua", "re_tierra_por",
                "re_cri"]
    },
    "Alianza Natomia": {
        "min": [336, 66, 21, 1, 13, 11, 6],
        "max": [350, 75, 40, 1, 15, 15, 8],
        "obj": ["vi", "inte", "sa", "al", "da_fuego", "pla", "ret_pm"]
    },
    "Anillo de brus": {
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
    "Guantes sota afortunada": {
        "min": [286, 55, 25, 1, 13, 0, 10, 4, 12],
        "max": [300, 60, 40, 1, 15, 12, 10, 6, 15],
        "obj": ["vi", "agi", "sa", "al", "da_aire", "prospe", "re_tierra_por", "es_pm", "re_emp"]
    },
    "Anillo poseido": {
        "min": [236, 55, 55, 2, 1, 7, 7, 7, 7, 7, 6],
        "max": [250, 60, 60, 2, 1, 7, 7, 7, 7, 7, 6],
        "obj": ["vi", "fo", "agi", "cri", "al", "da_neu", "da_tierra", "da_aire", "re_neu_por", "re_aire_por",
                "ret_pm"]
    },
    "Anillo de noai aludem": {
        "min": [86, 55, 55, 21, 6, 1, 1, 6, 6, 8, 3, 3, 11],
        "max": [100, 60, 60, 40, 6, 1, 1, 6, 6, 8, 10, 10, 11],
        "obj": ["vi", "inte", "agi", "sa", "cri", "al", "inv", "da_fuego", "da_aire", "re_agua_por", "re_tierra",
                "re_aire", "da_cri"]
    },
    "Crueldad de Belladona": {
        "min": [286, 21, 55, 8, 8, 8, 9, 450, 10, 0, 0, 8],
        "max": [300, 30, 60, 10, 10, 10, 10, 500, 10, 0, 0, 10],
        "obj": ["vi", "sa", "pot", "da_tierra", "da_fuego", "da_agua", "da_aire", "ini", "re_neu_por", "pla", "hui",
                "re_cri"]
    },
    "Brazalete de melenutrof": {
        "min": [286, 45, 4, 2, 8, 8, 8, 10],
        "max": [300, 50, 4, 2, 10, 10, 10, 10],
        "obj": ["vi", "pot", "cri", "al", "da_neu", "da_tierra", "da_agua", "re_neu_por"]
    },
    "Alianza quemaalmas": {
        "min": [286, 55, 55, 53, 16, 6, 6, 6, 6, 7, 7],
        "max": [300, 60, 60, 55, 30, 6, 6, 6, 6, 7, 7],
        "obj": ["vi", "fo", "inte", "agi", "sa", "da_neu", "da_tierra", "da_fuego", "da_aire", "re_agua_por",
                "re_aire_por"]
    },
    "Lanza de guerra": {
        "min": [336, 55, 14, 3, 8, 0, 7, 7, 13],
        "max": [350, 60, 30, 3, 8, 0, 7, 7, 13],
        "obj": ["vi", "inte", "sa", "cri", "da_fuego", "cu", "re_tierra_por", "re_aire_por", "da_cri"]
    },
    "Anillo de styx": {
        "min": [186, 58, 30, 3, 9, 280, 10, 0, 8],
        "max": [200, 60, 40, 3, 10, 350, 10, 0, 15],
        "obj": ["vi", "sue", "sa", "cri", "da_agua", "ini", "re_agua_por", "re_fuego_por", "re_agua"]
    },
    "Alianza golosona": {
        "min": [236, 55, 55, 30, 1, 11, 11, 0, 330, 7, 7, 7, 4],
        "max": [250, 60, 60, 40, 1, 12, 12, 10, 400, 7, 7, 7, 5],
        "obj": ["vi", "sue", "agi", "sa", "al", "da_agua", "da_aire", "prospe", "ini", "re_neu_por",
                "re_tierra_por", "re_fuego_por", "pla"]
    },
    "Gelanillo": {
        "min": [0],
        "max": [1],
        "obj": ["pa"]
    },
    "Anillo de Grithril": {
        "min": [236, 46, 46, 22, 3, 7, 7, 7, 10, 5, 11],
        "max": [250, 50, 50, 40, 3, 8, 8, 8, 10, 7, 15],
        "obj": ["vi", "fo", "sue", "sa", "cri", "da_neu", "da_tierra", "da_agua", "re_agua_por", "pla", "re_cri"]
    },
    "Alianza de Elya Wood": {
        "min": [86, 32, 4, 0, 10, 10, 10, 10],
        "max": [100, 35, 6, 0, 10, 10, 12, 12],
        "obj": ["vi", "inte", "cu", "prospe", "re_tierra_por", "re_fuego_por", "re_tierra", "re_fuego"]
    },
    "Cesto de devastador": {
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
    "Anillidon": {
        "min": [236, 55, 21, 2, 1, 8, 8, 4, 4, 12],
        "max": [250, 60, 30, 2, 1, 10, 10, 5, 5, 15],
        "obj": ["vi", "fo", "sa", "cri", "inv", "da_neu", "da_tierra", "da_aire", "hui", "es_pa", "re_cri"]
    },
    "Anillo Ancestral": {
        "min": [116, 28, 38, 21, 0, 6, 6],
        "max": [130, 30, 40, 35, 0, 6, 6],
        "obj": ["vi", "fo", "sue", "sa", "prospe", "re_tierra_por", "re_agua_por"]
    },
    "Kralanillo": {
        "min": [186, 46, 46, 34, 3, 1, 4, 8, 0, 10, 6],
        "max": [200, 50, 50, 50, 3, 1, 6, 10, 0, 10, 10],
        "obj": ["vi", "inte", "agi", "sa", "cri", "al", "da", "cu", "prospe", "re_neu_por", "re_neu"]
    },
    "Anillo de micholobo": {
        "min": [186, 35, 35, 16, 1, 8, 8, 8, 4, 8],
        "max": [200, 40, 40, 25, 1, 8, 8, 8, 4, 8],
        "obj": ["vi", "fo", "sue", "sa", "inv", "da_neu", "da_tierra", "da_agua", "ret_pm", "da_cri"]
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
    "Anillo de kukoloide": {
        "min": [286, 38, 38, 38, 9, 9, 9, 9, 201, 8, 3],
        "max": [300, 40, 40, 40, 9, 9, 9, 9, 300, 8, 6],
        "obj": ["vi", "fo", "inte", "agi", "da_neu", "da_tierra", "da_fuego", "da_agua", "ini", "re_agua_por", "pla"]
    },
    "Anillo inestable": {
        "min": [186, 40, 3, 3, 3, 3, 3, 11, 8, 31],
        "max": [200, 50, 5, 5, 5, 5, 5, 15, 12, 40],
        "obj": ["vi", "sa", "re_neu", "re_tierra", "re_fuego", "re_agua", "re_aire", "hui", "es_pm", "re_emp"]
    },
    "Anillo del rey jugador": {
        "min": [236, 45, 45, 21, 3, 1, 11, 11, 11, 6, 10, 4],
        "max": [250, 50, 50, 40, 3, 1, 11, 11, 11, 10, 10, 6],
        "obj": ["vi", "fo", "inte", "sa", "cri", "al", "da_neu", "da_tierra", "da_fuego", "prospe", "re_fuego_por", "ret_pm"]
    },
    "Momistianillo": {
        "min": [286, 35, 35, 21, 4, 1, 6, 6, 6, 8, 7, 25],
        "max": [300, 40, 40, 40, 4, 1, 7, 7, 7, 10, 7, 30],
        "obj": ["vi", "fo", "inte", "sa", "cri", "al", "da_neu", "da_tierra", "da_fuego", "cu", "re_agua_por", "re_cri"]
    },
    "Brazalete de los fondos marinos": {
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
    "Soberano sello de rey Stropajo": {
        "min": [136, 38, 38, 21, 1, 5, 10, 7, 8, 8],
        "max": [150, 40, 40, 35, 1, 7, 15, 7, 10, 10],
        "obj": ["vi", "sue", "agi", "sa", "al", "da", "prospe", "re_tierra_por", "re_tierra", "re_agua"]
    },
    "Anillo Gwen Astarde": {
        "min": [55, 55, 21, 5, 2, 13, 13, 13, 6, 301, 8, 11],
        "max": [60, 60, 30, 5, 2, 15, 15, 15, 10, 400, 10, 15],
        "obj": ["fo", "sue", "sa", "cri", "inv", "da_neu", "da_tierra", "da_agua", "prospe", "ini", "ret_pa", "da_emp"]
    },
    "Anillo criocrono": {
        "min": [286, 38, 38, 25, 1, 11, 11, 8, 8],
        "max": [300, 40, 40, 30, 1, 11, 11, 10, 10],
        "obj": ["vi", "inte", "sue", "sa", "al", "da_fuego", "da_agua", "cu", "da_cri"]
    },
    "Alianza inestable": {
        "min": [186, 41, 4, 4, 4, 4, 4, 11, 10, 33],
        "max": [200, 50, 5, 5, 5, 5, 5, 15, 12, 40],
        "obj": ["vi", "sa", "da_neu", "da_tierra", "da_fuego", "da_aire", "da_agua", "pla", "es_pa", "da_emp"]
    },
    "Pikanillo": {
        "min": [236, 28, 28, 20, 13, 5, 1, 11, 11, 11, 7, 7, 5],
        "max": [250, 30, 30, 25, 15, 5, 1, 11, 11, 11, 7, 7, 5],
        "obj": ["vi", "fo", "sue", "sa", "pot", "cri", "inv", "da_neu", "da_tierra", "da_agua", "re_fuego_por", "re_aire_por", "ret_pm"]
    },
    "Alianza fiedad": {
        "min": [186, 30, 45, 4, 5, 6],
        "max": [200, 40, 50, 4, 15, 10],
        "obj": ["vi", "sa", "pot", "cri", "prospe", "re_emp"]
    },
    "Anillo Ceano": {
        "min": [286, 45, 21, 3, 1, 8, 5, 5, 11, 10, 10, 4, 25],
        "max": [300, 50, 30, 3, 1, 10, 6, 6, 25, 10, 10, 5, 30],
        "obj": ["vi", "inte", "sa", "cri", "al", "da_fuego", "da_agua", "da_aire", "prospe", "re_agua_por", "re_aire_por", "pla", "re_emp"]
    },
    "Alianza levitrof": {
        "min": [236, 38, 38, 38, 25, 1, 9, 9, 9, 9, 201, 6],
        "max": [250, 40, 40, 40, 40, 1, 9, 9, 9, 9, 300, 6],
        "obj": ["vi", "fo", "inte", "sue", "sa", "inv", "da_neu", "da_tierra", "da_fuego", "da_agua", "ini", "re_fuego_por"]
    },
    "Codicia de Miseria": {
        "min": [286, 48, 48, 20, 3, 8, 8, 10, 8, 8],
        "max": [300, 50, 50, 30, 3, 10, 10, 10, 10, 10],
        "obj": ["vi", "sue", "agi", "sa", "cri", "da_agua", "da_aire", "re_aire_por", "es_pa", "da_cri"]
    },
}


def get_item_stats(name: str):
    """
    Devuelve un dict {'min': [...], 'max': [...], 'obj': [...]} para el nombre proporcionado.
    Búsqueda insensible a mayúsculas y espacios; intenta coincidencia exacta, luego coincidencia lowercase,
    luego búsqueda por inclusión.
    Retorna None si no se encuentra.
    """
    if not name:
        return None
    name = name.strip()
    # 1) Intentar clave exacta
    if name in ITEM_STATS:
        return ITEM_STATS[name]
    # 2) Búsqueda insensible a mayúsculas
    lname = name.lower()
    for key, val in ITEM_STATS.items():
        if key.lower() == lname:
            return val
    # 3) Búsqueda por inclusión (si el término del usuario aparece en la clave)
    for key, val in ITEM_STATS.items():
        if lname in key.lower():
            return val
    return None


def list_items():
    "Devuelve la lista de nombres disponibles (ordenada)."
    return sorted(ITEM_STATS.keys())


# Bloque de prueba mínimo
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        nombre = " ".join(sys.argv[1:])
        res = get_item_stats(nombre)
        if res is None:
            print(f"No encontrado: '{nombre}'")
        else:
            print(f"Encontrado: '{nombre}' -> min: {res['min']}\nmax: {res['max']}\nobj: {res['obj']}")
    else:
        print(f"{len(ITEM_STATS)} items disponibles. Ejemplo: muestra primeros 10 nombres:")
        for i, k in enumerate(list_items()[:10], 1):
            print(f"{i}. {k}")
        print("\nPrueba interactiva: escribe el nombre del anillo (enter para salir).")
        try:
            while True:
                nombre = input("Nombre> ").strip()
                if not nombre:
                    break
                r = get_item_stats(nombre)
                if r is None:
                    print("No encontrado.")
                else:
                    print("min:", r["min"])
                    print("max:", r["max"])
                    print("obj:", r["obj"])
        except (KeyboardInterrupt, EOFError):
            print("\nSalida.")
