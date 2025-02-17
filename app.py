from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
DATASET_PATH = os.path.join(BASE_DIR, 'datos.csv')  # Ubicación del dataset

# 📌 Verificar y crear la base de datos si no existe
def verificar_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id_usuario INTEGER,
        pregunta TEXT NOT NULL,
        respuesta TEXT,
        PRIMARY KEY (id_usuario, pregunta),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)

    conn.commit()
    conn.close()

verificar_base_datos()

# 📌 Preguntas de la encuesta
preguntas = [
    {"texto": "Tengo fama de decir lo que pienso claramente y sin rodeos.", "estilo": "Pragmático"},
    {"texto": "Estoy seguro/a de lo que es bueno y malo, lo que está bien y lo que está mal.", "estilo": "Teórico"},
    {"texto": "Muchas veces actúo sin mirar las consecuencias.", "estilo": "Activo"},
    {"texto": "Normalmente trato de resolver los problemas metódicamente y paso a paso.", "estilo": "Teórico"},
    {"texto": "Creo que los formalismos coartan y limitan la actuación libre de las personas.", "estilo": "Activo"},
]

# 📌 Ruta de registro de estudiante
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip().title()
        apellido = request.form.get("apellido").strip().title()

        matematicas = request.form.get("matematicas")
        historia = request.form.get("historia")
        fisica = request.form.get("fisica")
        quimica = request.form.get("quimica")
        biologia = request.form.get("biologia")
        ingles = request.form.get("ingles")
        geografia = request.form.get("geografia")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado.")

        cursor.execute("""
        INSERT INTO usuarios (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia))

        conn.commit()
        conn.close()

        # Guardar en el dataset CSV
        df = pd.read_csv(DATASET_PATH) if os.path.exists(DATASET_PATH) else pd.DataFrame(columns=[
            "Nombre", "Apellido", "Email", "Matematicas", "Historia", "Fisica", "Quimica", "Biologia", "Ingles", "Geografia"
        ])

        nueva_fila = pd.DataFrame({
            "Nombre": [nombre], "Apellido": [apellido], "Email": [email],
            "Matematicas": [matematicas], "Historia": [historia], "Fisica": [fisica],
            "Quimica": [quimica], "Biologia": [biologia], "Ingles": [ingles], "Geografia": [geografia]
        })

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
            session["usuario_id"] = usuario[0]
            session["nombre"] = usuario[1]
            session["apellido"] = usuario[2]
            return redirect(url_for("encuesta"))

        return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# 📌 Ruta de la encuesta
@app.route('/encuesta', methods=['GET', 'POST'])
def encuesta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas_previas = dict(cursor.fetchall())

    conn.close()

    return render_template("encuesta.html", preguntas=preguntas, respuestas_previas=respuestas_previas)

# 📌 Guardar respuestas
@app.route('/guardar_respuestas', methods=['POST'])
def guardar_respuestas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for i, pregunta in enumerate(preguntas):
        respuesta = request.form.get(f'pregunta{i}')
        if respuesta:
            cursor.execute("""
                INSERT INTO respuestas (id_usuario, pregunta, respuesta)
                VALUES (?, ?, ?)
                ON CONFLICT(id_usuario, pregunta) 
                DO UPDATE SET respuesta = excluded.respuesta
            """, (usuario_id, pregunta["texto"], respuesta))

    conn.commit()
    conn.close()

    return redirect(url_for("ver_progreso"))

# 📌 Ver progreso
@app.route("/ver_progreso")
def ver_progreso():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas = cursor.fetchall()
    
    conn.close()

    return render_template("progreso.html", respuestas=respuestas)

# 📌 Ruta de cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
