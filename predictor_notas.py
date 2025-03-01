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
            self.model = joblib.load(model_path)
        else:
            self.model = None
    
    def entrenar_modelo(self):
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener los datos de los usuarios, incluyendo el estilo
        cursor.execute("SELECT id_usuario, estilo, Apps_usadas, ciclo_1, ciclo_2, ciclo_3 FROM usuarios")
        usuarios_data = cursor.fetchall()
        conn.close()

        # Convertir datos a DataFrame
        df = pd.DataFrame(usuarios_data, columns=['id_usuario', 'estilo', 'Apps_usadas', 'ciclo_1', 'ciclo_2', 'ciclo_3'])

        # Codificar 'estilo' si existe, si no, asignar un valor predeterminado
        if 'estilo' in df.columns:
            label_encoder = LabelEncoder()
            df['estilo'] = label_encoder.fit_transform(df['estilo'].astype(str))
        else:
            print("⚠️ Advertencia: No se encontró la columna 'estilo' en SQLite.")
            df['estilo'] = 0  # Valor por defecto

        # Convertir Apps_usadas a número
        df['Apps_usadas'] = df['Apps_usadas'].astype(str).apply(lambda x: len(x.split(',')) if x else 0)
        
        # Definir las variables de entrenamiento
        X = df[['estilo', 'Apps_usadas']]
        y = df[['ciclo_1', 'ciclo_2', 'ciclo_3']].mean(axis=1)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        joblib.dump(model, MODEL_PATH)
        self.model = model
    
    def predecir_nota(self, estilo, apps_usadas):
        if self.model is None:
            return "Modelo no entrenado"
        
        label_encoder = LabelEncoder()
        estilo_codificado = label_encoder.fit_transform([estilo])[0]
        apps_cantidad = len(apps_usadas.split(','))
        
        nota_predicha = self.model.predict(np.array([[estilo_codificado, apps_cantidad]]))[0]
        return round(nota_predicha, 2)

# Entrenar el modelo al iniciar
predictor = NotaPredictor()
if not os.path.exists(MODEL_PATH):
    predictor.entrenar_modelo()
