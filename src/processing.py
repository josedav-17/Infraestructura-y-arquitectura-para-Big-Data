import os
import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient

DEFAULT_URI = "mongodb+srv://josedav:josedav@cluster1.gywv7vl.mongodb.net/bigdata_db?retryWrites=true&w=majority"
MONGO_URI = os.getenv("MONGO_URI", DEFAULT_URI)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "cleaned_data.xlsx")
REPORT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "cleaning_report.txt")

def main():
    os.makedirs(os.path.dirname(CLEANED_XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    print("Conectando a la base de datos analitica en la nube (MongoDB Atlas)...")
    client = MongoClient(MONGO_URI)
    db = client["bigdata_db"]
    col_productos = db["productos"]

    cursor = col_productos.find({}, {"_id": 0})
    raw_docs = list(cursor)
    df = pd.DataFrame(raw_docs)

    initial_count = len(df)
    print(f"Registros extraidos inicialmente: {initial_count}")

    if df.empty:
        print("No se encontraron registros en la base de datos.")
        client.close()
        return

    # Estructura para registrar metricas de auditoria
    nulls_initial = df.isnull().sum().to_dict()
    duplicates_initial = int(df.duplicated(subset=["code"]).sum())

    # 1. Eliminacion de Duplicados
    df = df.drop_duplicates(subset=["code"], keep="first")
    count_after_duplicates = len(df)

    # 2. Correccion de Tipos de Datos
    numeric_cols = ["energy_kcal_100g", "fat_100g", "sugars_100g", "proteins_100g", "salt_100g"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    string_cols = ["product_name", "brands", "categories", "nutriscore_grade"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 3. Manejo de Valores Nulos e Inconsistencias
    df["product_name"] = df["product_name"].replace(["nan", ""], "Desconocido")
    df["brands"] = df["brands"].replace(["nan", ""], "N/A")
    df["categories"] = df["categories"].replace(["nan", ""], "N/A")
    df["nutriscore_grade"] = df["nutriscore_grade"].replace(["nan", ""], "N/A")

    # 4. Tratamiento de Outliers (metodo IQR para azucares y calorias)
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

    # 5. Transformaciones Adicionales: Normalizacion Min-Max de Nutricion
    if "energy_kcal_100g" in df.columns:
        min_val = df["energy_kcal_100g"].min()
        max_val = df["energy_kcal_100g"].max()
        if max_val > min_val:
            df["energy_kcal_norm"] = (df["energy_kcal_100g"] - min_val) / (max_val - min_val)
        else:
            df["energy_kcal_norm"] = 0.0

    final_count = len(df)

    # Exportar archivo con la muestra de datos limpios
    df.head(50).to_excel(CLEANED_XLSX_PATH, index=False)
    print(f"Archivo de datos limpios generado en: {CLEANED_XLSX_PATH}")

    # Generar informe de auditoria
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== INFORME DE AUDITORIA Y LIMPIEZA DE DATOS ===\n")
        f.write(f"Fecha de ejecucion: {datetime.utcnow()}\n\n")
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
        f.write("   - Normalizacion: Escala Min-Max aplicada a 'energy_kcal_100g' -> 'energy_kcal_norm'\n\n")
        f.write("3. RESULTADO FINAL:\n")
        f.write(f"   - Total registros despues de limpieza: {final_count}\n")
        f.write("   - Estado de calidad: LIMPIO Y REGLAMENTADO\n")

    print(f"Reporte de auditoria generado en: {REPORT_PATH}")
    client.close()

if __name__ == "__main__":
    main()