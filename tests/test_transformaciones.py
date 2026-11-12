"""Pruebas locales de proceso/transformaciones.py.

No usa Databricks, S3 ni Delta: comprueba la lógica DataFrame (tipos, nulos,
conciliación Gold). Requiere Java 17 (PySpark lo instala uv):
    uv sync --locked && uv run pytest -q

Fuentes de datos:
  - E-commerce: el CSV de datasets/ecommerce/, que sí se versiona.
  - Automobiles: el CSV original NO se versiona (ver datasets/README.md), así que las pruebas públicas usan datos
    SINTÉTICOS (tests/datos_sinteticos.py). Las pruebas `*_csv_real` son opcionales y locales: solo se ejecutan si el archivo
    original está en su ubicación; en un clon limpio (y en el CI) se omiten con un motivo explícito y no cuentan como ejecutadas.
"""

import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession, functions as F

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "proceso"))
sys.path.insert(0, str(RAIZ / "tests"))

import comun  # noqa: E402
import datos_sinteticos as DS  # noqa: E402
import transformaciones as T  # noqa: E402

CSV_ECOMMERCE = RAIZ / "datasets/ecommerce/Ecommerce_Sales_Prediction_Dataset.csv"
CSV_AUTOMOBILES = RAIZ / "datasets/automobiles/Automobile_data.csv"

requiere_csv_automobiles = pytest.mark.skipif(
    not CSV_AUTOMOBILES.exists(),
    reason="OPCIONAL LOCAL: falta datasets/automobiles/Automobile_data.csv, que no se versiona (ver datasets/README.md). "
           "La cobertura pública de Automobiles son las pruebas con datos sintéticos; esta no se ejecutó.")


@pytest.fixture(scope="session")
def spark():
    s = (SparkSession.builder.master("local[2]").appName("tests")
         .config("spark.sql.ansi.enabled", "true")  # como serverless
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.ui.enabled", "false").getOrCreate())
    yield s
    s.stop()


def leer(spark, ruta):
    return (spark.read.format("csv").option("header", "true").option("inferSchema", "false")
            .option("mode", "FAILFAST").load(str(ruta)))


@pytest.fixture(scope="session")
def ecommerce(spark):
    raw = leer(spark, CSV_ECOMMERCE)
    comun.validar_columnas(raw, T.COLS_RAW_ECOMMERCE, "test")
    return T.silver_ecommerce(T.a_bronze(raw, "test"))


def _silver_automobiles(spark, ruta):
    raw = leer(spark, ruta)
    comun.validar_columnas(raw, T.COLS_RAW_AUTOMOBILES, "test")
    raw = raw.toDF(*[T.snake(c) for c in raw.columns])
    return T.silver_automobiles(T.a_bronze(raw, "test"))


@pytest.fixture(scope="session")
def autos_sinteticos(spark, tmp_path_factory):
    """Silver de Automobiles a partir de un CSV sintético escrito en un directorio temporal."""
    ruta = DS.escribir_csv(tmp_path_factory.mktemp("sintetico") / "automobiles_sintetico.csv")
    return _silver_automobiles(spark, ruta)


@pytest.fixture(scope="session")
def autos(spark):
    """Silver de Automobiles desde el CSV original. Solo para las pruebas opcionales locales (`*_csv_real`)."""
    return _silver_automobiles(spark, CSV_AUTOMOBILES)


def test_ecommerce_silver(ecommerce):
    assert ecommerce.count() == 1000
    comun.validar_tipos(ecommerce, T.TIPOS_SILVER_ECOMMERCE, "test")
    assert set(comun.conteo_nulos(ecommerce, list(T.TIPOS_SILVER_ECOMMERCE)).values()) == {0}
    r = ecommerce.agg(F.min("fecha"), F.max("fecha")).first()
    assert (str(r[0]), str(r[1])) == ("2023-01-01", "2025-09-26")
    assert ecommerce.first()["_archivo_origen"].endswith("Ecommerce_Sales_Prediction_Dataset.csv")


def test_contrato_de_columnas_sintetico_coincide_con_transformaciones():
    assert DS.COLUMNAS == T.COLS_RAW_AUTOMOBILES


def test_fixture_sintetico_no_es_el_dataset_original():
    """Las filas sintéticas son inventadas: marcas ficticias y un tamaño distinto del dataset original (205 filas)."""
    assert DS.FILAS == 12 != 205
    assert all(f[2].startswith("fabrica-") for f in DS.filas_raw())


@requiere_csv_automobiles
def test_fixture_sintetico_no_aparece_en_el_csv_original():
    original = CSV_AUTOMOBILES.read_text(encoding="utf-8")
    assert not any("fabrica-" in linea for linea in original.splitlines())
    assert not any(",".join(f) in original for f in DS.filas_raw())


def test_automobiles_silver_sintetico(autos_sinteticos):
    assert autos_sinteticos.count() == DS.FILAS
    comun.validar_tipos(autos_sinteticos, T.TIPOS_SILVER_AUTOMOBILES, "test")
    nulos = {c: n for c, n in comun.conteo_nulos(autos_sinteticos, list(T.COLS_BRONZE_AUTOMOBILES)).items() if n}
    assert nulos == DS.NULOS_SILVER
    assert {r[0] for r in autos_sinteticos.select("num_of_cylinders").distinct().collect()} == DS.CILINDROS
    assert autos_sinteticos.select("registro_hash").distinct().count() == DS.FILAS
    assert autos_sinteticos.first()["_archivo_origen"].endswith("automobiles_sintetico.csv")


def test_marcador_de_ausente_se_convierte_a_nulo_en_silver_sintetico(autos_sinteticos):
    sin_precio = autos_sinteticos.filter(F.col("price").isNull()).select("make").collect()
    assert sorted(r[0] for r in sin_precio) == ["fabrica-alfa", "fabrica-gamma"]
    assert autos_sinteticos.filter(F.col("num_of_doors").isNull()).count() == 1


@requiere_csv_automobiles
def test_automobiles_silver_csv_real(autos):
    assert autos.count() == 205
    comun.validar_tipos(autos, T.TIPOS_SILVER_AUTOMOBILES, "test")
    nulos = {c: n for c, n in comun.conteo_nulos(autos, list(T.COLS_BRONZE_AUTOMOBILES)).items() if n}
    assert nulos == {"normalized_losses": 41, "num_of_doors": 2, "bore": 4, "stroke": 4,
                     "horsepower": 2, "peak_rpm": 2, "price": 4}
    assert {r[0] for r in autos.select("num_of_cylinders").distinct().collect()} == {2, 3, 4, 5, 6, 8, 12}
    assert autos.select("registro_hash").distinct().count() == 205


def test_valor_invalido_queda_nulo_sin_error(spark):
    df = spark.createDataFrame([("12",), ("1x",), ("?",)], ["v"])
    assert [r[0] for r in df.select(T.a_entero("v")).collect()] == [12, None, None]


def test_gold_ecommerce_concilia(ecommerce):
    unidades = ecommerce.agg(F.sum("units_sold")).first()[0]
    mensual = T.gold_ecommerce_mensual_categoria(ecommerce)
    segmento = T.gold_ecommerce_segmento_categoria(ecommerce)
    assert mensual.agg(F.sum("unidades_vendidas")).first()[0] == unidades
    assert segmento.agg(F.sum("unidades_vendidas")).first()[0] == unidades
    assert segmento.count() == 15  # 3 segmentos x 5 categorías
    assert not any(c.startswith("precio_neto") for c in mensual.columns)


def test_gold_ecommerce_precio_neto_solo_si_se_declara(ecommerce):
    cols = T.gold_ecommerce_mensual_categoria(ecommerce, "porcentaje").columns
    assert "precio_neto_promedio_porcentaje" in cols
    with pytest.raises(ValueError):
        T.gold_ecommerce_mensual_categoria(ecommerce, "otra")


def test_gold_automobiles_concilia_sintetico(autos_sinteticos):
    marca = T.gold_automobiles_resumen_marca(autos_sinteticos)
    assert marca.count() == DS.MARCAS
    assert marca.agg(F.sum("registros")).first()[0] == DS.FILAS
    assert marca.agg(F.sum("registros_sin_precio")).first()[0] == DS.SIN_PRECIO
    carroceria = T.gold_automobiles_carroceria_combustible(autos_sinteticos)
    assert carroceria.count() == DS.COMBINACIONES_CARROCERIA_COMBUSTIBLE
    assert carroceria.agg(F.sum("registros")).first()[0] == DS.FILAS


@requiere_csv_automobiles
def test_gold_automobiles_concilia_csv_real(autos):
    marca = T.gold_automobiles_resumen_marca(autos)
    assert marca.count() == 22
    assert marca.agg(F.sum("registros")).first()[0] == 205
    assert marca.agg(F.sum("registros_sin_precio")).first()[0] == 4
    assert T.gold_automobiles_carroceria_combustible(autos).agg(F.sum("registros")).first()[0] == 205


def test_inventario_gold_coincide_con_funciones():
    assert len(comun.TABLAS["gold"]) == 4
