def stats_not_full(estadisticas_actuales, estadisticas_min):
    for i in range(len(estadisticas_actuales)):
        if estadisticas_actuales[i] < estadisticas_min[i]:
            return True  # Retorna True si alguna estadística actual es menor que la mínima
    return False  # Retorna False si todas las estadísticas actuales son mayores o iguales a las mínimas