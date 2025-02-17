from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"

# 📌 Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'datos.csv')

# 📌 Crear base de datos y tablas si no existen
def verificar_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 📌 Tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        contraseña TEXT NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        matematicas INTEGER,
        historia INTEGER,
        fisica INTEGER,
        quimica INTEGER,
        biologia INTEGER,
        ingles INTEGER,
        geografia INTEGER
    )
    """)

    # 📌 Tabla de respuestas (cada pregunta en una columna)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id_usuario INTEGER PRIMARY KEY,
        {} TEXT,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """.format(", ".join([f'pregunta_{i+1} TEXT' for i in range(80)])))

    conn.commit()
    conn.close()

verificar_base_datos()

# 📌 Definición de preguntas de la encuesta
preguntas = [
    {"texto": f"Pregunta {i+1}: Descripción de la pregunta aquí.", "estilo": "Pragmático" if i % 4 == 0 else "Teórico"} 
    for i in range(80)
]

@app.route('/')
def home():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("registro"))

# 📌 Ruta de registro de usuario
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip()
        apellido = request.form.get("apellido").strip()

        # Obtener calificaciones
        notas = {materia: request.form.get(materia) for materia in ["matematicas", "historia", "fisica", "quimica", "biologia", "ingles", "geografia"]}

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado. Intenta iniciar sesión.")

        # Insertar usuario en SQLite
        cursor.execute("""
            INSERT INTO usuarios (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, contraseña, nombre, apellido, *notas.values()))

        conn.commit()
        conn.close()

        # **Guardar en dataset CSV**
        df = pd.read_csv(DATASET_PATH)
        nueva_fila = pd.DataFrame({"Nombre": [nombre], "Apellido": [apellido], "Email": [email], **notas})
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_csv(DATASET_PATH, index=False)

        return redirect(url_for("login"))

    return render_template("registro.html")

# 📌 Ruta de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        contraseña = request.form["contraseña"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, apellido FROM usuarios WHERE email = ? AND contraseña = ?", (email, contraseña))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["usuario_id"], session["nombre"], session["apellido"] = usuario
            session["email"] = email
            return redirect(url_for("encuesta"))
        return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# 📌 Ruta de encuesta
@app.route('/encuesta', methods=['GET', 'POST'])
def encuesta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener respuestas previas
    cursor.execute(f"SELECT {', '.join([f'pregunta_{i+1}' for i in range(80)])} FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas_guardadas = cursor.fetchone()
    conn.close()

    respuestas_dict = {f'pregunta_{i+1}': respuestas_guardadas[i] if respuestas_guardadas else None for i in range(80)}

    return render_template("encuesta.html", preguntas=preguntas, respuestas=respuestas_dict)

# 📌 Ruta de resultados de la encuesta
@app.route('/resultado', methods=['POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    respuestas = {f'pregunta_{i+1}': request.form.get(f'pregunta_{i}') for i in range(80)}

    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    for i, pregunta in enumerate(preguntas):
        if respuestas.get(f'pregunta_{i+1}') == "+":
            estilos[pregunta["estilo"]] += 1

    # Guardar respuestas en la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ", ".join([f":pregunta_{i+1}" for i in range(80)])
    cursor.execute(f"""
        INSERT INTO respuestas (id_usuario, {', '.join([f'pregunta_{i+1}' for i in range(80)])})
        VALUES (:id_usuario, {placeholders})
        ON CONFLICT(id_usuario) DO UPDATE SET
        {', '.join([f'pregunta_{i+1} = excluded.pregunta_{i+1}' for i in range(80)])}
    """, {"id_usuario": usuario_id, **respuestas})

    conn.commit()
    conn.close()

    estilo_predominante = max(estilos, key=estilos.get)

    return render_template("resultado.html", nombre=session["nombre"], apellido=session["apellido"], estilo=estilo_predominante)

# 📌 Ruta de cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
