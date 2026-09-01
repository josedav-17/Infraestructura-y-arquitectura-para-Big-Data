# Proyecto de Ingesta de Datos desde API

## 1. Descripción

El presente proyecto implementa un proceso de extracción, transformación,
almacenamiento y validación de datos obtenidos desde una API REST pública.

El objetivo es automatizar la obtención de información desde una fuente
externa, almacenarla en una base de datos SQLite y generar archivos de
evidencia que permitan comprobar la integridad de los datos.

---

## 2. API utilizada

Para el desarrollo del proyecto se seleccionó JSONPlaceholder, una API REST
pública utilizada para pruebas y desarrollo.

Endpoint utilizado:

https://jsonplaceholder.typicode.com/posts

La consulta se realiza mediante el método HTTP GET.

La respuesta contiene información de publicaciones con los siguientes campos:

- id
- userId
- title
- body

La API no requiere autenticación para realizar la consulta.

---

## 3. Tecnologías utilizadas

El proyecto utiliza las siguientes tecnologías:

- Python 3.12
- Requests
- Pandas
- SQLite
- OpenPyXL
- GitHub Actions

---

## 4. Estructura del proyecto

```text
nombre_apellido/
│
├── setup.py
├── README.md
│
├── .github/
│   └── workflows/
│       └── bigdata.yml
│
└── src/
    ├── static/
    │   └── auditoria/
    │       └── ingestion.txt
    │
    ├── db/
    │   └── ingestion.db
    │
    ├── xlsx/
    │   └── ingestion.xlsx
    │
    └── ingestion.py