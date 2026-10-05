"""
PFO 2 - Sistema de Gestión de Tareas con API y Base de Datos
Servidor: API REST con Flask + SQLite + contraseñas hasheadas.
"""
import sqlite3
from functools import wraps

from flask import Flask, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.json.ensure_ascii = False  # para que "contraseña" y acentos se vean bien en JSON
DB_PATH = "tareas.db"


# ---------------------------------------------------------------- Base de datos
def get_db():
    """Devuelve una conexión a SQLite reutilizable durante la petición."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si no existen."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario       TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL
            )
            """
        )


# ------------------------------------------------------------------- Utilidades
def leer_credenciales():
    """Extrae usuario y contraseña del cuerpo JSON. Acepta 'contraseña' o 'contrasena'."""
    datos = request.get_json(silent=True) or {}
    usuario = (datos.get("usuario") or "").strip()
    password = datos.get("contraseña") or datos.get("contrasena") or ""
    return usuario, password


def verificar_usuario(usuario, password):
    fila = get_db().execute(
        "SELECT password_hash FROM usuarios WHERE usuario = ?", (usuario,)
    ).fetchone()
    return fila is not None and check_password_hash(fila["password_hash"], password)


def requiere_auth(f):
    """Protege un endpoint con autenticación HTTP Basic contra la base de datos."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        auth = request.authorization
        if not auth or not verificar_usuario(auth.username, auth.password):
            return (
                jsonify({"error": "Credenciales inválidas o ausentes"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Tareas"'},
            )
        g.usuario = auth.username
        return f(*args, **kwargs)
    return envoltura


# -------------------------------------------------------------------- Endpoints
@app.post("/registro")
def registro():
    usuario, password = leer_credenciales()
    if not usuario or not password:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'"}), 400

    try:
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
            (usuario, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya existe"}), 409

    return jsonify({"mensaje": f"Usuario '{usuario}' registrado correctamente"}), 201


@app.post("/login")
def login():
    usuario, password = leer_credenciales()
    if not usuario or not password:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'"}), 400

    if not verificar_usuario(usuario, password):
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    return jsonify({"mensaje": f"Inicio de sesión exitoso. Bienvenido/a, {usuario}"}), 200


@app.get("/tareas")
@requiere_auth
def tareas():
    usuario = g.usuario
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Gestor de Tareas</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background:#f4f6f8; display:flex;
           justify-content:center; align-items:center; height:100vh; margin:0; }}
    .card {{ background:#fff; padding:2rem 3rem; border-radius:12px;
             box-shadow:0 4px 16px rgba(0,0,0,.08); text-align:center; }}
    h1 {{ color:#2c3e50; margin-top:0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>¡Bienvenido/a, {usuario}!</h1>
    <p>Accediste correctamente al Sistema de Gestión de Tareas.</p>
  </div>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
