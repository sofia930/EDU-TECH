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

def verificar_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de usuarios
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

    # Tabla de respuestas (Guarda respuestas por usuario)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id_usuario INTEGER PRIMARY KEY,
        pregunta_1 TEXT,
        pregunta_2 TEXT,
        pregunta_3 TEXT,
        pregunta_4 TEXT,
        pregunta_5 TEXT,
        pregunta_6 TEXT,
        pregunta_7 TEXT,
        pregunta_8 TEXT,
        pregunta_9 TEXT,
        pregunta_10 TEXT,
        pregunta_11 TEXT,
        pregunta_12 TEXT,
        pregunta_13 TEXT,
        pregunta_14 TEXT,
        pregunta_15 TEXT,
        pregunta_16 TEXT,
        pregunta_17 TEXT,
        pregunta_18 TEXT,
        pregunta_19 TEXT,
        pregunta_20 TEXT,
        pregunta_21 TEXT,
        pregunta_22 TEXT,
        pregunta_23 TEXT,
        pregunta_24 TEXT,
        pregunta_25 TEXT,
        pregunta_26 TEXT,
        pregunta_27 TEXT,
        pregunta_28 TEXT,
        pregunta_29 TEXT,
        pregunta_30 TEXT,
        pregunta_31 TEXT,
        pregunta_32 TEXT,
        pregunta_33 TEXT,
        pregunta_34 TEXT,
        pregunta_35 TEXT,
        pregunta_36 TEXT,
        pregunta_37 TEXT,
        pregunta_38 TEXT,
        pregunta_39 TEXT,
        pregunta_40 TEXT,
        pregunta_41 TEXT,
        pregunta_42 TEXT,
        pregunta_43 TEXT,
        pregunta_44 TEXT,
        pregunta_45 TEXT,
        pregunta_46 TEXT,
        pregunta_47 TEXT,
        pregunta_48 TEXT,
        pregunta_49 TEXT,
        pregunta_50 TEXT,
        pregunta_51 TEXT,
        pregunta_52 TEXT,
        pregunta_53 TEXT,
        pregunta_54 TEXT,
        pregunta_55 TEXT,
        pregunta_56 TEXT,
        pregunta_57 TEXT,
        pregunta_58 TEXT,
        pregunta_59 TEXT,
        pregunta_60 TEXT,
        pregunta_61 TEXT,
        pregunta_62 TEXT,
        pregunta_63 TEXT,
        pregunta_64 TEXT,
        pregunta_65 TEXT,
        pregunta_66 TEXT,
        pregunta_67 TEXT,
        pregunta_68 TEXT,
        pregunta_69 TEXT,
        pregunta_70 TEXT,
        pregunta_71 TEXT,
        pregunta_72 TEXT,
        pregunta_73 TEXT,
        pregunta_74 TEXT,
        pregunta_75 TEXT,
        pregunta_76 TEXT,
        pregunta_77 TEXT,
        pregunta_78 TEXT,
        pregunta_79 TEXT,
        pregunta_80 TEXT,                         
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)

    conn.commit()
    conn.close()

# 📌 Preguntas de la encuesta
preguntas = [
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
    
    c# Crear tabla de usuarios si no existe
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

# 📌 Ruta principal (Muestra la bienvenida)
@app.route('/')
def home():
    return render_template("bienvenida.html")

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

# 📌 Ruta de resultados de la encuesta
@app.route('/resultado', methods=['POST'])
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  

    usuario_id = session["usuario_id"]
    nombre = session["nombre"]
    apellido = session["apellido"]

    respuestas = {f'pregunta{i}': request.form.get(f'pregunta{i}') for i in range(len(preguntas))}

    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for i, pregunta in enumerate(preguntas):
        respuesta = respuestas.get(f'pregunta{i}')
        if respuesta:
            estilos[pregunta["estilo"]] += (1 if respuesta == "+" else 0)

            cursor.execute("""
                INSERT INTO respuestas (id_usuario, pregunta, respuesta)
                VALUES (?, ?, ?)
                ON CONFLICT(id_usuario, pregunta) 
                DO UPDATE SET respuesta = excluded.respuesta
            """, (usuario_id, pregunta["texto"], respuesta))

    conn.commit()
    conn.close()

@app.route('/resultado')
def resultado():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    # Obtener respuestas de la encuesta desde la sesión
    respuestas = session.get("respuestas", {})

    # Inicializar los estilos de aprendizaje
    estilos = {"Activo": 0, "Reflexivo": 0, "Teórico": 0, "Pragmático": 0}

    for i, pregunta in enumerate(preguntas):
        respuesta = respuestas.get(f'pregunta_{i+1}')
        if respuesta == '+':
            estilos[pregunta["estilo"]] += 1  

    # Determinar el estilo predominante
    estilo_predominante = max(estilos, key=estilos.get)

    # Obtener rendimiento académico desde la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT matematicas, historia, fisica, quimica, biologia, ingles, geografia
        FROM usuarios WHERE id_usuario = ?
    """, (session["usuario_id"],))
    
    rendimiento = cursor.fetchone()
    conn.close()

    if rendimiento:
        materias = ["Matemáticas", "Historia", "Física", "Química", "Biología", "Inglés", "Geografía"]
        rendimiento_dict = {materias[i]: rendimiento[i] for i in range(len(materias))}
    else:
        rendimiento_dict = {}

    return render_template('resultado.html', nombre=session["nombre"], apellido=session["apellido"], 
                           estilo=estilo_predominante, rendimiento=rendimiento_dict, respuestas=respuestas)

@app.route("/ver_progreso")
def ver_progreso():
    if "usuario_id" not in session:
        return redirect(url_for("login"))  # Redirige a login si el usuario no ha iniciado sesión

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

@app.route('/ver_respuestas')
def ver_respuestas():
    return render_template("ver_respuestas.html")

if __name__ == '__main__':
    app.run(debug=True)  