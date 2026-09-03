from setuptools import setup, find_packages

setup(
    name="ingestion_bigdata",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "pymongo",
        "openpyxl"
    ],
)