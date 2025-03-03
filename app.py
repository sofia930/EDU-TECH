from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
import os
import pandas as pd
import numpy as np 
import re
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
from psycopg2 import pool 

app = Flask(__name__)
app.secret_key = "supersecreto"

# Rutas de archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = "postgresql://sofia:12345@localhost/mi_base_de_datos" 
db_pool = pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL) 
DATASET_PATH = r"C:\Users\sofia\Downloads\codigoFlask\dataset\datos.csv"
MODEL_PATH = os.path.join(BASE_DIR, 'modelo_notas.pkl')

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    if conn and hasattr(conn, 'closed') and not conn.closed:
        db_pool.putconn(conn)

def verificar_base_datos():
    conn = get_db_connection()  # Usa la nueva conexión
    cursor = conn.cursor() 
    
    # Crear tabla de usuarios (ya está en tu código)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        ciclo_1 REAL,
        ciclo_2 REAL,
        ciclo_3 REAL,
        estilo TEXT,
        Apss_usadas TEXT        
    )
    """)

    # CREAR LA TABLA RESPUESTAS (Asegurar que existe)
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
    release_db_connection(conn)


# Preguntas de la encuesta
preguntas =  [
            {"texto": "1. Tengo fama de decir lo que pienso claramente y sin rodeos.", "estilo": "Pragmático"},
            {"texto": "2. Estoy seguro/a de lo que es bueno y malo, lo que está bien y lo que está mal.", "estilo": "Teórico"},
            {"texto": "3. Muchas veces actúo sin mirar las consecuencias.", "estilo": "Activo"},
            {"texto": "4. Normalmente trato de resolver los problemas metódicamente y paso a paso.", "estilo": "Teórico"},
            {"texto": "5. Creo que los formalismos coartan y limitan la actuación libre de las personas.", "estilo": "Activo"},
            {"texto": "6. Me interesa saber cuáles son los sistemas de valores de los demás y con qué criterios actúan.", "estilo": "Teórico"},
            {"texto": "7. Pienso que el actuar intuitivamente puede ser siempre tan válido como actuar reflexivamente.", "estilo": "Activo"},
            {"texto": "8. Creo que lo más importante es que las cosas funcionen.", "estilo": "Pragmático"},
            {"texto": "9. Procuro estar al tanto de lo que ocurre aquí y ahora.", "estilo": "Activo"},
            {"texto": "10. Disfruto cuando tengo tiempo para preparar mi trabajo y realizarlo a conciencia.", "estilo": "Reflexivo"},
            {"texto": "11. Estoy a gusto siguiendo un orden en las comidas, en el estudio, haciendo ejercicio regularmente.", "estilo": "Teórico"},
            {"texto": "12. Cuando escucho una nueva idea, enseguida comienzo a pensar cómo ponerla en práctica.", "estilo": "Pragmático"},
            {"texto": "13. Prefiero las ideas originales y novedosas aunque no sean prácticas.", "estilo": "Activo"},
            {"texto": "14. Admito y me ajusto a las normas sólo si me sirven para lograr mis objetivos.", "estilo": "Pragmático"},
            {"texto": "15. Normalmente encajo bien con personas reflexivas, y me cuesta sintonizar con personas demasiado espontáneas e imprevisibles.", "estilo": "Teórico"},
            {"texto": "16. Escucho con más frecuencia que hablo.", "estilo": "Reflexivo"},
            {"texto": "17. Prefiero las cosas estructuradas a las desordenadas.", "estilo": "Teórico"},
            {"texto": "18. Cuando poseo cualquier información, trato de interpretarla bien antes de manifestar alguna conclusión.", "estilo": "Reflexivo"},
            {"texto": "19. Antes de hacer algo, estudio con cuidado sus ventajas e inconvenientes.", "estilo": "Reflexivo"},
            {"texto": "20. Me entusiasmo con el reto de hacer algo nuevo y diferente.", "estilo": "Activo"},
            {"texto": "21. Casi siempre procuro ser coherente con mis criterios y sistemas de valores. Tengo principios y los sigo.", "estilo": "Teórico"},
            {"texto": "22. Cuando hay una discusión, no me gusta ir con rodeos.", "estilo": "Pragmático"},
            {"texto": "23. Me disgusta implicarme afectivamente en mi ambiente de trabajo. Prefiero mantener relaciones distantes.", "estilo": "Teórico"},
            {"texto": "24. Me gustan más las personas realistas y concretas que las teóricas.", "estilo": "Pragmático"},
            {"texto": "25. Me cuesta ser creativo/a, romper estructuras.", "estilo": "Teórico"},
            {"texto": "26. Me siento a gusto con personas espontáneas y divertidas.", "estilo": "Activo"},
            {"texto": "27. La mayoría de las veces expreso abiertamente cómo me siento.", "estilo": "Activo"},
            {"texto": "28. Me gusta analizar y dar vueltas a las cosas.", "estilo": "Reflexivo"},
            {"texto": "29. Me molesta que la gente no se tome en serio las cosas.", "estilo": "Teórico"},
            {"texto": "30. Me atrae experimentar y practicar las últimas técnicas y novedades.", "estilo": "Pragmático"},
            {"texto": "31. Soy cauteloso/a a la hora de sacar conclusiones.", "estilo": "Reflexivo"},
            {"texto": "32. Prefiero contar con el mayor número de fuentes de información. Cuantos más datos reúna para reflexionar, mejor.", "estilo": "Reflexivo"},
            {"texto": "33. Tiendo a ser perfeccionista.", "estilo": "Teórico"},
            {"texto": "34. Prefiero oír las opiniones de los demás antes de exponer la mía.", "estilo": "Reflexivo"},
            {"texto": "35. Me gusta afrontar la vida espontáneamente y no tener que planificar todo previamente.", "estilo": "Activo"},
            {"texto": "36. En las discusiones, me gusta observar cómo actúan los demás participantes.", "estilo": "Reflexivo"},
            {"texto": "37. Me siento incómodo/a con las personas calladas y demasiado analíticas.", "estilo": "Activo"},
            {"texto": "38. Juzgo con frecuencia las ideas de los demás por su valor práctico.", "estilo": "Pragmático"},
            {"texto": "39. Me agobio si me obligan a acelerar mucho el trabajo para cumplir un plazo.", "estilo": "Reflexivo"},
            {"texto": "40. En las reuniones apoyo las ideas prácticas y realistas.", "estilo": "Pragmático"},
            {"texto": "41. Es mejor gozar del momento presente que deleitarse pensando en el pasado o en el futuro.", "estilo": "Activo"},
            {"texto": "42. Me molestan las personas que siempre desean apresurar las cosas.", "estilo": "Reflexivo"},
            {"texto": "43. Aporto ideas nuevas y espontáneas en los grupos de discusión.", "estilo": "Activo"},
            {"texto": "44. Pienso que son más consistentes las decisiones fundamentadas en un minucioso análisis que las basadas en la intuición.", "estilo": "Reflexivo"},
            {"texto": "45. Detecto frecuentemente la inconsistencia y puntos débiles en las argumentaciones de los demás.", "estilo": "Teórico"},
            {"texto": "46. Creo que es preciso saltarse las normas muchas más veces que cumplirlas.", "estilo": "Activo"},
            {"texto": "47. A menudo caigo en la cuenta de otras formas mejores y más prácticas de hacer las cosas.", "estilo": "Pragmático"},
            {"texto": "48. En conjunto hablo más que escucho.", "estilo": "Activo"},
            {"texto": "49. Prefiero distanciarme de los hechos y observarlos desde otras perspectivas.", "estilo": "Reflexivo"},
            {"texto": "50. Estoy convencido/a que debe imponerse la lógica y el razonamiento.", "estilo": "Teórico"},
            {"texto": "51. Me gusta buscar nuevas experiencias.", "estilo": "Activo"},
            {"texto": "52. Me gusta experimentar y aplicar las cosas.", "estilo": "Pragmático"},
            {"texto": "53. Pienso que debemos llegar pronto al grano, al meollo de los temas.", "estilo": "Pragmático"},
            {"texto": "54. Siempre trato de conseguir conclusiones e ideas claras.", "estilo": "Teórico"},
            {"texto": "55. Prefiero discutir cuestiones concretas y no perder el tiempo con pláticas superficiales.", "estilo": "Reflexivo"},
            {"texto": "56. Me impaciento cuando me dan explicaciones irrelevantes e incoherentes.", "estilo": "Pragmático"},
            {"texto": "57. Compruebo antes si las cosas funcionan realmente.", "estilo": "Pragmático"},
            {"texto": "58. Hago varios borradores antes de la redacción definitiva de un trabajo.", "estilo": "Reflexivo"},
            {"texto": "59. Soy consciente de que en las discusiones ayudo a mantener a los demás centrados en el tema, evitando divagaciones.", "estilo": "Pragmático"},
            {"texto": "60. Observo que, con frecuencia, soy uno/a de los/as más objetivos/as y desapasionados/as en las discusiones.", "estilo": "Teórico"},
            {"texto": "61. Cuando algo va mal, le quito importancia y trato de hacerlo mejor.", "estilo": "Activo"},
            {"texto": "62. Rechazo ideas originales y espontáneas si no las veo prácticas.", "estilo": "Pragmático"},
            {"texto": "63. Me gusta sopesar diversas alternativas antes de tomar una decisión.", "estilo": "Reflexivo"},
            {"texto": "64. Con frecuencia miro hacia delante para prever el futuro.", "estilo": "Teórico"},
            {"texto": "65. En los debates y discusiones prefiero desempeñar un papel secundario antes que ser el/la líder o el/la que más participa.", "estilo": "Reflexivo"},
            {"texto": "66. Me molestan las personas que no actúan con lógica.", "estilo": "Teórico"},
            {"texto": "67. Me resulta incómodo tener que planificar y prever las cosas.", "estilo": "Activo"},
            {"texto": "68. Creo que el fin justifica los medios en muchos casos.", "estilo": "Pragmático"},
            {"texto": "69. Suelo reflexionar sobre los asuntos y problemas.", "estilo": "Reflexivo"},
            {"texto": "70. El trabajar a conciencia me llena de satisfacción y orgullo.", "estilo": "Reflexivo"},
            {"texto": "71. Ante los acontecimientos trato de descubrir los principios y teorías en que se basan.", "estilo": "Teórico"},
            {"texto": "72. Con tal de conseguir el objetivo que pretendo soy capaz de herir sentimientos ajenos.", "estilo": "Pragmático"},
            {"texto": "73. No me importa hacer todo lo necesario para que sea efectivo mi trabajo.", "estilo": "Pragmático"},
            {"texto": "74. Con frecuencia soy una de las personas que más anima las fiestas.", "estilo": "Activo"},
            {"texto": "75. Me aburro enseguida con el trabajo metódico y minucioso.", "estilo": "Activo"},
            {"texto": "76. La gente con frecuencia cree que soy poco sensible a sus sentimientos.", "estilo": "Pragmático"},
            {"texto": "77. Suelo dejarme llevar por mis intuiciones.", "estilo": "Activo"},
            {"texto": "78. Si trabajo en grupo procuro que se siga un método y un orden.", "estilo": "Teórico"},
            {"texto": "79. Con frecuencia me interesa averiguar lo que piensa la gente.", "estilo": "Reflexivo"},
            {"texto": "80. Esquivo los temas subjetivos, ambiguos y poco claros.", "estilo": "Pragmático"},
            ]

class CalculoDeRendimiento:
    @staticmethod
    def obtener_rendimiento(nombre, apellido):
        conn =  get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ciclo_1, ciclo_2, ciclo_3
            FROM usuarios WHERE nombre = %s AND apellido = %s
        """, (nombre, apellido))
        rendimiento = cursor.fetchone()
        release_db_connection(conn)

        if rendimiento:
            notas = [nota for nota in rendimiento if nota is not None]
            if notas:
                promedio = sum(notas) / len(notas)
                tipo_rendimiento = pd.cut([promedio], bins=[-float("inf"), 5.99, 9.99, 10.99, 12.99, 13.99, 20], labels=['Reprobado (D-)', 'Desaprobado (D)', 'Aprobado (C)', 'Bueno (B)', 'Muy Bueno (A)', 'Excelente (A+)'])[0]
                return {
                    "promedio": round(promedio, 2),
                    "tipo_rendimiento": tipo_rendimiento
                }
        return {"promedio": "N/A", "tipo_rendimiento": "Sin datos"}
    
class HerramientasEducativas:
    herramientas = [
        {"nombre": "Sololearn: Es una aplicación y plataforma web que sirve para aprender a programar.", "tipo_app": "Activo"},
        {"nombre": "Duolingo: Es una aplicación gamificada para aprender idiomas con ejercicios interactivos.", "tipo_app": "Activo"},
        {"nombre": "Evernote: Es una aplicación para tomar notas, organizar información y gestionar tareas.", "tipo_app": "Reflexivo"},
        {"nombre": "MindMeister: Es una aplicación para crear mapas mentales y organizar ideas visualmente.", "tipo_app": "Reflexivo"},
        {"nombre": "Khan Academy: Es una plataforma educativa que te ayudará con cursos de matemáticas, ciencias y otros temas, con videos y ejercicios.", "tipo_app": "Teórico"},
        {"nombre": "Wolfram Alpha: Es un Motor de conocimiento computacional que resuelve ecuaciones y responde preguntas científicas.", "tipo_app": "Teórico"},
        {"nombre": "PhET Interactive Simulations: Es una app que realiza simulaciones interactivas para entender conceptos de matemáticas y ciencias.", "tipo_app": "Pragmático"},
        {"nombre": "Virtual ChemLab: Es una app que muestra laboratorio de química virtual para experimentación en un entorno seguro.", "tipo_app": "Pragmático"},
        {"nombre": "Photomath: Te ayudará a resolver problemas matemáticos escaneando con la cámara y muestra paso a paso la solución.", "tipo_app": "Pragmático"},
        {"nombre": "Mathway: Es una calculadora avanzada que resuelve problemas matemáticos y algebraicos con explicaciones.", "tipo_app": "Pragmático"},
        {"nombre": "Demos graphing calculator: Es una calculadora gráfica avanzada para visualizar ecuaciones y funciones matemáticas.", "tipo_app": "Activo"},
        {"nombre": "Periodic tablet: Es una app que muestra una tabla periódica interactiva con propiedades de los elementos.", "tipo_app": "Reflexivo"},
        {"nombre": "ChemCrafter: Es un juego educativo que permite experimentar con reacciones químicas virtuales.", "tipo_app": "Activo"},
        {"nombre": "Chemistry dictionary: Es un diccionario con términos y definiciones de química.", "tipo_app": "Teórico"},
        {"nombre": "Chemistry helper: Es una aplicación para cálculos y referencias en química.", "tipo_app": "Teórico"},
        {"nombre": "MEL Chemistry: Es una plataforma con experiencias de química en realidad aumentada y videos educativos.", "tipo_app": "Activo"},
        {"nombre": "Physics Toolbox: Es una app donde puedes encontrar un conjunto de herramientas para mediciones físicas usando sensores del móvil.\n", "tipo_app": "Activo"},
        {"nombre": "Physics Calculator: Es una app donde puedes usar una calculadora con fórmulas físicas para resolver problemas.", "tipo_app": "Activo"},
        {"nombre": "PHYWIZ: Es una app que te proporciona un asistente de física que resuelve problemas y explica conceptos.", "tipo_app": "Teórico"},
        {"nombre": "Fizyka: Es una aplicación educativa sobre física con simulaciones y explicaciones.", "tipo_app": "Teórico"},
        {"nombre": "Coursera: Es una plataforma con cursos en línea de universidades y empresas reconocidas.", "tipo_app": "Reflexivo"},
        {"nombre": "TED: Es una aplicación con charlas inspiradoras de expertos en diversos campos.", "tipo_app": "Reflexivo"},
        {"nombre": "GeoGebra: Es una herramienta interactiva para álgebra, geometría, cálculo y estadística.", "tipo_app": "Activo"},
        {"nombre": "Algebrator: Es una app que ayuda a resolver ecuaciones algebraicas con explicaciones detalladas.", "tipo_app": "Pragmático"},
        {"nombre": "Chemcollective: Es una app en donde puedes usar herramientas y simulaciones de química para la educación.", "tipo_app": "Reflexivo"},
        {"nombre": "Rosetta Stone: Es una aplicación que usa un método de aprendizaje de idiomas basado en la inmersión.", "tipo_app": "Pragmático"},
        {"nombre": "Babbel: Es una plataforma de aprendizaje de idiomas con cursos estructurados y lecciones interactivas.", "tipo_app": "Pragmático"},
        {"nombre": "Memrise: Es una plataforma de aprendizaje de idiomas con actividades dinamicas y juegos.", "tipo_app": "Activo"},
        {"nombre": "CodeCombat: Es una plataforma para aprender a programar con un enfoque gamificado tipo RPG.", "tipo_app": "Activo"},
        {"nombre": "Brilliant: Es una plataforma interactiva de aprendizaje de mátematica, ciencias y lógica.", "tipo_app": "Pragmatico"},
        {"nombre": "Todoist: Aplicación de gestión de tareas y organización del tiempo.", "tipo_app": "Pragmatico"},
        {"nombre": "Grammarly: Es un corrector gramatical avanzado para mejorar escritura en inglés.", "tipo_app": "Pragmatico"},
        {"nombre": "MyStudyLife: Planificador académico para gestionar tareas, exámenes y horarios.", "tipo_app": "Pragmatico"},
        {"nombre": "Desmos Scientific Calculator: Calculadora científica avanzada para resolver ecuaciones complejas.", "tipo_app": "Pragmatico"},
        {"nombre": "Microsoft Math Solver: Resuelve problemas matemáticos con explicaciones paso a paso.", "tipo_app": "Pragmatico"},
        {"nombre": "GoodNotes: Aplicación para tomar notas digitales organizadas y estructuradas.", "tipo_app": "Reflexivo"},
        {"nombre": "Notion: Herramienta de productividad para organizar proyectos y aprendizaje.", "tipo_app": "Reflexivo"},
        {"nombre": "AnkiDroid: Sistema de tarjetas de memoria para repasar conceptos a largo plazo.", "tipo_app": "Reflexivo"},
        {"nombre": "Coursera: Cursos en línea con contenido detallado y enfoque académico estructurado.", "tipo_app": "Reflexivo"},
        {"nombre": "Google Keep: Aplicación ligera para tomar notas rápidas y estructurarlas en categorías.", "tipo_app": "Reflexivo"},
        {"nombre": "Wolfram Alpha: Motor de búsqueda computacional que resuelve ecuaciones y problemas científicos.", "tipo_app": "Teorico"},
        {"nombre": "Physics Toolbox Suite: Aplicación con herramientas avanzadas para experimentos científicos.", "tipo_app": "Teorico"},
        {"nombre": "Stanford Online: Acceso a material educativo de la Universidad de Stanford.", "tipo_app": "Teorico"},
        {"nombre": "EdX: Plataforma de aprendizaje con cursos universitarios en ciencias y tecnología.", "tipo_app": "Teorico"},
        {"nombre": "MIT OpenCourseWare:Cursos gratuitos del MIT con contenido académico riguroso.", "tipo_app": "Teorico"},
        {"nombre": "Lightbot: Juego educativo que enseña lógica de programación de forma visual.", "tipo_app": "Activo"},
        {"nombre": "Todoist: Aplicación de gestión de tareas y organización del tiempo.", "tipo_app": "Reflexivo"},
        ]
    
    @classmethod
    def obtener_herramientas_recomendadas(cls, estilo):
        return [h["nombre"].replace("\n", "").strip() for h in cls.herramientas if h["tipo_app"] == estilo]

# Agregar una ruta en Flask para que la predicción se muestre en el HTML


# Ruta principal (Muestra la bienvenida)
@app.route('/')
def home():
    return render_template("bienvenida.html")  

def home1():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))  # Si ya está logueado, redirige al dashboard(panel)
    return redirect(url_for("registro"))

# Función para guardar en CSV
def guardar_en_csv(nombre, apellido, email, ciclo_1, ciclo_2, ciclo_3, Apps_usadas):
    print("🚀 Ejecutando guardar_en_csv()...")  # Debug

    # Si el archivo no existe, crearlo con encabezados
    if not os.path.exists(DATASET_PATH):
        df = pd.DataFrame(columns=["Nombre", "Apellido", "Email", "ciclo_1", "ciclo_2", "ciclo_3", "apps usadas"])
    else:
        try:
            df = pd.read_csv(DATASET_PATH)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=["Nombre", "Apellido", "Email", "ciclo_1", "ciclo_2", "ciclo_3", "apps usadas"])

    # Agregar nueva fila con los datos
    nueva_fila = pd.DataFrame([{
        "Nombre": nombre,
        "Apellido": apellido,
        "Email": email,
        "ciclo_1": ciclo_1,
        "ciclo_2": ciclo_2,
        "ciclo_3": ciclo_3,
        "apps usadas": Apps_usadas
    }])

    df = pd.concat([df, nueva_fila], ignore_index=True)

    # Guardar datos asegurando codificación UTF-8 y sin índice
    df.to_csv(DATASET_PATH, index=False, encoding='utf-8-sig')
    print(f"✅ Datos guardados en {DATASET_PATH}")
 
# Ruta de registro de estudiante

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        contrasena = request.form.get("contrasena", "").strip()
        nombre = request.form.get("nombre", "").strip().title()
        apellido = request.form.get("apellido", "").strip().title()
        Apps_usadas = request.form.get("Apps_usadas", "").strip()

        # Obtener y limpiar ciclos
        def limpiar_nota(cadena):
            cadena = re.sub(r"[^0-9\.,]", "", cadena.strip())
            return float(cadena.replace(",", ".")) if cadena not in ["", ".", ","] else None

        ciclo_1 = limpiar_nota(request.form.get("ciclo_1", ""))
        ciclo_2 = limpiar_nota(request.form.get("ciclo_2", ""))
        ciclo_3 = limpiar_nota(request.form.get("ciclo_3", ""))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template("registro.html", error="Este email ya está registrado. Intenta iniciar sesión.")

        # Insertar el nuevo usuario en la base de datos
        cursor.execute("""
            INSERT INTO usuarios (email, contrasena, nombre, apellido, ciclo_1, ciclo_2, ciclo_3, Apps_usadas) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (email, contrasena, nombre, apellido, ciclo_1, ciclo_2, ciclo_3, Apps_usadas))

        conn.commit()
        release_db_connection(conn)
        # Guardar en CSV
        guardar_en_csv(nombre, apellido, email, ciclo_1, ciclo_2, ciclo_3, Apps_usadas)

        return redirect(url_for("login"))
    return render_template("registro.html")

# Ruta de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        contrasena = request.form.get("contrasena", "").strip()

        conn =  get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, apellido FROM usuarios WHERE email = %s AND contrasena = %s", (email, contrasena))
        usuario = cursor.fetchone()
        release_db_connection(conn)

        if usuario:
            session["usuario_id"] = usuario[0]
            session["nombre"] = usuario[1]
            session["apellido"] = usuario[2]
            session["email"] = email  
            return redirect(url_for("dashboard"))  
        else:
            return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# Ruta del Dashboard
@app.route('/dashboard')
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  # Si no hay sesión, redirige a login

    nombre = session["nombre"]
    apellido = session["apellido"]

    return render_template("dashboard.html", nombre=nombre, apellido=apellido)

@app.route('/imagen1')
def imagen1():
    return render_template("imagen1.html")

@app.route('/imagen2')
def imagen2():
    return render_template("imagen2.html")

@app.route('/imagen3')
def imagen3():
    return render_template("imagen3.html")

@app.route('/imagen4')
def imagen4():
    return render_template("imagen4.html")

@app.route('/encuesta/<int:pagina>', methods=['GET', 'POST'])
def encuesta(pagina):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    inicio = (pagina - 1) * 20
    fin = inicio + 20
    preguntas_pagina = preguntas[inicio:fin]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = %s", (usuario_id,))
    respuestas_previas = dict(cursor.fetchall())  
    release_db_connection(conn)

    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor()
        for i, pregunta in enumerate(preguntas_pagina):
            respuesta = request.form.get(f'pregunta{inicio + i + 1}')
            if respuesta:
                cursor.execute("""
                INSERT INTO respuestas (id_usuario, pregunta, respuesta)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_usuario, pregunta) 
                DO UPDATE SET respuesta = EXCLUDED.respuesta;
                """, (usuario_id, pregunta["texto"], respuesta))

        conn.commit()
        release_db_connection(conn)
              
        if pagina == 1:
            return redirect(url_for("imagen2"))
        elif pagina == 2:
            return redirect(url_for("imagen3"))
        elif pagina == 3:
            return redirect(url_for("imagen4"))
        elif pagina == 4:
            return redirect(url_for("resultado"))
     

    return render_template(f"encuesta{pagina}.html", preguntas=preguntas_pagina, pagina=pagina, total_paginas=4, respuestas_previas=respuestas_previas)

class NotaPredictor:
    def __init__(self, model_path=MODEL_PATH):
        if os.path.exists(model_path):
            try:
                loaded_data = joblib.load(model_path)
                if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
                    self.model, self.label_encoder = loaded_data
                else:
                    raise ValueError("El archivo del modelo no contiene los datos esperados.")
            except Exception as e:
                print(f"⚠️ Error al cargar el modelo: {e}. Se reentrenará desde cero.")
                self.model = None
                self.label_encoder = LabelEncoder()
                self.entrenar_modelo()
        else:
            self.model = None
            self.label_encoder = LabelEncoder()
            self.entrenar_modelo()
    
    def entrenar_modelo(self):
        # Conectar a la base de datos SQLite y obtener datos actualizados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT estilo, Apps_usadas, ciclo_1, ciclo_2, ciclo_3 FROM usuarios WHERE estilo IS NOT NULL AND Apps_usadas IS NOT NULL")
        usuarios_data = cursor.fetchall()
        release_db_connection(conn)

        if not usuarios_data:
            print("⚠️ No hay datos suficientes para entrenar el modelo.")
            return

        df = pd.DataFrame(usuarios_data, columns=['estilo', 'Apps_usadas', 'ciclo_1', 'ciclo_2', 'ciclo_3'])

        # Codificar 'estilo' en valores numéricos
        self.label_encoder = LabelEncoder()
        df['estilo'] = self.label_encoder.fit_transform(df['estilo'].astype(str))

        # Convertir 'Apps_usadas' a la cantidad de aplicaciones usadas
        df['Apps_usadas'] = df['Apps_usadas'].astype(str).apply(lambda x: len(x.split(',')) if x else 0)

        # Calcular la nota promedio de los ciclos
        df['nota_promedio'] = df[['ciclo_1', 'ciclo_2', 'ciclo_3']].mean(axis=1)

        # Definir las variables de entrada y salida
        X = df[['estilo', 'Apps_usadas']]
        y = df['nota_promedio']

        if len(df) < 5:
            print("⚠️ Datos insuficientes para entrenar el modelo de predicción.")
            return

        # Entrenar el modelo
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Guardar el modelo entrenado y el label encoder correctamente
        joblib.dump((model, self.label_encoder), MODEL_PATH)
        self.model = model

        print("✅ Modelo entrenado correctamente con datos actualizados.")
    
    def predecir_nota(self, estilo, apps_usadas):
        if self.model is None:
            return "Modelo no entrenado"
        
        # Verificar si el estilo está en los datos entrenados
        if estilo not in self.label_encoder.classes_:
            print(f"⚠️ Estilo '{estilo}' no reconocido, asignando 'Activo' por defecto.")
            estilo = 'Activo'
        
        estilo_codificado = self.label_encoder.transform([estilo])[0]
        
        # Contar la cantidad de apps usadas
        apps_cantidad = len(apps_usadas.split(',')) if apps_usadas else 0

        # Realizar la predicción
        entrada = np.array([[estilo_codificado, apps_cantidad]])
        nota_predicha = self.model.predict(entrada)[0]

        return round(nota_predicha, 2)

# Eliminar modelo anterior si existe y reentrenar
if not os.path.exists(MODEL_PATH):  # Solo si no existe
    predictor = NotaPredictor()  # Entrena el modelo si no exisTE

# Entrenar el modelo al iniciar
predictor = NotaPredictor()
if not os.path.exists(MODEL_PATH):
    predictor.entrenar_modelo()

@app.route('/prediccion_nota', methods=['GET'])
def prediccion_nota():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT estilo, Apps_usadas FROM usuarios WHERE id_usuario = %s", (usuario_id,))
    usuario_data = cursor.fetchone()
    release_db_connection(conn)

    if not usuario_data:
        return "No se encontraron datos del usuario", 404

    estilo_aprendizaje, apps_usadas = usuario_data

    predictor = NotaPredictor()
    nota_predicha = predictor.predecir_nota(estilo_aprendizaje, apps_usadas)

    return render_template("prediccion_nota.html", nota_predicha=nota_predicha)


# Ruta de resultados de la encuesta
@app.route('/resultado', methods=['GET', 'POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  

    usuario_id = session["usuario_id"]
    nombre = session["nombre"]
    apellido = session["apellido"]

    conn = get_db_connection() 
    cursor = conn.cursor()
        
    # Verificar cuántas respuestas ha respondido el usuario
    cursor.execute("SELECT COUNT(*) FROM respuestas WHERE id_usuario = %s", (usuario_id,))
    num_respuestas = cursor.fetchone()[0]
    
    # Número total de preguntas
    total_preguntas = len(preguntas)  # Asegurarse de que `preguntas` contiene todas las preguntas
    
    # Si el usuario no ha respondido todas las preguntas, redirigir a progreso
    if num_respuestas < total_preguntas:
        release_db_connection(conn)
        return render_template("progreso.html", error="Aún no has terminado la encuesta. Responde todas las preguntas para ver tu estilo de aprendizaje.")

    # Obtener respuestas del usuario
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = %s", (usuario_id,))
    respuestas = dict(cursor.fetchall())  
    release_db_connection(conn)

    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    for pregunta in preguntas:
        respuesta = respuestas.get(pregunta["texto"])
        if respuesta == '+':
            estilos[pregunta["estilo"]] += 1  

    estilo_predominante = max(estilos, key=estilos.get)

    # Guardar el estilo de aprendizaje en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET estilo = %s WHERE id_usuario = %s", (estilo_predominante, usuario_id))
    conn.commit()
    release_db_connection(conn)

    rendimiento = CalculoDeRendimiento.obtener_rendimiento(nombre, apellido)
    promedio_rendimiento = rendimiento["promedio"]
    tipo_rendimiento = rendimiento["tipo_rendimiento"]

    # Obtener estilo y apps usadas para predecir la nota
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT estilo, Apps_usadas FROM usuarios WHERE id_usuario = %s", (usuario_id,))
    usuario_data = cursor.fetchone()
    release_db_connection(conn)

    if usuario_data:
        estilo_aprendizaje, apps_usadas = usuario_data
        predictor = NotaPredictor()
        nota_predicha = predictor.predecir_nota(estilo_aprendizaje, apps_usadas)
    else:
        nota_predicha = "N/A"

    # Determinar la última página respondida
    ultima_pagina = 1
    if num_respuestas > 60:
        ultima_pagina = 4
    elif num_respuestas > 40:
        ultima_pagina = 3
    elif num_respuestas > 20:
        ultima_pagina = 2

    return render_template('resultado.html', 
                           nombre=nombre, apellido=apellido, 
                           estilo=estilo_predominante, 
                           promedio_rendimiento=promedio_rendimiento, 
                           tipo_rendimiento=tipo_rendimiento, 
                           ultima_pagina=ultima_pagina,
                           nota_predicha=nota_predicha)


@app.route('/recomendaciones', methods=['GET'])
def recomendaciones():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('login'))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT estilo FROM usuarios WHERE id_usuario = %s", (usuario_id,))
        resultado = cursor.fetchone()

        if not resultado:
            return "No se encontró el estilo de aprendizaje.", 404  

        Estilos = resultado[0]  
        print(f"🔍 Estilo recuperado: {Estilos}")

        recomendaciones = HerramientasEducativas.obtener_herramientas_recomendadas(Estilos)

        print(f"Recomendaciones encontradas para estilo {Estilos}: {recomendaciones}")

        return render_template('recomendaciones.html', recomendaciones=recomendaciones, Estilos=Estilos)

    except Exception as e:
        print(f"⚠️ Error en recomendaciones: {e}")
        return "Ocurrió un error al obtener recomendaciones.", 500

    finally:
        if conn:
            release_db_connection(conn)  # ✅ Ahora se libera correctamente


@app.route("/ver_progreso")
def ver_progreso():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  # Redirige a login si el usuario no ha iniciado sesión

    usuario_id = session["usuario_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT pregunta, respuesta FROM respuestas WHERE id_usuario = %s", (usuario_id,))
    respuestas = cursor.fetchall()
    
    release_db_connection(conn)
    respuestas = list(dict.fromkeys(respuestas)) #eliminara duplicados al ver el progreso de las respuestas

    return render_template("progreso.html", respuestas=respuestas)

@app.route('/guardar_respuestas', methods=['POST'])
def guardar_respuestas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    for i, pregunta in enumerate(preguntas):
        respuesta = request.form.get(f'pregunta{i+1}')  # Se asegura de capturar correctamente la respuesta
        
        if respuesta:  # Solo guarda respuestas marcadas
            cursor.execute("""
                INSERT OR REPLACE INTO respuestas (id_usuario, pregunta, respuesta)
                VALUES (%s, %s, %s)
            """, (usuario_id, pregunta["texto"], respuesta))

    conn.commit()
    release_db_connection(conn)

    # Verificar si ya respondió todas las preguntas
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM respuestas WHERE id_usuario = %s", (usuario_id,))
    num_respuestas = cursor.fetchone()[0]
    release_db_connection(conn)

    # Redirigir al usuario a la siguiente página de la encuesta
    if num_respuestas < len(preguntas):
        return redirect(url_for("encuesta", pagina=(num_respuestas // 20) + 1))
    else:
        return redirect(url_for("resultado"))  # Si termina, ir a resultados


# Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/ver_respuestas')
def ver_respuestas():
    return render_template("ver_respuestas.html")

verificar_base_datos()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
