import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

PRIMARY_API_URL = "https://world.openfoodfacts.org/api/v2/search?categories_tags=en:beverages&page_size=100"
FALLBACK_API_URL = "https://dummyjson.com/products?limit=100"
HEADERS = {"User-Agent": "BigDataStudentApp/1.0 (contacto@estudiante.com)"}

MONGO_URI = os.getenv("MONGO_URI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "ingestion.xlsx")
AUDIT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "ingestion.txt")

def fetch_data_with_retry():
    print(f"Obteniendo datos desde la API principal: {PRIMARY_API_URL}")
    for attempt in range(1, 4):
        try:
            res = requests.get(PRIMARY_API_URL, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                raw_products = res.json().get("products", [])
                if raw_products:
                    return raw_products, "OpenFoodFacts"
        except requests.RequestException as e:
            print(f"Intento {attempt} fallido para API principal: {e}")
        time.sleep(2 * attempt)

    print(f"API principal no disponible. Usando API de respaldo: {FALLBACK_API_URL}")
    res = requests.get(FALLBACK_API_URL, timeout=15)
    res.raise_for_status()
    fallback_products = res.json().get("products", [])
    return fallback_products, "DummyJSON"

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

    raw_products, source_name = fetch_data_with_retry()
    total_api = len(raw_products)
    print(f"Datos obtenidos exitosamente de {source_name}: {total_api} registros.")

    seen_codes = set()
    docs = []

    for p in raw_products:
        if source_name == "OpenFoodFacts":
            code = str(p.get("code", "")).strip()
            nutriments = p.get("nutriments", {})
            name = p.get("product_name", "Desconocido")
            brand = p.get("brands", "N/A")
            cat = p.get("categories", "N/A")
            grade = str(p.get("nutriscore_grade", "N/A")).upper()
            kcal = float(nutriments.get("energy-kcal_100g", 0) or 0)
            fat = float(nutriments.get("fat_100g", 0) or 0)
            sugars = float(nutriments.get("sugars_100g", 0) or 0)
            proteins = float(nutriments.get("proteins_100g", 0) or 0)
        else:
            code = str(p.get("id", "")).strip()
            name = p.get("title", "Desconocido")
            brand = p.get("brand", "N/A")
            cat = p.get("category", "N/A")
            grade = "A" if p.get("rating", 0) >= 4.5 else "B"
            kcal = float(p.get("price", 0) * 10)
            fat = float(p.get("discountPercentage", 0))
            sugars = float(p.get("stock", 0))
            proteins = float(p.get("rating", 0))

        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        docs.append({
            "code": code,
            "product_name": name,
            "brands": brand,
            "categories": cat,
            "nutriscore_grade": grade,
            "energy_kcal_100g": kcal,
            "fat_100g": fat,
            "sugars_100g": sugars,
            "proteins_100g": proteins,
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
        "fuente": source_name,
        "registros_api": total_api,
        "registros_procesados": len(docs),
        "registros_db": total_db,
        "estado": "OK" if (valido and total_db > 0) else "ERROR"
    }
    col_auditoria.insert_one(audit_entry)

    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        f.write("AUDITORIA DE INGESTION BIG DATA\n")
        f.write(f"Fecha ejecucion: {audit_entry['fecha']}\n")
        f.write(f"Fuente de datos: {source_name}\n")
        f.write(f"Registros extraidos API: {total_api}\n")
        f.write(f"Registros unicos procesados: {len(docs)}\n")
        f.write(f"Registros persistidos Mongo: {total_db}\n")
        f.write(f"Estado validacion: {audit_entry['estado']}\n")

    print(f"Ingesta finalizada. Estado: {audit_entry['estado']}")
    client.close()

if __name__ == "__main__":
    main()