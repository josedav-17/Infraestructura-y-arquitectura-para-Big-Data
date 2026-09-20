import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "ingestion.db")
SOURCES_DIR = os.path.join(BASE_DIR, "data_sources")

ENRICHED_XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "enriched_data.xlsx")
REPORT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "enriched_report.txt")

def load_source_file(filename, loader):
    path = os.path.join(SOURCES_DIR, filename)
    if not os.path.exists(path):
        return None
    
    try:
        df = loader(path)
        if "code" in df.columns:
            df["code"] = df["code"].astype(str).str.strip()
            df = df.drop_duplicates(subset=["code"], keep="first")
            return df
    except Exception:
        pass
    return None

def main():
    os.makedirs(os.path.dirname(ENRICHED_XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        print("Base de datos no encontrada.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        try:
            df_base = pd.read_sql_query("SELECT * FROM productos_limpios", conn)
        except Exception:
            df_base = pd.read_sql_query("SELECT * FROM productos", conn)

        df_base["code"] = df_base["code"].astype(str).str.strip()
        base_count = len(df_base)

        file_map = [
            ("precios.json", pd.read_json),
            ("paises.xlsx", pd.read_excel),
            ("fabricantes.csv", pd.read_csv),
            ("empaque.xml", pd.read_xml),
            ("popularidad.html", lambda p: pd.read_html(p)[0]),
            ("impuestos.txt", lambda p: pd.read_csv(p, sep="|"))
        ]

        df_enriched = df_base.copy()

        for filename, loader in file_map:
            df_src = load_source_file(filename, loader)
            if df_src is not None:
                df_enriched = pd.merge(df_enriched, df_src, on="code", how="left")

        num_cols = df_enriched.select_dtypes(include=['float64', 'int64', 'number']).columns
        df_enriched[num_cols] = df_enriched[num_cols].fillna(0.0)

        obj_cols = df_enriched.select_dtypes(include=['object', 'string']).columns
        df_enriched[obj_cols] = df_enriched[obj_cols].fillna("No Aplica")

        df_enriched.to_sql("productos_enriquecidos", conn, if_exists="replace", index=False)

    df_enriched.head(500).to_excel(ENRICHED_XLSX_PATH, index=False)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== REPORTE DE ENRIQUECIMIENTO ===\n")
        f.write(f"Fecha: {datetime.now()}\n")
        f.write(f"Base: {base_count}\n")
        f.write(f"Enriquecidos: {len(df_enriched)}\n")

    print(f"Enriquecimiento finalizado: {len(df_enriched)} registros.")

if __name__ == "__main__":
    main()