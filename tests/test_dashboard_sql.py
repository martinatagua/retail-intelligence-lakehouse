"""Las consultas de dashboard/sql/ se ejecutan contra las tablas Gold generadas en local.

Comprueba que todas las columnas existen y que los indicadores cuadran con Silver.
Las tablas se registran como vistas temporales: el prefijo workspace.dev_gold. se
elimina, porque el Spark local no tiene catálogo Unity Catalog. Requiere Java 17.

E-commerce usa su CSV versionado. Automobiles se prueba con datos SINTÉTICOS (tests/datos_sinteticos.py), porque el CSV original
no se versiona; con el CSV original presente se repite además como prueba opcional local (parámetro `real`), que en un clon
limpio se omite con un motivo explícito y no cuenta como ejecutada.
"""

import re
import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "proceso"))
sys.path.insert(0, str(RAIZ / "tests"))

import comun  # noqa: E402
import datos_sinteticos as DS  # noqa: E402
import transformaciones as T  # noqa: E402

SQL = sorted((RAIZ / "dashboard" / "sql").glob("*.sql"))
PREFIJO = "workspace.dev_gold."
CSV_AUTOMOBILES = RAIZ / "datasets/automobiles/Automobile_data.csv"
# Filas esperadas por consulta. 01, 02, 05 (E-commerce) no dependen de la fuente de Automobiles.
FILAS = {
    "sintetico": {"01": 165, "02": 15, "03": DS.MARCAS, "04": DS.COMBINACIONES_CARROCERIA_COMBUSTIBLE, "05": 1, "06": 1},
    "real": {"01": 165, "02": 15, "03": 22, "04": 9, "05": 1, "06": 1},
}


@pytest.fixture(scope="module", params=["sintetico", "real"])
def fuente(request):
    """Fuente de Automobiles: `sintetico` (siempre) o `real` (opcional local: el CSV original no se versiona)."""
    if request.param == "real" and not CSV_AUTOMOBILES.exists():
        pytest.skip("OPCIONAL LOCAL: falta datasets/automobiles/Automobile_data.csv, que no se versiona (ver datasets/README.md). "
                    "La cobertura pública usa datos sintéticos; esta variante no se ejecutó.")
    return request.param


@pytest.fixture(scope="module")
def spark(fuente, tmp_path_factory):
    s = (SparkSession.builder.master("local[2]").appName("tests-dashboard")
         .config("spark.sql.ansi.enabled", "true")
         .config("spark.ui.enabled", "false").getOrCreate())
    leer = lambda p: s.read.option("header", "true").option("inferSchema", "false").csv(str(p))  # noqa: E731
    if fuente == "real":
        ruta_autos = CSV_AUTOMOBILES
    else:
        ruta_autos = DS.escribir_csv(tmp_path_factory.mktemp("sintetico") / "automobiles_sintetico.csv")
    autos = leer(ruta_autos)
    autos = autos.toDF(*[T.snake(c) for c in autos.columns])
    eco = T.silver_ecommerce(T.a_bronze(leer(RAIZ / "datasets/ecommerce/Ecommerce_Sales_Prediction_Dataset.csv"), "t"))
    aut = T.silver_automobiles(T.a_bronze(autos, "t"))
    gold = {
        "ecommerce_ventas_mensuales_categoria": T.gold_ecommerce_mensual_categoria(eco),
        "ecommerce_ventas_segmento_categoria": T.gold_ecommerce_segmento_categoria(eco),
        "automobiles_resumen_marca": T.gold_automobiles_resumen_marca(aut),
        "automobiles_resumen_carroceria_combustible": T.gold_automobiles_carroceria_combustible(aut),
    }
    assert set(gold) == set(comun.TABLAS["gold"])
    for nombre, df in gold.items():
        df.createOrReplaceTempView(nombre)
    yield s


def ejecutar(spark, archivo):
    texto = archivo.read_text(encoding="utf-8")
    assert PREFIJO in texto, f"{archivo.name}: debe consultar {PREFIJO}<tabla>"
    for tabla in re.findall(re.escape(PREFIJO) + r"(\w+)", texto):
        assert tabla in comun.TABLAS["gold"], f"{archivo.name}: {tabla} no es una tabla Gold"
    return spark.sql(texto.replace(PREFIJO, "")).collect()


def test_hay_una_consulta_por_tabla_gold():
    tablas = {t for f in SQL for t in re.findall(re.escape(PREFIJO) + r"(\w+)", f.read_text())}
    assert tablas == set(comun.TABLAS["gold"])


@pytest.mark.parametrize("archivo", SQL, ids=[f.name for f in SQL])
def test_consulta_ejecuta(spark, fuente, archivo):
    filas = ejecutar(spark, archivo)
    assert len(filas) == FILAS[fuente][archivo.name[:2]]


def test_kpis_concilian(spark, fuente):
    eco = ejecutar(spark, RAIZ / "dashboard/sql/05_kpi_ecommerce.sql")[0]
    assert eco["unidades_vendidas_total"] == 29631 and eco["registros_silver"] == 1000
    aut = ejecutar(spark, RAIZ / "dashboard/sql/06_kpi_automobiles.sql")[0]
    esperado = (DS.FILAS, DS.SIN_PRECIO, DS.MARCAS) if fuente == "sintetico" else (205, 4, 22)
    assert (aut["vehiculos"], aut["vehiculos_sin_precio"], aut["marcas"]) == esperado
