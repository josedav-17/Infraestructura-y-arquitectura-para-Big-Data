import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "cleaned_data.xlsx")
REPORT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "cleaning_report.txt")

def main():
    if not MONGO_URI or "<" in MONGO_URI:
        print("ERROR CRITICO: La variable MONGO_URI no esta configurada o contiene '<>'.")
        print("Configura el Secret MONGO_URI en GitHub > Settings > Secrets and variables > Actions.")
        sys.exit(1)

    os.makedirs(os.path.dirname(CLEANED_XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    client = MongoClient(MONGO_URI)
    db = client["bigdata_db"]
    col_productos = db["productos"]

    raw_docs = list(col_productos.find({}, {"_id": 0}))
    df = pd.DataFrame(raw_docs)

    initial_count = len(df)

    if df.empty:
        print("No se encontraron registros en MongoDB.")
        client.close()
        sys.exit(1)

    nulls_initial = df.isnull().sum().to_dict()
    duplicates_initial = int(df.duplicated(subset=["code"]).sum())

    df = df.drop_duplicates(subset=["code"], keep="first")

    numeric_cols = ["energy_kcal_100g", "fat_100g", "sugars_100g", "proteins_100g"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    string_cols = ["product_name", "brands", "categories", "nutriscore_grade"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["product_name"] = df["product_name"].replace(["nan", ""], "Desconocido")
    df["brands"] = df["brands"].replace(["nan", ""], "N/A")
    df["categories"] = df["categories"].replace(["nan", ""], "N/A")

    outliers_treated = 0
    for col in ["sugars_100g", "energy_kcal_100g"]:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            outliers_mask = df[col] > upper_bound
            outliers_treated += int(outliers_mask.sum())
            df.loc[outliers_mask, col] = upper_bound

    if "energy_kcal_100g" in df.columns:
        min_val = df["energy_kcal_100g"].min()
        max_val = df["energy_kcal_100g"].max()
        df["energy_kcal_norm"] = (df["energy_kcal_100g"] - min_val) / (max_val - min_val) if max_val > min_val else 0.0

    final_count = len(df)

    df.head(50).to_excel(CLEANED_XLSX_PATH, index=False)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== INFORME DE AUDITORIA Y LIMPIEZA DE DATOS ===\n")
        f.write(f"Fecha ejecucion: {datetime.utcnow()}\n\n")
        f.write("1. ESTADISTICAS INICIALES:\n")
        f.write(f"   - Total registros extraidos: {initial_count}\n")
        f.write(f"   - Registros duplicados detectados: {duplicates_initial}\n")
        f.write("   - Valores nulos por columna:\n")
        for k, v in nulls_initial.items():
            f.write(f"     * {k}: {v}\n")
        f.write("\n2. OPERACIONES DE LIMPIEZA REALIZADAS:\n")
        f.write(f"   - Registros duplicados eliminados: {duplicates_initial}\n")
        f.write("   - Imputacion de nulos: Cadenas a 'Desconocido/NA', Numericos a 0.0\n")
        f.write("   - Correccion de tipos: Conversion explicita a float64 y string\n")
        f.write(f"   - Outliers acotados (IQR): {outliers_treated} valores ajustados al limite superior\n")
        f.write("   - Normalizacion: Escala Min-Max en 'energy_kcal_100g'\n\n")
        f.write("3. RESULTADO FINAL:\n")
        f.write(f"   - Total registros limpios: {final_count}\n")
        f.write("   - Estado de calidad: LIMPIO Y REGLAMENTADO\n")

    client.close()

if __name__ == "__main__":
    main()