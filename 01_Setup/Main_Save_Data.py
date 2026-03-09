import os
import json
import argparse
import sys
from datetime import datetime

# usa módulos locales
from Extra_get_kamas import get_kamas
from Extra_Database import agregar_datos

# archivo para guardar kamas iniciales por objeto
STORE_FILENAME = os.path.join(os.path.dirname(__file__), "last_kamas.json")


def _load_store():
    if os.path.exists(STORE_FILENAME):
        try:
            with open(STORE_FILENAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_store(store):
    try:
        with open(STORE_FILENAME, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("ERROR: no se pudo guardar last_kamas.json:", e)


def save_initial_kamas(objeto):
    """
    Captura kamas actuales y los guarda como 'iniciales' para el objeto.
    """
    print(f"[Main_Save_Data] Leyendo kamas iniciales para: {objeto} ...")
    kamas = get_kamas()
    if kamas == 0:
        print("[WARNING] get_kamas devolvió 0. Asegúrate de que la ventana esté visible.")
    store = _load_store()
    store[objeto] = {"kamas_iniciales": int(kamas), "timestamp": datetime.now().isoformat()}
    _save_store(store)
    print(f"[Main_Save_Data] Kamas iniciales guardadas: {kamas} (objeto: {objeto})")
    return kamas  # <-- DEVOLVER el valor


def finalize_session(objeto, intentos, exito, tiempo_medio_intento=None,
                     modo_encadenado_activo=False, precio_objeto_base=None,
                     precio_venta_objeto_final=None, tipo_exo=None, kamas_iniciales_arg=None):
    """
    Lee kamas finales (get_kamas), obtiene kamas iniciales desde el store o argumento,
    y llama a agregar_datos(...) para registrar en Excel.
    Devuelve 0 si todo OK, distinto de 0 en error.
    """
    # obtener kamas iniciales preferentemente del store
    store = _load_store()
    initial_entry = store.get(objeto)
    if kamas_iniciales_arg is not None:
        try:
            kamas_iniciales = int(kamas_iniciales_arg)
        except Exception:
            print("ERROR: kamas_iniciales inválido. Debe ser entero.")
            return 1
    elif initial_entry:
        kamas_iniciales = int(initial_entry.get("kamas_iniciales", 0))
        print(f"[Main_Save_Data] Usando kamas iniciales guardadas ({kamas_iniciales}) para objeto '{objeto}'.")
    else:
        print(f"[Main_Save_Data] No se encontró kamas iniciales para '{objeto}' en {STORE_FILENAME}. Intenta ejecutar 'save-init' antes o pasa --kamas-iniciales.")
        return 2

    print("[Main_Save_Data] Leyendo kamas finales (get_kamas)...")
    kamas_finales = get_kamas()
    print(f"[Main_Save_Data] Kamas finales leídos: {kamas_finales}")

    # llamar a la función de base de datos
    try:
        result = agregar_datos(
            objeto_seleccionado=objeto,
            intentos=int(intentos),
            kamas_iniciales=int(kamas_iniciales),
            kamas_finales=int(kamas_finales),
            exito=exito,
            tiempo_medio_intento=tiempo_medio_intento,
            modo_encadenado_activo=modo_encadenado_activo,
            precio_objeto_base=precio_objeto_base,
            precio_venta_objeto_final=precio_venta_objeto_final,
            tipo_exo=tipo_exo
        )
        if not result:
            print("ERROR: agregar_datos devolvió fallo. No se han guardado los datos en Excel.")
            return 3
        else:
            print("OK: Datos guardados en la base de datos (Excel).")
    except Exception as e:
        print("ERROR: agregar_datos falló con excepción:", e)
        return 3

    # si fue éxito, eliminar el registro inicial del store (se usó)
    if str(exito).strip().lower() in ("pa", "1", "success", "exito", "true"):
        if objeto in store:
            try:
                del store[objeto]
                _save_store(store)
                print(f"[Main_Save_Data] Entrada inicial eliminada de {STORE_FILENAME} para '{objeto}'.")
            except Exception as e:
                print("WARNING: no se pudo eliminar la entrada inicial:", e)

    return 0


# ------------------ NUEVA FUNCIÓN: leer ambas kamas y guardar ------------------
def capture_and_save(objeto,
                     intentos=3,
                     exito="PA",
                     tiempo_medio_intento=2.0,
                     modo_encadenado_activo=True,
                     precio_objeto_base=0,
                     precio_venta_objeto_final=0,
                     tipo_exo="PA",
                     use_store=False):
    """
    Flujo simple que:
      1) lee kamas actuales (iniciales)
      2) espera a que el usuario pulse Enter cuando quiera leer las kamas finales
      3) lee kamas finales y llama a agregar_datos con los valores suministrados
    Devuelve True si guardar en Excel tuvo éxito.
    """
    print(f"[capture_and_save] Objeto: {objeto} - leyendo kamas iniciales...")
    kamas_iniciales = get_kamas()
    print(f"[capture_and_save] Kamas iniciales leídas: {kamas_iniciales}")

    # Si el usuario quiere usar el store persistente, guardar iniciales
    if use_store:
        store = _load_store()
        store[objeto] = {"kamas_iniciales": int(kamas_iniciales), "timestamp": datetime.now().isoformat()}
        _save_store(store)
        print("[capture_and_save] Kamas iniciales también guardadas en last_kamas.json.")

    print("Realiza las acciones/magueos necesarios ahora. Cuando quieras leer las kamas finales y guardar, pulsa Enter.")
    try:
        input("Pulsa Enter para leer kamas finales y guardar (o Ctrl+C para cancelar)...")
    except KeyboardInterrupt:
        print("Operación cancelada por usuario antes de leer kamas finales.")
        return False

    print("[capture_and_save] Leyendo kamas finales...")
    kamas_finales = get_kamas()
    print(f"[capture_and_save] Kamas finales leídas: {kamas_finales}")

    print("[capture_and_save] Llamando a agregar_datos para guardar en Excel...")
    ok = agregar_datos(
        objeto_seleccionado=objeto,
        intentos=intentos,
        kamas_iniciales=kamas_iniciales,
        kamas_finales=kamas_finales,
        exito=exito,
        tiempo_medio_intento=tiempo_medio_intento,
        modo_encadenado_activo=modo_encadenado_activo,
        precio_objeto_base=precio_objeto_base,
        precio_venta_objeto_final=precio_venta_objeto_final,
        tipo_exo=tipo_exo
    )
    if ok:
        print("[capture_and_save] Datos guardados correctamente en Excel.")
    else:
        print("[capture_and_save] Error al guardar datos en Excel.")
    return bool(ok)
# ---------------------------------------------------------------------------


def _parse_args():
    p = argparse.ArgumentParser(description="Guardar kamas iniciales / finalizar sesión y guardar en Excel.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("save-init", help="Leer y guardar kamas iniciales para un objeto")
    p_init.add_argument("--obj", required=True, help="Nombre del objeto (key en DB)")

    p_fin = sub.add_parser("finalize", help="Leer kamas finales y guardar sesión en Excel")
    p_fin.add_argument("--obj", required=True, help="Nombre del objeto")
    p_fin.add_argument("--intentos", required=True, type=int, help="Número de intentos realizados en la sesión")
    p_fin.add_argument("--result", required=True, help="Resultado: 'PA' para exito PA o 'FAIL' para fallo (sin runas)")
    p_fin.add_argument("--tiempo", type=float, default=None, help="Tiempo medio por intento (s)")
    p_fin.add_argument("--modo-encadenado", action="store_true", help="Evita pop-ups para precios")
    p_fin.add_argument("--precio-base", type=int, default=None)
    p_fin.add_argument("--precio-venta", type=int, default=None)
    p_fin.add_argument("--tipo-exo", type=str, default=None)
    p_fin.add_argument("--kamas-iniciales", type=int, default=None, help="Opcional: fuerza kamas iniciales en caso de no usar save-init")

    return p.parse_args()


if __name__ == "__main__":
    # Si se llama sin argumentos, ejecutar modo interactivo simplificado que lee kamas y guarda (inventando lo demás)
    if len(sys.argv) == 1:
        print("Modo interactivo simplificado: leer kamas iniciales/finales y guardar en la DB (datos inventados salvo kamas).")
        objeto = input("Objeto (clave en DB) [DemoObjeto]: ").strip() or "DemoObjeto"
        # Valores inventados por defecto (puedes cambiarlos)
        intentos_def = 3
        exito_def = "PA"  # por defecto asumimos PA para demo; el usuario puede cambiar input siguiente
        tiempo_def = 2.0
        modo_enc_def = True
        precio_base_def = 0
        precio_venta_def = 0
        tipo_exo_def = "PA"

        # Preguntar si desea cambiar el resultado por defecto
        res_in = input(f"Resultado por defecto='{exito_def}'. Cambiar? (PA/FAIL) [Enter=PA]: ").strip()
        if res_in:
            exito_def = res_in if res_in.upper() in ("PA", "FAIL") else exito_def

        # Ejecutar captura y guardar (usa valores inventados)
        ok = capture_and_save(
            objeto=objeto,
            intentos=intentos_def,
            exito=exito_def,
            tiempo_medio_intento=tiempo_def,
            modo_encadenado_activo=modo_enc_def,
            precio_objeto_base=precio_base_def,
            precio_venta_objeto_final=precio_venta_def,
            tipo_exo=tipo_exo_def,
            use_store=False
        )
        sys.exit(0 if ok else 2)

    # Si se pasaron argumentos, usar el comportamiento CLI existente
    args = _parse_args()
    if args.cmd == "save-init":
        save_initial_kamas(args.obj)
        sys.exit(0)

    if args.cmd == "finalize":
        # normalizar exito valor que espera agregar_datos
        res = args.result.strip().lower()
        exito_flag = "PA" if res in ("pa", "1", "success", "exito") else 0
        exit_code = finalize_session(
            objeto=args.obj,
            intentos=args.intentos,
            exito=exito_flag,
            tiempo_medio_intento=args.tiempo,
            modo_encadenado_activo=args.modo_encadenado,
            precio_objeto_base=args.precio_base,
            precio_venta_objeto_final=args.precio_venta,
            tipo_exo=args.tipo_exo,
            kamas_iniciales_arg=args.kamas_iniciales
        )
        sys.exit(exit_code)
