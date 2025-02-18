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

# 📌 Clase para manejar sesión
class SessionService:
    @staticmethod
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @staticmethod
    def ver_respuestas():
        return render_template("ver_respuestas.html")

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
            return redirect(url_for("encuesta"))

        return render_template("login.html", error="⚠️ Email o contraseña incorrectos")

    return render_template("login.html")

# 📌 Ruta de Encuesta
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

# 📌 Ver Progreso
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
    return SessionService.logout()

@app.route('/ver_respuestas')
def ver_respuestas():
    return SessionService.ver_respuestas()

if __name__ == '__main__':
    app.run(debug=True)
