import bcrypt
import psycopg2

# Conectar a la base de datos PostgreSQL
conn = psycopg2.connect(
    dbname="mi_base_de_datos",
    user="sofia",
    password="12345",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

# Obtener todas las contraseñas actuales
cursor.execute("SELECT id_usuario, contrasena FROM usuarios")
usuarios = cursor.fetchall()

for usuario in usuarios:
    id_usuario = usuario[0]
    contrasena_plana = usuario[1]  

    # Verificar si la contraseña ya está cifrada
    if contrasena_plana.startswith("$2b$"):
        continue  # Ya está cifrada, no hacer nada

    # Cifrar la contraseña
    hashed_password = bcrypt.hashpw(contrasena_plana.encode('utf-8'), bcrypt.gensalt())

    # Actualizar la contraseña en la base de datos
    cursor.execute("UPDATE usuarios SET contrasena = %s WHERE id_usuario = %s", (hashed_password.decode('utf-8'), id_usuario))

conn.commit()
conn.close()

print("✅ Contraseñas convertidas correctamente.")
