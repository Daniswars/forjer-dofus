import sys

# Importa los módulos (asegúrate de que existan y tengan función main)
import Setup_Ring
import Setup_Runes_Filter
import Setup_Read_New_Item_Name
import Setup_Item_Stats_Database
import Setup_Equipo_Recursos
import Mage_Exo_Verify
import Aux_Guardar_exito

def _run_setup_steps():
    print("Ejecutando Setup_Equipo_Recursos...")
    Setup_Equipo_Recursos.main("Equipo")  # o "Recursos" según

    print("Ejecutando Setup_Runes_Filter...")
    Setup_Runes_Filter.main()

    print("Ejecutando Setup_Read_New_Item_Name...")
    setup_item_name = Setup_Read_New_Item_Name.read_new_item_name()

    print("Ejecutando Setup_Item_Stats_Database...")
    setup_stats = Setup_Item_Stats_Database.get_item_stats(setup_item_name)

    print("Ejecutando Setup_Ring...")
    Setup_Equipo_Recursos.main("Equipo")  # o "Recursos" según
    Setup_Ring.main()

    Setup_Equipo_Recursos.main("Recursos")  # o "Recursos" según
    return setup_item_name, setup_stats

def main():
    """
    Ejecuta la fase de setup y devuelve (item_name, item_stats).
    """
    Setup_Item_Name, Setup_Stats = _run_setup_steps()

    # Verificar exo antes de terminar el setup
    try:
        print("Verificando exo (PA/PM) antes de iniciar magueo...")
        if Mage_Exo_Verify.verify_success():
            print("Exo detectado. Ejecutando guardado...")
            Aux_Guardar_exito.perform_dofus_sequence()
            print("Rehaciendo setup tras guardar exo...")
            Setup_Item_Name, Setup_Stats = _run_setup_steps()
        else:
            print("No hay exo detectado. Continuando normal.")
    except Exception as e:
        print(f"Error en verificación/guardado de exo: {e}")

    print("Setup completado. Item:", Setup_Item_Name)
    return Setup_Item_Name, Setup_Stats



if __name__ == "__main__":
    main()
