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
        apellido TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id_respuesta INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER,
        pregunta TEXT,
        respuesta TEXT,
        FOREIGN KEY(id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)
    
    conn.commit()
    conn.close()

verificar_base_datos()

@app.route('/')
def home():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))  # Si ya está logueado, redirige al dashboard
    return redirect(url_for("registro"))  # Si no está logueado, lo lleva a registro
# 📌 Ruta de registro

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        contraseña = request.form.get("contraseña").strip()
        nombre = request.form.get("nombre").strip()
        apellido = request.form.get("apellido").strip()

        # Obtener las calificaciones
        matematicas = request.form.get("matematicas")
        historia = request.form.get("historia")
        fisica = request.form.get("fisica")
        quimica = request.form.get("quimica")
        biologia = request.form.get("biologia")
        ingles = request.form.get("ingles")
        geografia = request.form.get("geografia")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            conn.close()
            return render_template("registro.html", error="⚠️ Este email ya está registrado. Intenta iniciar sesión.")

        # Insertar el nuevo usuario en SQLite
        cursor.execute("""
            INSERT INTO usuarios (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, contraseña, nombre, apellido, matematicas, historia, fisica, quimica, biologia, ingles, geografia))

        conn.commit()
        conn.close()

        # **Guardar en el dataset CSV**
        df = pd.read_csv(DATASET_PATH)

        # Crear una nueva fila con los datos
        nueva_fila = pd.DataFrame({
            "Nombre": [nombre],
            "Apellido": [apellido],
            "Email": [email],
            "Matematicas": [matematicas],
            "Historia": [historia],
            "Fisica": [fisica],
            "Quimica": [quimica],
            "Biologia": [biologia],
            "Ingles": [ingles],
            "Geografia": [geografia]
        })

        # Agregar la fila al dataset
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_csv(DATASET_PATH, index=False)

        return redirect(url_for("login"))  # Redirigir al login después de registrarse

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

# 📌 Ruta del Dashboard
@app.route('/dashboard')
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  # 🔹 Si no hay sesión, redirige a login

    nombre = session["nombre"]
    apellido = session["apellido"]

    return render_template("dashboard.html", nombre=nombre, apellido=apellido)

# 📌 Ruta de la encuesta
@app.route('/encuesta', methods=['GET', 'POST'])
def encuesta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        df = pd.read_csv(DATASET_PATH)

        # Buscar al usuario en el dataset
        index = df[(df['Nombre'].str.lower() == session["nombre"].lower()) & 
                   (df['Apellido'].str.lower() == session["apellido"].lower())].index

        if not index.empty:
            for i, pregunta in enumerate(preguntas):
                df.at[index[0], f"Pregunta_{i+1}"] = request.form.get(f'pregunta{i}')

        df.to_csv(DATASET_PATH, index=False)

        return redirect(url_for("resultado"))

    return render_template("encuesta.html", preguntas=preguntas)

@app.route('/resultado', methods=['POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  # Redirigir si el usuario no ha iniciado sesión

    # Obtener respuestas de la encuesta
    respuestas = {f'pregunta{i}': request.form.get(f'pregunta{i}') for i in range(len(preguntas))}

    # Validar que todas las respuestas estén completas
    if None in respuestas.values():
        return render_template("encuesta.html", preguntas=preguntas, error="⚠️ Debes responder todas las preguntas.")

    # Inicializar los estilos de aprendizaje
    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    # Contar las respuestas por estilo
    for i in range(len(preguntas)):  
        respuesta = respuestas.get(f'pregunta{i}')
        if respuesta == '+':
            estilos[preguntas[i]['estilo']] += 1  

    # Determinar el estilo predominante
    estilo_predominante = max(estilos, key=estilos.get)

   
    # **📌 Obtener rendimiento académico del usuario desde la BD**
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT matematicas, historia, fisica, quimica, biologia, ingles, geografia
        FROM usuarios WHERE id_usuario = ?""", (session["usuario_id"],))
    
    rendimiento = cursor.fetchone()
    conn.close()

    if rendimiento:
        materias = ["Matemáticas", "Historia", "Física", "Química", "Biología", "Inglés", "Geografía"]
        rendimiento_dict = {materias[i]: rendimiento[i] for i in range(len(materias))}
    else:
        rendimiento_dict = {}

    return render_template('resultado.html', nombre=session["nombre"], apellido=session["apellido"], 
                           estilo=estilo_predominante, rendimiento=rendimiento_dict)
# 📌 Ruta de cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/ver_respuestas')
def ver_respuestas():
    return render_template("ver_respuestas.html")

if __name__ == '__main__':
    app.run(debug=True)
