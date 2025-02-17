from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"  # Clave secreta para sesiones

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')  # Ruta de la base de datos
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'datos.csv')  # Ruta del dataset CSV

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
    conn.commit()
    conn.close()

# 📌 Inicializar la base de datos
verificar_base_datos()

# 📌 Función para guardar estudiantes en el CSV
def guardar_en_csv(nombre, apellido, email):
    datos_nuevo = pd.DataFrame([[nombre, apellido, email]], columns=["Nombre", "Apellido", "Email"])
    if os.path.exists(DATASET_PATH):
        datos_existentes = pd.read_csv(DATASET_PATH)
        datos_actualizados = pd.concat([datos_existentes, datos_nuevo], ignore_index=True)
    else:
        datos_actualizados = datos_nuevo
    datos_actualizados.to_csv(DATASET_PATH, index=False)

# 📌 Ruta principal (Redirige al registro si no ha iniciado sesión)
@app.route('/')
def home():
    if "usuario_id" in session:
        return redirect(url_for("encuesta"))
    return redirect(url_for("registro"))

# 📌 Ruta de registro de estudiante
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre").strip()
        apellido = request.form.get("apellido").strip()
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado. Intenta iniciar sesión.")
        
        cursor.execute("INSERT INTO usuarios (email, contraseña, nombre, apellido) VALUES (?, ?, ?, ?)", 
                       (email, contraseña, nombre, apellido))
        conn.commit()
        conn.close()
        
        guardar_en_csv(nombre, apellido, email)  # Guardar en CSV
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
            session["email"] = email
            return redirect(url_for("encuesta"))
        else:
            return render_template("login.html", error="⚠️ Email o contraseña incorrectos")
    
    return render_template("login.html")

# 📌 Ruta de la encuesta
@app.route('/encuesta', methods=['GET', 'POST'])
def encuesta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        return redirect(url_for("resultado"))
    return render_template("encuesta.html", preguntas=preguntas)

# 📌 Ruta de resultados de la encuesta
@app.route('/resultado', methods=['POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    respuestas = {f'pregunta{i}': request.form.get(f'pregunta{i}') for i in range(len(preguntas))}
    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}
    for i in range(len(preguntas)):
        if respuestas.get(f'pregunta{i}') == '+':
            estilos[preguntas[i]['estilo']] += 1  
    estilo_predominante = max(estilos, key=estilos.get)
    return render_template('resultado.html', nombre=session["nombre"], apellido=session["apellido"], estilo=estilo_predominante)

# 📌 Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
