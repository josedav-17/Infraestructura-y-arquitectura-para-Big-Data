from setuptools import setup, find_packages

setup(
    name="jose_cardona_bigdata",
    version="0.3",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "pymongo",
        "openpyxl",
        "lxml",
        "html5lib"
    ],
)