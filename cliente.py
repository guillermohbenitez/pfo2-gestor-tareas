"""
PFO 2 - Cliente de consola para la API de Gestión de Tareas.
Requiere que servidor.py esté corriendo en http://127.0.0.1:5000
"""
import getpass

import requests

BASE_URL = "http://127.0.0.1:5000"


def pedir_credenciales():
    usuario = input("Usuario: ").strip()
    password = getpass.getpass("Contraseña: ")
    return usuario, password


def registrar():
    usuario, password = pedir_credenciales()
    r = requests.post(f"{BASE_URL}/registro", json={"usuario": usuario, "contraseña": password})
    print(f"[{r.status_code}] {r.json()}")


def iniciar_sesion():
    usuario, password = pedir_credenciales()
    r = requests.post(f"{BASE_URL}/login", json={"usuario": usuario, "contraseña": password})
    print(f"[{r.status_code}] {r.json()}")
    if r.status_code == 200:
        return usuario, password
    return None


def ver_tareas(sesion):
    if not sesion:
        print("Primero tenés que iniciar sesión.")
        return
    r = requests.get(f"{BASE_URL}/tareas", auth=sesion)
    print(f"[{r.status_code}]")
    print(r.text)


def main():
    sesion = None
    while True:
        print("\n=== Gestor de Tareas ===")
        print("1. Registrarse\n2. Iniciar sesión\n3. Ver tareas\n4. Salir")
        op = input("Opción: ").strip()
        try:
            if op == "1":
                registrar()
            elif op == "2":
                sesion = iniciar_sesion() or sesion
            elif op == "3":
                ver_tareas(sesion)
            elif op == "4":
                break
            else:
                print("Opción inválida.")
        except requests.ConnectionError:
            print("No se pudo conectar con el servidor. ¿Está corriendo servidor.py?")


if __name__ == "__main__":
    main()
