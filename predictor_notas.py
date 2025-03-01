import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Definir rutas
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'modelo_notas.pkl')
DB_PATH = os.path.join(BASE_DIR, 'database.db')

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT estilo, Apps_usadas, ciclo_1, ciclo_2, ciclo_3 FROM usuarios WHERE estilo IS NOT NULL AND Apps_usadas IS NOT NULL")
        usuarios_data = cursor.fetchall()
        conn.close()

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
if os.path.exists(MODEL_PATH):
    os.remove(MODEL_PATH)

# Entrenar el modelo al iniciar
predictor = NotaPredictor()
if not os.path.exists(MODEL_PATH):
    predictor.entrenar_modelo()