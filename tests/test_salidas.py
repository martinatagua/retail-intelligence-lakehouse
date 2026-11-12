"""Las salidas de diagnóstico no deben exponer el bucket ni URI/rutas S3 completas.

El procesamiento usa los valores reales; solo se sanitiza lo que se imprime o se incluye en excepciones.
Los valores de esta prueba son de ejemplo. Sin Spark ni Java: se usan dobles de dbutils y spark.
"""

import re
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "proceso"))

import comun  # noqa: E402

BUCKET = "bucket-privado-de-prueba"
URI_RE = re.compile(r"s3a?://[^\s<]")          # cualquier URI con un bucket que no esté oculto
PARAMS = {"entorno": "dev", "catalogo": "workspace", "esquema_bronze": "dev_bronze", "esquema_silver": "dev_silver",
          "esquema_gold": "dev_gold", "s3_bucket": BUCKET,
          "raw_path_ecommerce": "ecommerce/Ecommerce_Sales_Prediction_Dataset.csv",
          "raw_path_automobiles": "automobiles/Automobile_data.csv"}


@pytest.fixture(autouse=True)
def limpiar_registro():
    comun._valores_ocultos.clear()
    yield
    comun._valores_ocultos.clear()


def dbutils_falso(valores=PARAMS, ls=None):
    widgets = types.SimpleNamespace(text=lambda n, d: None, get=lambda n: valores.get(n, ""))
    fs = types.SimpleNamespace(ls=ls or (lambda ruta: [types.SimpleNamespace(size=1234)]))
    return types.SimpleNamespace(widgets=widgets, fs=fs)


def spark_falso(catalogos=("workspace",)):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [(c,) for c in catalogos]
    spark.catalog.databaseExists.return_value = True
    return spark


def sin_exposicion(texto):
    assert BUCKET not in texto
    assert not URI_RE.search(texto)


# --- Funciones reutilizables -------------------------------------------------------
def test_ocultar_sustituye_bucket_y_uris():
    comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE)
    assert comun.ocultar(f"s3://{BUCKET}/raw/x.csv") == "s3://<bucket>/raw/x.csv"
    assert comun.ocultar(f"Access denied to bucket {BUCKET}") == "Access denied to bucket <bucket>"
    assert comun.ocultar(f"s3a://{'otro-bucket'}/lakehouse") == "s3a://<bucket>/lakehouse"   # conserva el esquema
    assert comun.ocultar("sin rutas") == "sin rutas"
    assert comun.ocultar(Exception(f"s3://{BUCKET}/x")) == "s3://<bucket>/x"


def test_parametros_visibles_no_expone_bucket_ni_rutas_y_no_altera_los_reales():
    p = comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE + ("raw_path_ecommerce",))
    visibles = comun.parametros_visibles(p)
    sin_exposicion(" ".join(f"{k}={v}" for k, v in visibles.items()))
    assert visibles["s3_bucket"] == "<bucket>"
    assert visibles["raw_root"] == "s3://<bucket>/raw"
    assert visibles["catalogo"] == "workspace"
    assert p["raw_root"] == f"s3://{BUCKET}/raw"                  # el procesamiento conserva la ruta real
    assert comun.ruta_raw(p, p["raw_path_ecommerce"]).startswith(f"s3://{BUCKET}/raw/ecommerce/")
    assert comun.ruta_tabla(p, "bronze", "t") == f"s3://{BUCKET}/lakehouse/dev/bronze/t"


def test_sin_rutas_quita_archivo_origen():
    df = MagicMock()
    df.columns = ["a", "_archivo_origen"]
    comun.sin_rutas(df)
    df.drop.assert_called_once_with("_archivo_origen")
    df2 = MagicMock()
    df2.columns = ["a"]
    assert comun.sin_rutas(df2) is df2


def test_errores_de_aislamiento_ocultan_las_rutas():
    p = comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE)
    with pytest.raises(ValueError) as exc:
        comun.validar_aislamiento({**p, "lakehouse_root": f"s3://{BUCKET}/lakehouse/prod"})
    sin_exposicion(str(exc.value))
    with pytest.raises(ValueError) as exc:
        comun.validar_aislamiento({**p, "lakehouse_root": f"s3://{BUCKET}/raw/dev"})
    sin_exposicion(str(exc.value))


# --- escribir_tabla_externa ----------------------------------------------------------
def spark_tabla(ubicacion_existente=None, ubicacion_final=None, tipo="EXTERNAL", ruta=None):
    spark = MagicMock()
    spark.catalog.tableExists.return_value = ubicacion_existente is not None
    detalle = [{"location": ubicacion_existente or ruta}, {"location": ubicacion_final or ruta}]
    spark.sql.return_value.first.side_effect = detalle if ubicacion_existente else [detalle[1]]
    spark.catalog.getTable.return_value.tableType = tipo
    return spark


def test_escribir_tabla_externa_imprime_sin_bucket(capsys):
    p = comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE)
    ruta = comun.ruta_tabla(p, "bronze", "t")
    comun.escribir_tabla_externa(spark_tabla(ruta=ruta), MagicMock(), "`c`.`s`.`t`", ruta)
    sin_exposicion(capsys.readouterr().out)


def test_escribir_tabla_externa_errores_sin_bucket():
    p = comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE)
    ruta = comun.ruta_tabla(p, "bronze", "t")
    otra = f"s3://{BUCKET}/lakehouse/prod/bronze/t"
    with pytest.raises(RuntimeError) as exc:
        comun.escribir_tabla_externa(spark_tabla(ubicacion_existente=otra, ruta=ruta), MagicMock(), "`c`.`s`.`t`", ruta)
    sin_exposicion(str(exc.value))
    with pytest.raises(RuntimeError) as exc:
        comun.escribir_tabla_externa(spark_tabla(tipo="MANAGED", ruta=ruta), MagicMock(), "`c`.`s`.`t`", ruta)
    sin_exposicion(str(exc.value))


# --- Notebook 00_prep_amb ejecutado con dobles ----------------------------------------
def ejecutar_notebook(nombre, dbutils, spark):
    ruta = RAIZ / "proceso" / nombre
    espacio = {"dbutils": dbutils, "spark": spark, "display": lambda *a, **k: None, "__name__": "notebook"}
    exec(compile(ruta.read_text(encoding="utf-8"), str(ruta), "exec"), espacio)
    return espacio


def test_prep_amb_no_imprime_bucket_ni_rutas(capsys):
    espacio = ejecutar_notebook("00_prep_amb.py", dbutils_falso(), spark_falso())
    salida = capsys.readouterr().out
    sin_exposicion(salida)
    assert "<bucket>" in salida and "dev_bronze" in salida          # sigue siendo informativa
    assert espacio["p"]["raw_root"] == f"s3://{BUCKET}/raw"           # pero el proceso usa el valor real


def test_prep_amb_error_al_listar_raw_no_expone_bucket():
    def ls(ruta):
        raise OSError(f"AccessDenied: no se puede leer {ruta} (bucket {BUCKET})")
    with pytest.raises(RuntimeError) as exc:
        ejecutar_notebook("00_prep_amb.py", dbutils_falso(ls=ls), spark_falso())
    sin_exposicion(str(exc.value))
    assert exc.value.__cause__ is None and exc.value.__suppress_context__   # la traza no enseña la excepción original


def test_prep_amb_raw_vacio_no_expone_bucket():
    with pytest.raises(AssertionError) as exc:
        ejecutar_notebook("00_prep_amb.py",
                          dbutils_falso(ls=lambda ruta: [types.SimpleNamespace(size=0)]), spark_falso())
    sin_exposicion(str(exc.value))


def test_prep_amb_con_bucket_invalido_falla_sin_reproducirlo():
    with pytest.raises(ValueError) as exc:
        ejecutar_notebook("00_prep_amb.py", dbutils_falso({**PARAMS, "s3_bucket": f"s3://{BUCKET}/raw"}), spark_falso())
    sin_exposicion(str(exc.value))


def test_prep_amb_sin_bucket_falla_pronto_y_claro():
    with pytest.raises(ValueError, match="s3_bucket"):
        ejecutar_notebook("00_prep_amb.py", dbutils_falso({k: v for k, v in PARAMS.items() if k != "s3_bucket"}),
                          spark_falso())


# --- Regresión: bucket corto (tres caracteres) sin falsos positivos ------------------------------
CORTO = "abc"


@pytest.fixture
def bucket_corto():
    p = comun.leer_parametros(dbutils_falso({**PARAMS, "s3_bucket": CORTO}), comun.PARAMS_BASE)
    assert comun.errores_nombre_bucket(CORTO) == []
    return p


def test_bucket_corto_se_oculta_en_uri_s3(bucket_corto):
    assert comun.ocultar(f"s3://{CORTO}/raw") == "s3://<bucket>/raw"
    assert comun.ocultar(f"s3a://{CORTO}/lakehouse/dev/bronze/t") == "s3a://<bucket>/lakehouse/dev/bronze/t"
    assert comun.ocultar(f"fallo leyendo s3://{CORTO}/raw/x.csv, intento 2") == "fallo leyendo s3://<bucket>/raw/x.csv, intento 2"
    assert comun.ocultar(f"s3://{CORTO}") == "s3://<bucket>"


@pytest.mark.parametrize("texto", [
    "El identificador abc123 fue procesado",
    "xabc, abcx, abcabc, abc_1, abc-1, mi-abc, mi_abc, mi.abc, abc.def",
    "Tabla ecommerce_abc_ventas lista",
    "Ábaco y abacus no cambian",
    "123abc",
])
def test_bucket_corto_no_modifica_subcadenas_de_texto_ordinario(bucket_corto, texto):
    assert comun.ocultar(texto) == texto


def test_bucket_corto_como_valor_explicito_de_s3_bucket_se_oculta(bucket_corto):
    visibles = comun.parametros_visibles({**bucket_corto, "nota": "abc123 procesado"})
    assert visibles["s3_bucket"] == "<bucket>"
    assert visibles["raw_root"] == "s3://<bucket>/raw"
    assert visibles["lakehouse_root"] == "s3://<bucket>/lakehouse/dev"
    assert visibles["nota"] == "abc123 procesado"              # el resto de valores no se altera
    assert bucket_corto["s3_bucket"] == CORTO and bucket_corto["raw_root"] == f"s3://{CORTO}/raw"   # valores reales intactos


def test_parametros_visibles_oculta_s3_bucket_aunque_no_este_registrado():
    assert comun.parametros_visibles({"s3_bucket": "xy1"})["s3_bucket"] == "<bucket>"


def test_bucket_corto_aislado_como_token_se_oculta_pero_no_dentro_de_palabras(bucket_corto):
    assert comun.ocultar("AccessDenied en el bucket abc.") == "AccessDenied en el bucket <bucket>."
    assert comun.ocultar("bucket 'abc' no existe") == "bucket '<bucket>' no existe"
    assert comun.ocultar("abc123 y abc") == "abc123 y <bucket>"


@pytest.mark.parametrize("mensaje", [
    "CHECK OK  catálogo 'workspace' accesible",
    "Falta el parámetro obligatorio 's3_bucket'. Configura BUNDLE_VAR_s3_bucket",
    "OK  `workspace`.`dev_bronze`.`t`  ->  tabla externa",
    "",
])
def test_mensajes_sin_rutas_s3_permanecen_identicos(bucket_corto, mensaje):
    assert comun.ocultar(mensaje) == mensaje


def test_la_sanitizacion_previa_sigue_funcionando_con_bucket_largo():
    comun.leer_parametros(dbutils_falso(), comun.PARAMS_BASE)
    assert comun.ocultar(f"s3://{BUCKET}/raw/x.csv") == "s3://<bucket>/raw/x.csv"
    assert comun.ocultar(f"Access denied to bucket {BUCKET}") == "Access denied to bucket <bucket>"


# --- Cobertura permanente de ocultar(): salidas exactas con el bucket `abc` --------------------------
# Cada caso: (texto de entrada, salida exacta esperada).
def _x(texto):
    """Expande <S3> y <S3A>: así este archivo no contiene URI literales (el validador solo admite marcadores documentales)."""
    return texto.replace("<S3A>", "s3a:" + "//").replace("<S3>", "s3:" + "//")


CASOS_OCULTAR = [
    # subcadenas dentro de texto ordinario: sin cambios
    ("abc123", "abc123"),
    ("xabc", "xabc"),
    ("abcabc", "abcabc"),
    ("abc_1", "abc_1"),
    ("mi-abc", "mi-abc"),
    ("mi.abc", "mi.abc"),
    ("123abc", "123abc"),
    ("El identificador abc123 fue procesado", "El identificador abc123 fue procesado"),
    # token aislado y con puntuación
    ("abc", "<bucket>"),
    ("bucket abc", "bucket <bucket>"),
    ("(abc),", "(<bucket>),"),
    ("bucket 'abc'.", "bucket '<bucket>'."),
    # URI: esquema original, ruta, archivo y puntuación posterior
    ("<S3>abc/raw", "<S3><bucket>/raw"),
    ("<S3A>abc/raw/file.csv", "<S3A><bucket>/raw/file.csv"),
    ("<S3A>abc", "<S3A><bucket>"),
    ("<S3>abc", "<S3><bucket>"),
    ("<S3>abc/lakehouse/dev/bronze/ecommerce_ventas", "<S3><bucket>/lakehouse/dev/bronze/ecommerce_ventas"),
    ("fallo en <S3A>abc/raw/file.csv, reintento", "fallo en <S3A><bucket>/raw/file.csv, reintento"),
    ("leer (<S3>abc/raw).", "leer (<S3><bucket>/raw)."),
    ("ver <S3A>abc.", "ver <S3A><bucket>."),
    ("<S3>abc: acceso denegado", "<S3><bucket>: acceso denegado"),
    ("'<S3A>abc/raw'", "'<S3A><bucket>/raw'"),
    # dos URI en una frase (también con esquemas distintos)
    ("de <S3>abc/raw a <S3>abc/lakehouse", "de <S3><bucket>/raw a <S3><bucket>/lakehouse"),
    ("de <S3A>abc/raw a <S3>abc/lakehouse", "de <S3A><bucket>/raw a <S3><bucket>/lakehouse"),
    # URI de otro bucket: también se oculta el bucket, con su esquema
    ("<S3A>otro-bucket/x", "<S3A><bucket>/x"),
    # sin URI ni bucket: idéntico
    ("", ""),
    ("CHECK OK  catálogo 'workspace' accesible", "CHECK OK  catálogo 'workspace' accesible"),
    ("Tabla ecommerce_abc_ventas lista", "Tabla ecommerce_abc_ventas lista"),
    # ya ocultos: idempotente
    ("<S3A><bucket>/raw", "<S3A><bucket>/raw"),
]


@pytest.mark.parametrize("texto, esperado", CASOS_OCULTAR, ids=[c[0] or "vacío" for c in CASOS_OCULTAR])
def test_ocultar_salida_exacta_con_bucket_abc(bucket_corto, texto, esperado):
    assert comun.ocultar(_x(texto)) == _x(esperado)


def test_ocultar_es_idempotente(bucket_corto):
    for texto, _ in CASOS_OCULTAR:
        una_vez = comun.ocultar(_x(texto))
        assert comun.ocultar(una_vez) == una_vez


def test_ocultar_no_altera_las_rutas_funcionales(bucket_corto):
    assert bucket_corto["raw_root"] == _x("<S3>abc/raw")
    assert comun.ruta_raw(bucket_corto, "ecommerce/x.csv") == _x("<S3>abc/raw/ecommerce/x.csv")
    assert comun.ruta_tabla(bucket_corto, "gold", "t") == _x("<S3>abc/lakehouse/dev/gold/t")
    comun.ocultar(comun.ruta_raw(bucket_corto, "x.csv"))
    assert comun.ruta_raw(bucket_corto, "x.csv") == _x("<S3>abc/raw/x.csv")


def test_parametros_visibles_exacto_con_bucket_abc(bucket_corto):
    p = {**bucket_corto, "raw_path_ecommerce": "ecommerce/abc123.csv", "nota": "El identificador abc123 fue procesado"}
    assert comun.parametros_visibles(p) == {
        **{k: v for k, v in p.items() if k not in ("s3_bucket", "raw_root", "lakehouse_root")},
        "s3_bucket": "<bucket>",
        "raw_root": "s3://<bucket>/raw",
        "lakehouse_root": "s3://<bucket>/lakehouse/dev",
    }
