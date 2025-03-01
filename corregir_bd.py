import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(usuarios);")
columnas = cursor.fetchall()

conn.close()

print("Columnas en la tabla usuarios:")
for columna in columnas:
    print(columna[1])  # El nombre de la columna

