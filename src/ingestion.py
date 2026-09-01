import requests
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

base = Path(__file__).parent

db = base / "db" / "ingestion.db"
xlsx = base / "xlsx" / "ingestion.xlsx"
auditoria = base / "static" / "auditoria" / "ingestion.txt"

api = "https://jsonplaceholder.typicode.com/posts"


# Crear carpetas
db.parent.mkdir(parents=True, exist_ok=True)
xlsx.parent.mkdir(parents=True, exist_ok=True)
auditoria.parent.mkdir(parents=True, exist_ok=True)


# Obtener datos del API
respuesta = requests.get(api)
datos = respuesta.json()

print("Datos obtenidos:", len(datos))


# Crear la base de datos
conexion = sqlite3.connect(db)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    body TEXT,
    fecha TEXT
)
""")

conexion.commit()


# Guardar los datos
cursor.execute("DELETE FROM posts")

fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for dato in datos:
    cursor.execute("""
    INSERT INTO posts (id, user_id, title, body, fecha)
    VALUES (?, ?, ?, ?, ?)
    """, (
        dato["id"],
        dato["userId"],
        dato["title"],
        dato["body"],
        fecha
    ))

conexion.commit()


# Leer los datos con Pandas
df = pd.read_sql_query(
    "SELECT * FROM posts ORDER BY id",
    conexion
)

print("Datos guardados:", len(df))


# Crear archivo Excel
df.head(10).to_excel(
    xlsx,
    index=False
)


# Comparar los datos del API con SQLite
api_df = pd.DataFrame(datos)

api_df = api_df.rename(
    columns={"userId": "user_id"}
)

api_df = api_df[["id", "user_id", "title", "body"]]

db_df = df[["id", "user_id", "title", "body"]]

api_df = api_df.sort_values("id").reset_index(drop=True)
db_df = db_df.sort_values("id").reset_index(drop=True)

if api_df.equals(db_df):
    resultado = "INTEGRIDAD OK"
else:
    resultado = "SE ENCONTRARON DIFERENCIAS"


# Crear auditoría
texto = f"""
AUDITORIA DE INGESTA
--------------------

API: {api}

Fecha: {fecha}

Registros obtenidos del API: {len(api_df)}
Registros guardados en SQLite: {len(db_df)}

Resultado:
{resultado}
"""

auditoria.write_text(texto, encoding="utf-8")

conexion.close()

print("Excel creado:", xlsx)
print("Auditoria creada:", auditoria)
print("Proceso terminado")