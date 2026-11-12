"""Datos SINTÉTICOS con el esquema de Automobiles, solo para pruebas.

NO son el dataset Automobile ni una copia parcial, resumida o derivada de él: las 12 filas se inventaron a mano para este
repositorio (marcas ficticias «fabrica-*», valores arbitrarios). Existen porque el CSV original de Automobiles no se versiona
(ver datasets/README.md) y las pruebas públicas deben ejecutarse en un clon sin ese archivo.

Cubren las reglas de transformaciones.py: marcador `?` en columnas enteras, decimales, de palabras y de precio; todas las palabras
de cilindros; varias carrocerías y combustibles; y filas distintas entre sí. Los resultados esperados están en
tests/test_transformaciones.py y tests/test_dashboard_sql.py, calculados a mano a partir de esta tabla.
"""

import csv
from pathlib import Path

# Mismo contrato de columnas RAW que proceso/transformaciones.py (COLS_RAW_AUTOMOBILES); se comprueba en las pruebas.
COLUMNAS = (
    "symboling", "normalized-losses", "make", "fuel-type", "aspiration",
    "num-of-doors", "body-style", "drive-wheels", "engine-location",
    "wheel-base", "length", "width", "height", "curb-weight", "engine-type",
    "num-of-cylinders", "engine-size", "fuel-system", "bore", "stroke",
    "compression-ratio", "horsepower", "peak-rpm", "city-mpg", "highway-mpg",
    "price",
)

# marca, combustible, carrocería, cilindros, puertas, precio, caballos, pérdidas normalizadas, bore, stroke, rpm
ESPECIFICACIONES = [
    ("fabrica-alfa", "gas", "sedan", "four", "four", "10000", "100", "100", "3.1", "3.2", "5000"),
    ("fabrica-alfa", "gas", "sedan", "four", "two", "12000", "110", "?", "3.1", "3.2", "5200"),
    ("fabrica-alfa", "gas", "hatchback", "three", "two", "?", "80", "90", "2.9", "3.0", "5400"),
    ("fabrica-beta", "diesel", "sedan", "four", "four", "15000", "95", "120", "3.4", "3.5", "4400"),
    ("fabrica-beta", "gas", "wagon", "six", "four", "20000", "150", "110", "?", "?", "5600"),
    ("fabrica-beta", "diesel", "wagon", "five", "four", "18000", "?", "130", "3.3", "3.4", "?"),
    ("fabrica-gamma", "gas", "hardtop", "eight", "two", "30000", "200", "?", "3.8", "3.1", "5000"),
    ("fabrica-gamma", "gas", "hardtop", "twelve", "two", "?", "250", "150", "3.6", "3.3", "5800"),
    ("fabrica-gamma", "gas", "sedan", "two", "?", "25000", "180", "140", "3.5", "3.2", "6000"),
    ("fabrica-delta", "gas", "hatchback", "four", "two", "9000", "70", "85", "3.0", "3.1", "4800"),
    ("fabrica-delta", "diesel", "hatchback", "four", "four", "11000", "75", "95", "3.2", "3.3", "4500"),
    ("fabrica-delta", "gas", "hatchback", "three", "two", "8000", "60", "80", "2.8", "2.9", "5100"),
]

# Resultados que se derivan a mano de ESPECIFICACIONES (las pruebas los comparan con lo que calcula el código).
FILAS = len(ESPECIFICACIONES)                                   # 12
MARCAS = 4
COMBINACIONES_CARROCERIA_COMBUSTIBLE = 7                        # sedan-gas/diesel, hatchback-gas/diesel, wagon-gas/diesel, hardtop-gas
SIN_PRECIO = 2
NULOS_SILVER = {"normalized_losses": 2, "num_of_doors": 1, "bore": 1, "stroke": 1,
                "horsepower": 1, "peak_rpm": 1, "price": 2}
CILINDROS = {2, 3, 4, 5, 6, 8, 12}


def filas_raw():
    """Filas completas (26 columnas, todo texto, como en RAW) construidas de forma determinista."""
    filas = []
    for i, (marca, comb, carroceria, cilindros, puertas, precio, caballos, perdidas, bore, stroke, rpm) in enumerate(ESPECIFICACIONES):
        filas.append((
            str(i % 4 - 1), perdidas, marca, comb, "std" if i % 3 else "turbo", puertas, carroceria,
            "fwd" if i % 2 else "rwd", "front", f"{90 + i}.5", f"{160 + 3 * i}.0", f"{64 + i % 4}.2", f"{52 + i % 5}.1",
            str(2000 + 15 * i), "ohc", cilindros, str(100 + 4 * i), "mpfi", bore, stroke,
            f"{8 + i % 3}.0", caballos, rpm, str(20 + i), str(28 + i), precio,
        ))
    return filas


def escribir_csv(destino):
    """Escribe el CSV sintético (cabecera RAW de Automobiles) en `destino` y devuelve su ruta."""
    destino = Path(destino)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        w.writerows(filas_raw())
    return destino
