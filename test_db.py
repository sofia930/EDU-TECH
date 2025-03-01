import sqlite3
import pandas as pd

DB_PATH = "database.db"  # Asegúrate de que esta ruta sea correcta

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Obtener los datos de los usuarios incluyendo "Estilo"
cursor.execute("SELECT nombre, apellido, ciclo_1, ciclo_2, ciclo_3, estilo FROM usuarios")
usuarios = cursor.fetchall()

conn.close()

# Convertir los datos en un DataFrame
df_usuarios = pd.DataFrame(usuarios, columns=['Nombre', 'Apellido', 'ciclo_1', 'ciclo_2', 'ciclo_3', 'Estilo'])

# Mostrar las primeras filas del DataFrame
print("Datos extraídos de la base de datos:")
print(df_usuarios.head())
