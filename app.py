from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'datos.csv')

# 📌 Preguntas de la encuesta
preguntas = [
    {"texto": "Tengo fama de decir lo que pienso claramente y sin rodeos.", "estilo": "Pragmático"},
    {"texto": "Estoy seguro/a de lo que es bueno y malo, lo que está bien y lo que está mal.", "estilo": "Teórico"},
    {"texto": "Muchas veces actúo sin mirar las consecuencias.", "estilo": "Activo"},
    {"texto": "Normalmente trato de resolver los problemas metódicamente y paso a paso.", "estilo": "Teórico"},
    {"texto": "Creo que los formalismos coartan y limitan la actuación libre de las personas.", "estilo": "Activo"},
]

# 📌 Verificar y crear base de datos

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
        id_usuario INTEGER PRIMARY KEY,
        pregunta_1 TEXT,
        pregunta_2 TEXT,
        pregunta_3 TEXT,
        pregunta_4 TEXT,
        pregunta_5 TEXT,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)
    
    conn.commit()
    conn.close()

verificar_base_datos()

# 📌 Ruta de registro de usuario
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip()
        apellido = request.form.get("apellido").strip()
        
        # Obtener calificaciones
        notas = {
            "matematicas": request.form.get("matematicas"),
            "historia": request.form.get("historia"),
            "fisica": request.form.get("fisica"),
            "quimica": request.form.get("quimica"),
            "biologia": request.form.get("biologia"),
            "ingles": request.form.get("ingles"),
            "geografia": request.form.get("geografia"),
        }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado. Intenta iniciar sesión.")

        cursor.execute("""
            INSERT INTO usuarios (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, contraseña, nombre, apellido, *notas.values()))
        conn.commit()
        conn.close()

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
            session["usuario_id"] = usuario[0]
            session["nombre"] = usuario[1]
            session["apellido"] = usuario[2]
            return redirect(url_for("encuesta"))
        else:
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
    cursor.execute("SELECT pregunta_1, pregunta_2, pregunta_3, pregunta_4, pregunta_5 FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas_guardadas = cursor.fetchone()
    conn.close()

    respuestas_dict = {f'pregunta_{i+1}': respuesta for i, respuesta in enumerate(respuestas_guardadas)} if respuestas_guardadas else {}
    
    return render_template("encuesta.html", preguntas=preguntas, respuestas=respuestas_dict)

# 📌 Ruta de resultados
@app.route('/resultado', methods=['POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    respuestas = {f'pregunta_{i+1}': request.form.get(f'pregunta{i}') for i in range(len(preguntas))}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO respuestas (id_usuario, pregunta_1, pregunta_2, pregunta_3, pregunta_4, pregunta_5)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (usuario_id, *respuestas.values()))
    conn.commit()
    conn.close()
    return redirect(url_for("ver_respuestas"))

if __name__ == '__main__':
    app.run(debug=True)
