import sys

# Importa los módulos (asegúrate de que existan y tengan función main)
import Setup_Ring
import Setup_Runes_Filter
import Setup_Read_New_Item_Name
import Setup_Item_Stats_Database
import Setup_Equipo_Recursos

def main():

    print("Ejecutando Setup_Equipo_Recursos...")
    Setup_Equipo_Recursos.main("Equipo")  # o "Recursos" según

    print("Ejecutando Setup_Runes_Filter...")
    # Si tu módulo tiene otra función principal, cámbiala aquí
    Setup_Runes_Filter.main()

    print("Ejecutando Setup_Read_New_Item_Name...")
    Setup_Item_Name = Setup_Read_New_Item_Name.read_new_item_name()

    print("Ejecutando Setup_Item_Stats_Database...")
    Setup_Stats = Setup_Item_Stats_Database.get_item_stats(Setup_Item_Name)

    print("Ejecutando Setup_Ring...")
    Setup_Equipo_Recursos.main("Equipo")  # o "Recursos" según
    Setup_Ring.main()

    print(Setup_Stats)
    return Setup_Stats

if __name__ == "__main__":
    main()

