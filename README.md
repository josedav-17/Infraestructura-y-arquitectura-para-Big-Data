# Proyecto Integrador Big Data: Ingestión, Limpieza y Enriquecimiento de Datos
## JOSE DAVID CARDONA MAZO
## UNIVERSIDAD DIGITAL DE ANTIOQUIA - 2026

---
# El siguiente proyecto ha sido modificado, adaptado y configurado de acuerdo a las observaciones dadas por el docente en las actividades, el presente readme es una recolección de los pasos dados en las actividades (EA1 - EA2) - Dando como actividad actual EA3

---

---

## 1. Descripción del Proyecto

El presente proyecto implementa un pipeline automatizado de procesamiento de datos (*Data Pipeline*) a gran escala desarrollado en Python. Cubre el ciclo de vida completo de los datos para su posterior modelado y analítica:

1. **EA1 - Ingestión de Datos (API a BD):** Extracción masiva de datos desde APIs REST públicas, almacenamiento en base de datos relacional SQLite (`src/db/ingestion.db`) y base de datos NoSQL MongoDB Atlas, además de la generación de reportes iniciales de auditoría.
2. **EA2 - Limpieza y Procesamiento de Datos:** Tratamiento integral de nulos, eliminación de duplicados por la clave única `code`, acotamiento de valores atípicos (*outliers*) mediante el método del rango intercuartílico (IQR), normalización Min-Max de variables y corrección explícita de tipos sobre el 100% del dataset.
3. **EA3 - Enriquecimiento de Datos:** Integración y cruce de información (*Left Join*) mediante la clave `code` con múltiples fuentes adicionales en diversos formatos (JSON, XLSX, CSV, XML, HTML, TXT) para complementar el dataset base con variables de precios, países, fabricantes, empaques, popularidad e impuestos.

---

## 2. Fuentes de Datos y APIs Utilizadas

- **API Principal:** [OpenFoodFacts API v2](https://world.openfoodfacts.org/)
  - **Endpoint:** `https://world.openfoodfacts.org/api/v2/search?categories_tags=en:beverages`
  - **Método:** HTTP GET
  - **Volumen:** Extracción paginada de **> 1,000 registros** únicos de productos.
- **API de Respaldo (Fallback):** [DummyJSON Products API](https://dummyjson.com/products)
- **Fuentes Complementarias para Enriquecimiento (EA3):**
  - **JSON:** Precios y tiendas asociadas (`precios.json`).
  - **XLSX:** Países de origen y exportadores (`paises.xlsx`).
  - **CSV:** Datos de fabricantes y certificaciones ISO (`fabricantes.csv`).
  - **XML:** Información de empaque y reciclabilidad (`empaque.xml`).
  - **HTML:** Puntuaciones y reseñas de usuarios (`popularidad.html`).
  - **TXT:** Porcentajes de impuestos y categoría fiscal (`impuestos.txt`).

---

## 3. Tecnologías y Librerías Utilizadas

- **Lenguaje:** Python 3.10+
- **Procesamiento e Integración de Datos:** Pandas, OpenPyXL, lxml, html5lib
- **Peticiones HTTP:** Requests
- **Bases de Datos:** SQLite3 (Almacenamiento local estructurado) y PyMongo (MongoDB Atlas)
- **Automatización CI/CD:** GitHub Actions

---

## 4. Estructura del Repositorio

```text
jose_cardona/
├── setup.py
├── README.md
├── .github/
│   └── workflows/
│       └── bigdata.yml
└── src/
    ├── data_sources/            # Fuentes secundarias para la EA3
    │   ├── precios.json
    │   ├── paises.xlsx
    │   ├── fabricantes.csv
    │   ├── empaque.xml
    │   ├── popularidad.html
    │   └── impuestos.txt
    ├── static/
    │   └── auditoria/          # Logs y reportes de trazabilidad
    │       ├── ingestion.txt
    │       ├── cleaning_report.txt
    │       └── enriched_report.txt
    ├── db/
    │   └── ingestion.db        # Base de datos SQLite local
    ├── xlsx/                   # Muestras exportadas en Excel
    │   ├── ingestion.xlsx
    │   ├── cleaned_data.xlsx
    │   └── enriched_data.xlsx
    ├── ingestion.py            # Script EA1: Ingesta masiva
    ├── processing.py           # Script EA2: Limpieza y procesamiento
    └── enrichment.py           # Script EA3: Enriquecimiento
```

---

## 5. Trazabilidad del Pipeline de Datos

```text
[ API REST ]
    │
    ▼
( ingestion.py ) ──► Guardado en SQLite (ingestion.db) & MongoDB
    │            ──► Genera: ingestion.xlsx & ingestion.txt
    ▼
( processing.py ) ──► Lectura de SQLite / MongoDB
    │             ──► Tratamiento de nulos, duplicados, outliers y normalización
    │             ──► Genera: cleaned_data.xlsx & cleaning_report.txt
    ▼
( enrichment.py ) ──► Cruce por 'code' con 6 fuentes externas (JSON, CSV, XML, etc.)
                  ──► Genera: enriched_data.xlsx & enriched_report.txt
```

---

## 6. Instrucciones para Instalación y Ejecución Local

### Paso 1: Clonar el Repositorio
```bash
git https://github.com/josedav-17/Infraestructura-y-arquitectura-para-Big-Data.git
cd Infraestructura-y-arquitectura-para-Big-Data.git
```

### Paso 2: Crear y Activar un Entorno Virtual (Opcional pero recomendado)
```bash
# En Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# En Windows:
python -m venv venv
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias
Instala el proyecto en modo ejecutable utilizando `setup.py`:
```bash
pip install --upgrade pip
pip install -e .
```

### Paso 4: Configurar Variables de Entorno (Opcional para MongoDB)
Si tienes de una instancia de MongoDB, también puedes configurar la variable:
```bash
# En Linux / macOS:
export MONGO_URI="mongodb+srv://alguna:clave@cluster.mongodb.net/"

# En Windows (CMD):
set MONGO_URI="mongodb+srv://alguna:clave@cluster.mongodb.net/"
```
*Nota: Si no se configura `MONGO_URI`, el sistema funcionará de forma completamente autónoma utilizando **SQLite** localmente.*

### Paso 5: Ejecución Secuencial de los Scripts

1. **Ejecutar Ingestión de Datos (EA1):**
   ```bash
   python src/ingestion.py
   ```
   *Extrae >1,000 registros de la API y crea `src/db/ingestion.db`.*

2. **Ejecutar Limpieza y Procesamiento (EA2):**
   ```bash
   python src/processing.py
   ```
   *Limpia la totalidad de los datos y crea `src/xlsx/cleaned_data.xlsx` y el reporte `src/static/auditoria/cleaning_report.txt`.*

3. **Ejecutar Enriquecimiento de Datos (EA3):**
   ```bash
   python src/enrichment.py
   ```
   *Integra las 6 fuentes externas y genera `src/xlsx/enriched_data.xlsx` y `src/static/auditoria/enriched_report.txt`.*

---

## 7. Automatización con GitHub Actions

Este proyecto cuenta con un flujo CI/CD automatizado configurado en `.github/workflows/bigdata.yml`.

### Funcionamiento del Workflow:
- **Disparadores (Triggers):** Se ejecuta automáticamente ante cualquier evento `push` a la rama `main` o de forma manual mediante `workflow_dispatch`.
- **Ambiente:** Ejecutores virtuales Ubuntu (`ubuntu-latest`) con Python 3.10.
- **Pasos del Flujo:**
  1. Clona el repositorio (`actions/checkout@v4`).
  2. Configura el intérprete de Python (`actions/setup-python@v5`).
  3. Instala las dependencias del proyecto (`pip install -e .`).
  4. Ejecuta consecutivamente los tres scripts:
     - `python src/ingestion.py`
     - `python src/processing.py`
     - `python src/enrichment.py`
  5. **Artefactos:** Carga y almacena automáticamente todas las evidencias generadas (`.xlsx` y `.txt`) en la sección de artefactos de GitHub Actions para su descarga y verificación.