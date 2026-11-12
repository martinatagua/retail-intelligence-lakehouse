"""Pruebas de parámetros y aislamiento dev/prod de proceso/comun.py (sin Spark)."""

import sys
import types
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "proceso"))

import comun  # noqa: E402

BASE = {
    "catalogo": "cat",
    "s3_bucket": "example-retail-bucket",
}
DEV = {**BASE, "entorno": "dev", "esquema_bronze": "dev_bronze", "esquema_silver": "dev_silver",
       "esquema_gold": "dev_gold", "lakehouse_root": "s3://example-retail-bucket/lakehouse/dev",
       "raw_root": "s3://example-retail-bucket/raw"}
PROD = {**BASE, "entorno": "prod", "esquema_bronze": "bronze", "esquema_silver": "silver",
        "esquema_gold": "gold", "lakehouse_root": "s3://example-retail-bucket/lakehouse/prod",
        "raw_root": "s3://example-retail-bucket/raw"}


def dbutils_falso(valores):
    widgets = types.SimpleNamespace(text=lambda n, d: None, get=lambda n: valores.get(n, ""))
    return types.SimpleNamespace(widgets=widgets)


@pytest.mark.parametrize("p", [DEV, PROD])
def test_aislamiento_valido(p):
    comun.validar_aislamiento(p)


@pytest.mark.parametrize("cambio", [
    {"entorno": "dev", "esquema_gold": "gold"},                                         # dev -> esquema prod
    {"entorno": "dev", "lakehouse_root": PROD["lakehouse_root"]},                       # dev -> ruta prod
    {"entorno": "prod", "esquema_bronze": "dev_bronze"},                                # prod -> esquema dev
    {"entorno": "prod", "lakehouse_root": "s3://<nombre-del-bucket>/lakehouse"},
    {"entorno": "test"},
])
def test_aislamiento_violado(cambio):
    base = DEV if cambio.get("entorno") == "dev" else PROD
    with pytest.raises(ValueError):
        comun.validar_aislamiento({**base, **cambio})


def test_leer_parametros_exige_entorno_y_normaliza():
    valores = {**DEV, "lakehouse_root": DEV["lakehouse_root"]}
    p = comun.leer_parametros(dbutils_falso(valores), comun.PARAMS_BASE)
    assert p["entorno"] == "dev" and p["esquema_bronze"] == "dev_bronze"
    with pytest.raises(ValueError, match="entorno"):
        comun.leer_parametros(dbutils_falso({k: v for k, v in DEV.items() if k != "entorno"}), comun.PARAMS_BASE)


def test_bucket_s3_obligatorio_y_deriva_rutas():
    valores = {k: v for k, v in DEV.items() if k != "raw_root" and k != "lakehouse_root"}
    p = comun.leer_parametros(dbutils_falso(valores), comun.PARAMS_BASE)
    assert p["raw_root"] == "s3://example-retail-bucket/raw"
    assert p["lakehouse_root"] == "s3://example-retail-bucket/lakehouse/dev"
    with pytest.raises(ValueError, match="s3_bucket"):
        comun.leer_parametros(dbutils_falso({k: v for k, v in valores.items() if k != "s3_bucket"}), comun.PARAMS_BASE)


S3 = "s3://"   # las muestras con URI se construyen por partes: el validador no admite URI literales en tests
BUCKETS_VALIDOS = [
    "mi-bucket", "example-retail-bucket", "abc", "a1b", "datos.retail.2026", "bucket-con-numeros-123",
    "a" * 63, "a-b", "1.2.3", "1.2.3.4.5", "bucket-s3", "mi-bucket-s3alias2", "mi.mrap.datos",
    "tabla-s3-datos", "xn-bucket", "sthree", "amzn-s3-demo", "mi--x-datos",
]
# (valor, fragmento del motivo que debe aparecer en el error)
BUCKETS_INVALIDOS = [
    (S3 + "mi-bucket", "sin s3://"), (S3 + "mi-bucket/raw", "sin s3://"), ("s3a:" + "//mi-bucket", "sin s3://"),
    ("mi-bucket/raw", "sin s3://"), ("dbfs:/raw", "sin s3://"), ("/mi-bucket", "sin s3://"),
    ("MiBucket", "mayúsculas"), ("MI-BUCKET", "mayúsculas"),
    ("ab", "entre 3 y 63"), ("a", "entre 3 y 63"), ("a" * 64, "entre 3 y 63"),
    ("mi bucket", "espacios"), (" mi-bucket", "espacios"), ("mi-bucket ", "espacios"), ("mi-bucket\n", "espacios"),
    ("mi\tbucket", "espacios"), ("mi_bucket", "solo admite"), ("mi@bucket", "solo admite"), ("bücket-datos", "solo admite"),
    ("-abc", "empezar y terminar"), ("abc-", "empezar y terminar"), (".abc", "empezar y terminar"),
    ("abc.", "empezar y terminar"),
    ("a..b", "consecutivos"), ("mi..bucket", "consecutivos"),
    ("192.168.1.1", "IPv4"), ("10.0.0.1", "IPv4"), ("0.0.0.0", "IPv4"),
    ("xn--abc", "prefijo reservado"), ("sthree-datos", "prefijo reservado"),
    ("amzn-s3-demo-bucket", "prefijo reservado"), ("amzn-s3-demo-", "prefijo reservado"),
    ("mi-bucket-s3alias", "sufijo reservado"), ("mi-bucket--ol-s3", "sufijo reservado"),
    ("mi-bucket.mrap", "sufijo reservado"), ("mi-bucket--x-s3", "sufijo reservado"),
    ("mi-bucket--table-s3", "sufijo reservado"),
    ("<nombre-del-bucket>", "solo admite"), ("${var.s3_bucket}", "solo admite"),
]


@pytest.mark.parametrize("nombre", BUCKETS_VALIDOS)
def test_nombre_bucket_valido(nombre):
    assert comun.errores_nombre_bucket(nombre) == []
    comun.validar_nombre_bucket(nombre)
    p = comun.leer_parametros(dbutils_falso({**DEV, "s3_bucket": nombre}), comun.PARAMS_BASE)
    assert p["raw_root"] == f"s3://{nombre}/raw"


@pytest.mark.parametrize("nombre, motivo", BUCKETS_INVALIDOS)
def test_nombre_bucket_invalido(nombre, motivo):
    errores = comun.errores_nombre_bucket(nombre)
    assert any(motivo in e for e in errores), errores
    with pytest.raises(ValueError, match="nombre de bucket S3") as exc:
        comun.validar_nombre_bucket(nombre)
    reservados = comun.BUCKET_PREFIJOS_RESERVADOS + comun.BUCKET_SUFIJOS_RESERVADOS
    assert len(nombre) < 8 or nombre in reservados or nombre not in str(exc.value)   # el mensaje no reproduce el valor
    with pytest.raises(ValueError, match="nombre de bucket S3"):
        comun.leer_parametros(dbutils_falso({**DEV, "s3_bucket": nombre}), comun.PARAMS_BASE)


def test_bucket_vacio_o_ausente_falla_con_mensaje_claro():
    for valor in ("", "   "):
        with pytest.raises(ValueError, match="Falta el parámetro obligatorio 's3_bucket'"):
            comun.leer_parametros(dbutils_falso({**DEV, "s3_bucket": valor}), comun.PARAMS_BASE)
    sin_bucket = {k: v for k, v in DEV.items() if k != "s3_bucket"}
    with pytest.raises(ValueError, match="BUNDLE_VAR_s3_bucket"):
        comun.leer_parametros(dbutils_falso(sin_bucket), comun.PARAMS_BASE)


def test_bucket_con_espacios_no_se_normaliza_en_silencio():
    with pytest.raises(ValueError, match="espacios"):
        comun.leer_parametros(dbutils_falso({**DEV, "s3_bucket": " example-retail-bucket "}), comun.PARAMS_BASE)


def test_dev_y_prod_con_el_mismo_bucket_comparten_raw_y_separan_lakehouse():
    """Con un único s3_bucket, RAW es compartido y las tablas de cada entorno no se solapan."""
    d = comun.leer_parametros(dbutils_falso(DEV), comun.PARAMS_BASE)
    pr = comun.leer_parametros(dbutils_falso(PROD), comun.PARAMS_BASE)
    assert d["raw_root"] == pr["raw_root"] == "s3://example-retail-bucket/raw"
    assert d["lakehouse_root"] != pr["lakehouse_root"]
    assert not (d["lakehouse_root"] + "/").startswith(pr["lakehouse_root"] + "/")
    assert not (pr["lakehouse_root"] + "/").startswith(d["lakehouse_root"] + "/")


def test_el_ejemplo_de_prueba_es_un_bucket_valido_y_el_marcador_documental_no():
    assert comun.errores_nombre_bucket("example-retail-bucket") == []
    assert comun.errores_nombre_bucket("<nombre-del-bucket>") != []


def test_rutas_por_entorno():
    assert comun.ruta_tabla(DEV, "gold", "t") == "s3://example-retail-bucket/lakehouse/dev/gold/t"
    assert comun.ruta_tabla(PROD, "gold", "t") == "s3://example-retail-bucket/lakehouse/prod/gold/t"
    assert comun.nombre_tabla(DEV, "gold", "t") == "`cat`.`dev_gold`.`t`"


# --- grant_principal ---------------------------------------------------------------
@pytest.mark.parametrize("nombre, tipo", [
    ("retail_etl_readers", "grupo"),
    ("lector@example.com", "usuario"),
    ("0f6c2d1e-8a3b-4c5d-9e7f-1a2b3c4d5e6f", "service_principal"),
])
def test_principal_valido(nombre, tipo):
    assert comun.validar_principal(nombre) == tipo


@pytest.mark.parametrize("nombre", [
    "admins", "users", "Account Users",                    # sistema: acceso indiscriminado
    "users-clone-2026-08-21-1611-UTC",                     # grupo local generado por Databricks
    "retail_etl_readers (workspace)",                      # grupo local renombrado en una migración
    "", "grupo`; DROP",
])
def test_principal_rechazado(nombre):
    with pytest.raises(ValueError):
        comun.validar_principal(nombre)


def test_enmascarar_correo():
    assert comun.enmascarar("lector@example.com") == "l***@example.com"
    assert comun.enmascarar("retail_etl_readers") == "retail_etl_readers"


def test_aislamiento_rechaza_lakehouse_dentro_de_raw():
    # La External Location permite escribir en todo el bucket: el código impide escribir dentro de RAW.
    with pytest.raises(ValueError, match="se solapan"):
        comun.validar_aislamiento({**PROD, "raw_root": "s3://example-retail-bucket/lakehouse"})
