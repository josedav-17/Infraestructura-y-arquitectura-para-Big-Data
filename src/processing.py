import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "ingestion.db")
XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "cleaned_data.xlsx")
REPORT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "cleaning_report.txt")

def handle_outliers_iqr(df, column):
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    df[column] = np.where(df[column] < lower, lower, df[column])
    df[column] = np.where(df[column] > upper, upper, df[column])
    return df

def main():
    os.makedirs(os.path.dirname(XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        print("Base de datos no encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM productos", conn)
    except Exception as e:
        print(f"Error al leer base de datos: {e}")
        conn.close()
        return

    initial_count = len(df)
    df = df.drop_duplicates(subset=["code"], keep="first")
    dedup_count = len(df)

    df["code"] = df["code"].astype(str).str.strip()
    df["product_name"] = df["product_name"].fillna("Sin Nombre").astype(str).str.strip()
    df["brands"] = df["brands"].fillna("Desconocido").astype(str).str.strip()
    df["nutriscore_grade"] = df["nutriscore_grade"].fillna("UNKNOWN").astype(str).str.upper()

    num_cols = ["energy_100g", "sugars_100g", "fat_100g"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df = handle_outliers_iqr(df, col)

    for col in num_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val > min_val:
            df[f"{col}_norm"] = (df[col] - min_val) / (max_val - min_val)
        else:
            df[f"{col}_norm"] = 0.0

    final_count = len(df)

    df.to_sql("productos_limpios", conn, if_exists="replace", index=False)
    conn.close()

    df.head(500).to_excel(XLSX_PATH, index=False)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== REPORTE DE LIMPIEZA ===\n")
        f.write(f"Fecha: {datetime.now()}\n")
        f.write(f"Iniciales: {initial_count}\n")
        f.write(f"Sin duplicados: {dedup_count}\n")
        f.write(f"Finales: {final_count}\n")

    print(f"Limpieza finalizada: {final_count} registros.")

if __name__ == "__main__":
    main()