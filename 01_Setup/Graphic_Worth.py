import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configuración de estilo básica para los gráficos
plt.rcParams["figure.figsize"] = (12, 6)


def cargar_y_limpiar_datos(archivo_excel, hojas):
    df_lista = []

    if not os.path.exists(archivo_excel):
        print(f"No se encontró el archivo: {archivo_excel}")
        return pd.DataFrame()

    for hoja in hojas:
        try:
            print(f"Procesando hoja: {hoja}...")
            df = pd.read_excel(archivo_excel, sheet_name=hoja)

            # Estandarizar nombres de columnas clave ya que varían entre "Éxitos" y "Fallos"
            df.rename(
                columns={
                    "Intentos Totales": "Intentos",
                    "Kamas por Intento (promedio)": "Kamas por Intento",
                    "Inversion Total": "Inversion",
                },
                inplace=True,
            )

            # Quedarnos solo con lo que nos interesa para costes
            columnas_interes = [
                "Objeto",
                "Intentos",
                "Inversion",
                "Kamas por Intento",
                "Tiempo Medio por Intento (s)",
            ]
            # Filtrar solo las columnas que existan en el archivo por si acaso
            columnas_validas = [c for c in columnas_interes if c in df.columns]

            df_lista.append(df[columnas_validas])
        except Exception as e:
            print(f"No se pudo leer la hoja '{hoja}': {e}")

    if not df_lista:
        print("No se encontraron hojas válidas o no contienen las columnas necesarias.")
        return pd.DataFrame()

    # Combinar todos los datos en un solo DataFrame
    df_completo = pd.concat(df_lista, ignore_index=True)

    # --- LIMPIEZA DE DATOS ---
    # 1. Eliminar filas sin intentos o donde la inversión sea 0 (sesiones vacías)
    df_completo = df_completo[df_completo["Intentos"] > 0]
    df_completo = df_completo[df_completo["Inversion"] > 0]

    # 2. Convertir a numérico por seguridad y limpiar nulos
    df_completo["Kamas por Intento"] = pd.to_numeric(
        df_completo["Kamas por Intento"], errors="coerce"
    )

    # 3. FILTRO CRÍTICO: Eliminar errores de registro (> 200,000 kamas por intento)
    df_inicial = len(df_completo)
    df_completo = df_completo[df_completo["Kamas por Intento"] <= 200000]
    print(
        f"Filtradas {df_inicial - len(df_completo)} filas por superar el límite de 200k kamas/intento."
    )

    return df_completo


def generar_graficos_costes(df, modo_orden="muestras"):
    if df.empty:
        print("No hay datos suficientes para graficar.")
        return

    # Trabajar con una copia y pasar los costos directamente a Millones de Kamas
    df = df.copy()
    df["Kamas por Intento (M)"] = df["Kamas por Intento"] / 1_000_000

    # Agrupamos por Objeto para ver los sospechosos habituales que más kamas tragan
    df_agrupado = (
        df.groupby("Objeto")
        .agg(
            Inversion_Total=("Inversion", "sum"),
            Coste_Medio_Intento_M=("Kamas por Intento (M)", "mean"),
            Tiempo_Medio_Intento=("Tiempo Medio por Intento (s)", "mean"),
            Total_Intentos=("Intentos", "sum"),
            Muestras=("Objeto", "size"),  # Cuenta las veces que aparece el registro
        )
        .reset_index()
    )

    # Convertimos la media por intento a media por 80 intentos (en millones)
    df_agrupado["Coste_80_Intentos_M"] = df_agrupado["Coste_Medio_Intento_M"] * 80

    # Lógica de ordenación según la opción elegida
    if modo_orden == "coste_menor":
        df_top_costes = df_agrupado.nsmallest(50, "Coste_80_Intentos_M").sort_values(
            by="Coste_80_Intentos_M", ascending=False
        )
        titulo_grafico = "Dispersión del Coste por Intento (Top 50 más baratos)"
    elif modo_orden == "coste_mayor":
        df_top_costes = df_agrupado.nlargest(50, "Coste_80_Intentos_M").sort_values(
            by="Coste_80_Intentos_M", ascending=True
        )
        titulo_grafico = "Dispersión del Coste por Intento (Top 50 más caros)"
    else:  # por defecto "muestras"
        df_top_costes = df_agrupado.nlargest(50, "Muestras").sort_values(
            by="Muestras", ascending=True
        )
        titulo_grafico = "Dispersión del Coste por Intento (Top 50 más frecuentes)"

    # -------------------------------------------------------------
    # GRÁFICO: Distribución del Coste por Intento real (Boxplot)
    # -------------------------------------------------------------
    df_filtrado_top = df[df["Objeto"].isin(df_top_costes["Objeto"])]
    objetos = df_top_costes["Objeto"].tolist()
    
    # Crear etiquetas combinando nombre, número de muestras y coste por 80 intentos
    etiquetas = [
        f"{row.Objeto} (N={row.Muestras}) | 80 Int: {row.Coste_80_Intentos_M:.2f}M" 
        for row in df_top_costes.itertuples()
    ]
    
    datos_boxplot = [
        df_filtrado_top[df_filtrado_top["Objeto"] == obj]["Kamas por Intento (M)"].dropna()
        for obj in objetos
    ]

    # Hacemos la figura más grande verticalmente y trabajamos sobre el objeto 'ax' para personalizar
    fig, ax = plt.subplots(figsize=(14, 14))
    bplot = ax.boxplot(
        datos_boxplot, vert=False, labels=etiquetas, patch_artist=True, 
        medianprops=dict(color="black", linewidth=1.5)
    )

    # Cargar colormap para colorear de forma distinta y bandas horizontales tipo tabla
    # usamos un colormap bastante amplio para diferenciar muchos
    colors = plt.cm.tab20.colors + plt.cm.tab20b.colors + plt.cm.tab20c.colors
    
    for i, patch in enumerate(bplot["boxes"]):
        # Coloreo de la caja
        patch.set_facecolor(colors[i % len(colors)])
        # Banda visual de separación "tipo tabla" para las filas pares
        if i % 2 == 0:
            ax.axhspan(i + 0.5, i + 1.5, facecolor='lightgray', alpha=0.3, zorder=0)

    ax.axvline(
        x=0.1,  # 100,000 Kamas son 0.1 Millones
        color="red",
        linestyle="--",
        label="Umbral de Alerta (0.1M/intento)",
    )
    ax.grid(True, axis="x", linestyle="--", alpha=0.7)

    ax.set_title(
        titulo_grafico,
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Millones de Kamas por Intento", fontsize=12)
    ax.set_ylabel("Objeto (Muestras)", fontsize=12)
    ax.legend(loc="upper right")
    
    plt.tight_layout()
    plt.savefig("dispersion_coste_por_intento.png")
    plt.show()


# --- EJECUCIÓN DEL PROGRAMA ---
# Directorio base y archivo de Excel
base_dir = r"C:\Users\danis\OneDrive\Desktop\Forjamagia"
archivo_excel = os.path.join(base_dir, "20260213_Dofus3_Mage_Database.xlsx")

# Especifica los nombres de las hojas a procesar
hojas_a_procesar = [
    "Exitos Forjamagia",
    "Fallos Forjamagia",
    "Old 2",
    "Old 3",
]

# Ejecutar el flujo
datos_limpios = cargar_y_limpiar_datos(archivo_excel, hojas_a_procesar)

print("\n--- GENERANDO GRÁFICO ---")
# CAMBIA ESTE NÚMERO SI QUIERES OTRO ORDEN:
# "1" = Ordenar por cantidad realizada (Más frecuentes)
# "2" = Ordenar por coste de 80 intentos (Más baratos)
# "3" = Ordenar por coste de 80 intentos (Más caros)
OPCION_ELEGIDA = "1" 

if OPCION_ELEGIDA == "2":
    modo = "coste_menor"
elif OPCION_ELEGIDA == "3":
    modo = "coste_mayor"
else:
    modo = "muestras"

generar_graficos_costes(datos_limpios, modo)
