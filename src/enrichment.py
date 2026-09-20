import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "db", "ingestion.db")
SOURCES_DIR = os.path.join(BASE_DIR, "data_sources")
ENRICHED_XLSX_PATH = os.path.join(BASE_DIR, "xlsx", "enriched_data.xlsx")
REPORT_PATH = os.path.join(BASE_DIR, "static", "auditoria", "enriched_report.txt")

def main():
    os.makedirs(os.path.dirname(ENRICHED_XLSX_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        df_base = pd.read_sql_query("SELECT * FROM productos_limpios", conn)
    except Exception:
        df_base = pd.read_sql_query("SELECT * FROM productos", conn)

    df_base["code"] = df_base["code"].astype(str).str.strip()
    cant_base = len(df_base)
    cols_base = len(df_base.columns)

    fuentes = []

    f_json = os.path.join(SOURCES_DIR, "precios.json")
    if os.path.exists(f_json):
        df_j = pd.read_json(f_json)
        df_j["code"] = df_j["code"].astype(str).str.strip()
        fuentes.append(("JSON Precios", df_j))

    f_xlsx = os.path.join(SOURCES_DIR, "paises.xlsx")
    if os.path.exists(f_xlsx):
        df_x = pd.read_excel(f_xlsx)
        df_x["code"] = df_x["code"].astype(str).str.strip()
        fuentes.append(("XLSX Paises", df_x))

    f_csv = os.path.join(SOURCES_DIR, "fabricantes.csv")
    if os.path.exists(f_csv):
        df_c = pd.read_csv(f_csv)
        df_c["code"] = df_c["code"].astype(str).str.strip()
        fuentes.append(("CSV Fabricantes", df_c))

    f_xml = os.path.join(SOURCES_DIR, "empaque.xml")
    if os.path.exists(f_xml):
        df_m = pd.read_xml(f_xml)
        df_m["code"] = df_m["code"].astype(str).str.strip()
        fuentes.append(("XML Empaque", df_m))

    f_html = os.path.join(SOURCES_DIR, "popularidad.html")
    if os.path.exists(f_html):
        df_h = pd.read_html(f_html)[0]
        df_h["code"] = df_h["code"].astype(str).str.strip()
        fuentes.append(("HTML Popularidad", df_h))

    f_txt = os.path.join(SOURCES_DIR, "impuestos.txt")
    if os.path.exists(f_txt):
        df_t = pd.read_csv(f_txt, sep="|")
        df_t["code"] = df_t["code"].astype(str).str.strip()
        fuentes.append(("TXT Impuestos", df_t))

    df_final = df_base.copy()
    logs = []

    for nombre, df_f in fuentes:
        df_f = df_f.drop_duplicates(subset=["code"], keep="first")
        df_final = pd.merge(df_final, df_f, on="code", how="left")
        
        col_ref = df_f.columns[1] if len(df_f.columns) > 1 else "code"
        coincidencias = df_final[col_ref].notna().sum()
        logs.append(f"{nombre}: {len(df_f)} registros leidos, {coincidencias} coincidencias.")

    num_cols = df_final.select_dtypes(include=['float64', 'int64']).columns
    df_final[num_cols] = df_final[num_cols].fillna(0.0)

    obj_cols = df_final.select_dtypes(include=['object', 'string', 'str']).columns
    df_final[obj_cols] = df_final[obj_cols].fillna("No Aplica")

    df_final.to_sql("productos_enriquecidos", conn, if_exists="replace", index=False)
    conn.close()

    df_final.to_excel(ENRICHED_XLSX_PATH, index=False)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("REPORTE DE AUDITORIA DE ENRIQUECIMIENTO (EA3)\n")
        f.write(f"Fecha: {datetime.now()}\n")
        f.write(f"Registros base: {cant_base}\n")
        f.write(f"Registros finales: {len(df_final)}\n")
        f.write(f"Columnas iniciales: {cols_base}\n")
        f.write(f"Columnas finales: {len(df_final.columns)}\n\n")
        f.write("Detalle de las fuentes unidas:\n")
        for log in logs:
            f.write(f"{log}\n")

    print("Proceso de enriquecimiento finalizado con exito.")

if __name__ == "__main__":
    main()