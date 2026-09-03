import os
import sys
import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

API_URL = "https://world.openfoodfacts.org/api/v2/search?categories_tags=en:beverages&page_size=100"
HEADERS = {"User-Agent": "BigDataStudentApp/1.0 (contacto@estudiante.com)"}

MONGO_URI = os.getenv("MONGO_URI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "ingestion.xlsx")
AUDIT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "ingestion.txt")

def main():
    if not MONGO_URI or "<" in MONGO_URI:
        print("ERROR CRITICO: La variable MONGO_URI no esta configurada o contiene '<>'.")
        print("Configura el Secret MONGO_URI en GitHub > Settings > Secrets and variables > Actions.")
        sys.exit(1)

    os.makedirs(os.path.dirname(XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)

    print("Conectando a MongoDB Atlas...")
    client = MongoClient(MONGO_URI)
    db = client["bigdata_db"]
    col_productos = db["productos"]
    col_auditoria = db["auditoria_ingestion"]

    col_productos.create_index("code")

    print(f"Obteniendo datos desde la API: {API_URL}")
    res = requests.get(API_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()

    raw_products = res.json().get("products", [])
    total_api = len(raw_products)

    seen_codes = set()
    docs = []

    for p in raw_products:
        code = str(p.get("code", "")).strip()
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        nutriments = p.get("nutriments", {})
        docs.append({
            "code": code,
            "product_name": p.get("product_name", "Desconocido"),
            "brands": p.get("brands", "N/A"),
            "categories": p.get("categories", "N/A"),
            "nutriscore_grade": str(p.get("nutriscore_grade", "N/A")).upper(),
            "energy_kcal_100g": float(nutriments.get("energy-kcal_100g", 0) or 0),
            "fat_100g": float(nutriments.get("fat_100g", 0) or 0),
            "sugars_100g": float(nutriments.get("sugars_100g", 0) or 0),
            "proteins_100g": float(nutriments.get("proteins_100g", 0) or 0),
            "fecha_ingesta": datetime.utcnow()
        })

    if docs:
        col_productos.delete_many({})
        col_productos.insert_many(docs)

        df = pd.DataFrame(docs)
        df_sample = df[["code", "product_name", "brands", "nutriscore_grade", "energy_kcal_100g", "sugars_100g"]]
        df_sample.head(25).to_excel(XLSX_PATH, index=False)

    total_db = col_productos.count_documents({})
    valido = len(docs) == total_db

    audit_entry = {
        "fecha": datetime.utcnow(),
        "registros_api": total_api,
        "registros_procesados": len(docs),
        "registros_db": total_db,
        "estado": "OK" if (valido and total_db > 0) else "ERROR"
    }
    col_auditoria.insert_one(audit_entry)

    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        f.write("AUDITORIA DE INGESTION BIG DATA\n")
        f.write(f"Fecha ejecucion: {audit_entry['fecha']}\n")
        f.write(f"Registros extraidos API: {total_api}\n")
        f.write(f"Registros unicos procesados: {len(docs)}\n")
        f.write(f"Registros persistidos Mongo: {total_db}\n")
        f.write(f"Estado validacion: {audit_entry['estado']}\n")

    client.close()

if __name__ == "__main__":
    main()