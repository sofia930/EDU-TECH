from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset.csv')  # Ruta del dataset

# 📌 Preguntas de la encuesta
preguntas = [
    {"texto": "Tengo fama de decir lo que pienso claramente y sin rodeos.", "estilo": "Pragmático"},
    {"texto": "Estoy seguro/a de lo que es bueno y malo, lo que está bien y lo que está mal.", "estilo": "Teórico"},
    {"texto": "Muchas veces actúo sin mirar las consecuencias.", "estilo": "Activo"},
    {"texto": "Normalmente trato de resolver los problemas metódicamente y paso a paso.", "estilo": "Teórico"},
    {"texto": "Creo que los formalismos coartan y limitan la actuación libre de las personas.", "estilo": "Activo"},
]

# 📌 Verificar si la base de datos existe y crearla si no
def verificar_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla de usuarios si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        contraseña TEXT NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

verificar_base_datos()

# 📌 Ruta de registro de estudiante
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip().title()
        apellido = request.form.get("apellido").strip().title()

        # 📌 1️⃣ Verificar si el email ya está en el dataset
        try:
            df = pd.read_csv(DATASET_PATH, encoding="utf-8")
            if email in df["email"].values:
                return render_template("registro.html", error="⚠️ Este email ya está registrado en el dataset.")
        except FileNotFoundError:
            # Si el archivo no existe, lo creamos después
            df = pd.DataFrame(columns=["email", "nombre", "apellido", "contraseña"])

        # 📌 2️⃣ Conectar con SQLite y verificar si el usuario ya está registrado
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado en la base de datos.")

        # 📌 3️⃣ Insertar el usuario en la base de datos
        cursor.execute("INSERT INTO usuarios (email, contraseña, nombre, apellido) VALUES (?, ?, ?, ?)", 
                       (email, contraseña, nombre, apellido))
        conn.commit()
        conn.close()

        # 📌 4️⃣ Agregar el usuario al dataset
        nuevo_registro = pd.DataFrame([[email, nombre, apellido, contraseña]], 
                                      columns=["email", "nombre", "apellido", "contraseña"])
        df = pd.concat([df, nuevo_registro], ignore_index=True)
        df.to_csv(DATASET_PATH, index=False, encoding="utf-8")

        return redirect(url_for("login"))  # ✅ Redirige al login

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
            session["email"] = email  
            return redirect(url_for("dashboard"))  # ✅ Redirige al Dashboard
        else:
            return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# 📌 Ruta del Dashboard
@app.route('/dashboard')
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    nombre = session["nombre"]
    apellido = session["apellido"]
    
    return render_template("dashboard.html", nombre=nombre, apellido=apellido)

# 📌 Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
