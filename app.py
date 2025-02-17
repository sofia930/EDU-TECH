from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
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

    # ✅ Crear tabla para almacenar respuestas de la encuesta
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id_respuesta INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER,
        pregunta TEXT NOT NULL,
        respuesta TEXT NOT NULL,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)

    conn.commit()
    conn.close()

app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

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

verificar_base_datos()

# 📌 Clase para calcular rendimiento
class CalculoDeRendimiento:
    @staticmethod
    def obtener_rendimiento(nombre, apellido):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matematicas, historia, fisica, quimica, biologia, ingles, geografia 
            FROM usuarios WHERE nombre = ? AND apellido = ?
        """, (nombre, apellido))
        estudiante_data = cursor.fetchone()
        conn.close()

        if estudiante_data:
            calificaciones = list(estudiante_data)
            promedio = sum(calificaciones) / len(calificaciones)
            return pd.cut([promedio], bins=[0, 70, 80, 90, 100], labels=['Bajo', 'Básico', 'Alto', 'Superior'])[0]
        else:
            return "No hay datos"

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
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip().title()
        apellido = request.form.get("apellido").strip().title()

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

# 📌 Ruta de la encuesta (Después del login)
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

    nombre = session["nombre"]
    apellido = session["apellido"]
    usuario_id = session["usuario_id"]

    # Obtener respuestas de la encuesta
    respuestas = {f'pregunta{i}': request.form.get(f'pregunta{i}') for i in range(len(preguntas))}
    
    # Validar que todas las respuestas estén completas
    if None in respuestas.values():
        return render_template("encuesta.html", preguntas=preguntas, error="⚠️ Debes responder todas las preguntas.")

    # Inicializar los estilos de aprendizaje
    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    # Guardar respuestas en la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for i, pregunta in enumerate(preguntas):
        respuesta = respuestas[f'pregunta{i}']
        estilos[pregunta["estilo"]] += (1 if respuesta == "+" else 0)
        
        # Guardar la respuesta en la tabla respuestas
        cursor.execute("INSERT INTO respuestas (id_usuario, pregunta, respuesta) VALUES (?, ?, ?)",
                       (usuario_id, pregunta["texto"], respuesta))

    conn.commit()
    conn.close()

    # Determinar el estilo predominante
    estilo_predominante = max(estilos, key=estilos.get)

    # 📌 Obtener rendimiento académico del usuario
    rendimiento = CalculoDeRendimiento.obtener_rendimiento(nombre, apellido)

    return render_template('resultado.html', nombre=nombre, apellido=apellido, 
                           estilo=estilo_predominante, rendimiento=rendimiento)

@app.route("/ver_respuestas")
def ver_respuestas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = ?", (session["usuario_id"],))
    respuestas = cursor.fetchall()
    
    conn.close()

    return render_template("ver_respuestas.html", respuestas=respuestas)
# 📌 Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
