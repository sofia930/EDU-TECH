from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
DATASET_PATH = os.path.join(BASE_DIR, 'datos.csv')

# 📌 Clase para gestionar la base de datos
class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.verificar_base_datos()

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def verificar_base_datos(self):
        conn = self.conectar()
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

db_manager = DatabaseManager()  # Instancia de la base de datos

# 📌 Clase Usuario
class Usuario:
    def __init__(self, email, contraseña, nombre, apellido, calificaciones):
        self.email = email.strip().lower()
        self.contraseña = contraseña.strip()
        self.nombre = nombre.strip().title()
        self.apellido = apellido.strip().title()
        self.calificaciones = calificaciones

    def registrar(self):
        conn = db_manager.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (self.email,))
        if cursor.fetchone():
            conn.close()
            return False  # Usuario ya existe

        cursor.execute("""
        INSERT INTO usuarios (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.email, self.contraseña, self.nombre, self.apellido, *self.calificaciones))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def autenticar(email, contraseña):
        conn = db_manager.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, apellido FROM usuarios WHERE email = ? AND contraseña = ?", (email.strip().lower(), contraseña))
        usuario = cursor.fetchone()
        conn.close()
        return usuario

# 📌 Clase para manejar la encuesta
class Encuesta:
    preguntas = [
        {"texto": "Tengo fama de decir lo que pienso claramente y sin rodeos.", "estilo": "Pragmático"},
        {"texto": "Estoy seguro/a de lo que es bueno y malo, lo que está bien y lo que está mal.", "estilo": "Teórico"},
        {"texto": "Muchas veces actúo sin mirar las consecuencias.", "estilo": "Activo"},
        {"texto": "Normalmente trato de resolver los problemas metódicamente y paso a paso.", "estilo": "Teórico"},
        {"texto": "Creo que los formalismos coartan y limitan la actuación libre de las personas.", "estilo": "Activo"},
    ]

    @staticmethod
    def guardar_respuestas(usuario_id, respuestas):
        conn = db_manager.conectar()
        cursor = conn.cursor()
        for i, pregunta in enumerate(Encuesta.preguntas):
            respuesta = respuestas.get(f'pregunta{i}')
            if respuesta:
                cursor.execute("""
                    INSERT INTO respuestas (id_usuario, pregunta, respuesta)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id_usuario, pregunta) 
                    DO UPDATE SET respuesta = excluded.respuesta
                """, (usuario_id, pregunta["texto"], respuesta))

        conn.commit()
        conn.close()

# 📌 Ruta principal corregida
@app.route('/')
def home():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("registro"))

# 📌 Ruta de Registro
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        datos = {
            "email": request.form.get("email"),
            "contraseña": request.form.get("contraseña"),
            "nombre": request.form.get("nombre"),
            "apellido": request.form.get("apellido"),
            "calificaciones": [
                request.form.get("matematicas") or 0,
                request.form.get("historia") or 0,
                request.form.get("fisica") or 0,
                request.form.get("quimica") or 0,
                request.form.get("biologia") or 0,
                request.form.get("ingles") or 0,
                request.form.get("geografia") or 0
            ]
        }

        usuario = Usuario(**datos)
        if not usuario.registrar():
            return render_template("registro.html", error="⚠️ Este email ya está registrado.")

        return redirect(url_for("login"))

    return render_template("registro.html")

# 📌 Ruta de Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        contraseña = request.form["contraseña"]
        usuario = Usuario.autenticar(email, contraseña)

        if usuario:
            session["usuario_id"], session["nombre"], session["apellido"] = usuario
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# 📌 Ruta del Dashboard
@app.route('/dashboard')
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", nombre=session["nombre"], apellido=session["apellido"])

# 📌 Encuesta Corregida
@app.route('/encuesta', methods=['GET', 'POST'])
def encuesta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = db_manager.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas_previas = dict(cursor.fetchall())
    conn.close()

    return render_template("encuesta.html", preguntas=Encuesta.preguntas, respuestas_previas=respuestas_previas)

# 📌 Guardar Respuestas
@app.route('/guardar_respuestas', methods=['POST'])
def guardar_respuestas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    Encuesta.guardar_respuestas(usuario_id, request.form)
    return redirect(url_for("ver_respuestas"))

@app.route("/ver_progreso")
def ver_progreso():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    conn = db_manager.conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = ?", (usuario_id,))
    respuestas = cursor.fetchall()
    
    conn.close()

    return render_template("progreso.html", respuestas=respuestas)


# 📌 Ruta de Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/ver_respuestas')
def ver_respuestas():
    return render_template("ver_respuestas.html")

if __name__ == '__main__':
    app.run(debug=True)
