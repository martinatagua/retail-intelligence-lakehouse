"""Pruebas del validador estático scripts/validar_repo.py."""

import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import validar_repo  # noqa: E402


def test_detecta_clave_duplicada(tmp_path):
    f = tmp_path / "x.yml"
    f.write_text("variables:\n  raw_root: a\n  raw_root: b\n")
    with pytest.raises(yaml.YAMLError, match="duplicada 'raw_root'"):
        validar_repo.cargar_yaml(f)


def test_repositorio_consistente(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["validar_repo.py"])
    validar_repo.errores.clear()
    assert validar_repo.main() == 0


def test_validador_no_requiere_pyspark():
    """validar_repo.py debe funcionar en un entorno sin PySpark (comun.py lo importa de forma diferida)."""
    import subprocess
    codigo = (
        "import sys; sys.modules['pyspark'] = None; "          # cualquier 'import pyspark' falla
        "sys.argv = ['validar_repo.py']; sys.path.insert(0, 'scripts'); "
        "import validar_repo; sys.exit(validar_repo.main())"
    )
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert "CORRECTO: 0 error(es)" in r.stdout


# --- s3_bucket en el bundle ---------------------------------------------------------------------
def _bundle():
    return validar_repo.cargar_yaml(RAIZ / "databricks.yml")


def _job():
    return validar_repo.cargar_yaml(RAIZ / "resources" / "wf_prod_etl_retail.job.yml")["resources"]["jobs"]["wf_prod_etl_retail"]


def test_bundle_real_declara_s3_bucket_sin_default_ni_override():
    assert validar_repo.errores_s3_bucket_bundle(_bundle(), _job()) == []


def test_s3_bucket_con_default_ausente_o_fijado_en_un_target_se_detecta():
    import copy
    b = _bundle()
    con_default = copy.deepcopy(b)
    con_default["variables"]["s3_bucket"]["default"] = "x"
    assert any("sin default" in e for e in validar_repo.errores_s3_bucket_bundle(con_default))
    sin_declarar = copy.deepcopy(b)
    del sin_declarar["variables"]["s3_bucket"]
    assert any("declarado" in e for e in validar_repo.errores_s3_bucket_bundle(sin_declarar))
    en_target = copy.deepcopy(b)
    en_target["targets"]["dev"]["variables"]["s3_bucket"] = "x"
    assert any("target dev" in e for e in validar_repo.errores_s3_bucket_bundle(en_target))
    job = copy.deepcopy(_job())
    next(x for x in job["parameters"] if x["name"] == "s3_bucket")["default"] = "otro"
    assert any("parámetro s3_bucket" in e for e in validar_repo.errores_s3_bucket_bundle(b, job))


# --- URI S3 literales ------------------------------------------------------------------------
S3 = "s3://"     # se construyen las muestras por partes para que este archivo no contenga URI literales


@pytest.mark.parametrize("texto", [
    f"ruta {S3}<nombre-del-bucket>/raw/", f"LIST '{S3}<nombre-del-bucket>/raw/';", f"{S3}…/lakehouse/dev/",
    f"{S3}${{s3_bucket}}/raw/", f"f'{S3}{{bucket}}/raw'", "spark.read s3:// sin autoridad", f"{S3}...",
])
def test_s3_marcadores_documentales_permitidos(texto):
    assert validar_repo.s3_literales_no_permitidos(texto, "README.md") == []


@pytest.mark.parametrize("texto", [
    f"{S3}retail-datos-reales/raw/", f"x = '{S3}mi-bucket'", "s3a:" + "//mi-bucket/x", f"{S3}example-bucket/raw",
])
def test_s3_literal_real_se_detecta(texto):
    assert validar_repo.s3_literales_no_permitidos(texto, "docs/x.md") == [1]


def test_ejemplo_de_prueba_solo_se_admite_en_tests():
    muestra = f"{S3}example-retail-bucket/raw"
    assert validar_repo.s3_literales_no_permitidos(muestra, "tests/test_x.py") == []
    assert validar_repo.s3_literales_no_permitidos(muestra, "proceso/x.py") == [1]
    assert validar_repo.s3_literales_no_permitidos(f"{S3}otro-bucket/raw", "tests/test_x.py") == [1]


# --- Salidas sin rutas ni bucket -------------------------------------------------------------
def test_salidas_con_rutas_detecta_impresiones_y_excepciones_inseguras():
    mala = (
        "origen = comun.ruta_raw(p, 'x')\n"
        "print(f'{origen}')\n"
        "print(p['lakehouse_root'])\n"
        "print(comun.ruta_tabla(p, 'gold', 't'))\n"
        "comun.exigir(True, f'ruta {ruta}')\n"
        "raise RuntimeError(f'en {ubicacion}')\n"
        "print(f\"{p['s3_bucket']}\")\n"
    )
    assert [n for n, _ in validar_repo.salidas_con_rutas(mala)] == [2, 3, 4, 5, 6, 7]


def test_salidas_con_rutas_acepta_las_salidas_ocultas_y_las_normales():
    buena = (
        "origen = comun.ruta_raw(p, 'x')\n"
        "print(f'{comun.ocultar(origen)}')\n"
        "for k, v in comun.parametros_visibles(p).items():\n"
        "    print(k, v)\n"
        "print(f\"{p['catalogo']}\")\n"
        "comun.exigir(True, f\"RAW {comun.ocultar(ruta)}\")\n"
        "raise RuntimeError(f\"{comun.ocultar(ubicacion)}\")\n"
        "df = spark.read.load(origen)\n"          # uso en memoria: no es una salida
    )
    assert validar_repo.salidas_con_rutas(buena) == []


# --- deploy-prod.yml -------------------------------------------------------------------------
def _deploy():
    import copy
    return copy.deepcopy(validar_repo.cargar_yaml(RAIZ / ".github" / "workflows" / "deploy-prod.yml"))


def test_deploy_real_cumple_las_reglas():
    assert validar_repo.errores_deploy(_deploy()) == []


def test_deploy_mantiene_vars_y_no_pasa_a_secrets():
    env = _deploy()["jobs"]["bundle"]["env"]
    assert env["BUNDLE_VAR_s3_bucket"] == "${{ vars.DATABRICKS_S3_BUCKET }}"
    assert env["BUNDLE_VAR_grant_principal"] == "${{ vars.DATABRICKS_GRANT_PRINCIPAL }}"


def _con_paso(doc, indice, extra):
    doc["jobs"]["bundle"]["steps"][indice]["run"] += "\n" + extra
    return doc


@pytest.mark.parametrize("extra", [
    'echo "bucket: $BUNDLE_VAR_s3_bucket"', 'printf "%s" "${BUNDLE_VAR_grant_principal}"',
    'echo "${!v}"', "printenv", "env | sort", "set -x", "bash -x script.sh", "databricks bundle validate --debug",
    "declare -p", 'echo "${{ vars.DATABRICKS_S3_BUCKET }}"', 'echo "${{ secrets.DATABRICKS_HOST }}"',
    'python3 -c "import os; print(os.environ)"', 'python3 -c "print(BUNDLE_VAR_s3_bucket)"',
])
def test_deploy_detecta_impresiones_de_la_configuracion(extra):
    errs = validar_repo.errores_deploy(_con_paso(_deploy(), 4, extra))
    assert errs, extra


def test_deploy_exige_mascara_y_comprobacion_en_el_primer_paso():
    doc = _deploy()
    doc["jobs"]["bundle"]["steps"][0]["run"] = doc["jobs"]["bundle"]["steps"][0]["run"].replace(
        'echo "::add-mask::$BUNDLE_VAR_s3_bucket"', "true")
    assert any("enmascarar BUNDLE_VAR_s3_bucket" in e for e in validar_repo.errores_deploy(doc))
    doc = _deploy()
    doc["jobs"]["bundle"]["steps"][0]["run"] = doc["jobs"]["bundle"]["steps"][0]["run"].replace(
        '[ -z "$BUNDLE_VAR_s3_bucket" ]', "false")
    assert any("fallar si falta BUNDLE_VAR_s3_bucket" in e for e in validar_repo.errores_deploy(doc))
    doc = _deploy()
    doc["jobs"]["bundle"]["steps"].insert(0, {"uses": "actions/checkout@" + "0" * 40})
    assert validar_repo.errores_deploy(doc)       # un 'uses' antes del paso de enmascarado


def test_deploy_exige_validar_el_formato_antes_de_cualquier_bundle():
    doc = _deploy()
    pasos = doc["jobs"]["bundle"]["steps"]
    pasos[:] = [p for p in pasos if "validar_nombre_bucket" not in str(p.get("run", ""))]
    assert any("formato del bucket" in e for e in validar_repo.errores_deploy(doc))
    doc = _deploy()
    pasos = doc["jobs"]["bundle"]["steps"]
    i = next(i for i, p in enumerate(pasos) if "validar_nombre_bucket" in str(p.get("run", "")))
    pasos.append(pasos.pop(i))                    # al final: después de validate y deploy
    assert any("antes de cualquier" in e for e in validar_repo.errores_deploy(doc))


def test_deploy_rechaza_que_el_bucket_venga_de_otra_fuente():
    doc = _deploy()
    doc["jobs"]["bundle"]["env"]["BUNDLE_VAR_s3_bucket"] = "${{ secrets.DATABRICKS_S3_BUCKET }}"
    assert any("BUNDLE_VAR_s3_bucket debe recibirse" in e for e in validar_repo.errores_deploy(doc))


# --- Datasets: Automobile excluido, E-commerce incluido -----------------------------------------
def _ignorado(ruta):
    import subprocess
    return subprocess.run(["git", "check-ignore", "-q", "--", ruta], cwd=RAIZ).returncode == 0


def test_automobile_esta_ignorado_y_ecommerce_no():
    assert _ignorado("datasets/automobiles/Automobile_data.csv")
    assert _ignorado("otra/ruta/Automobile_data.csv")                # copias movidas con el mismo nombre
    assert not _ignorado("datasets/ecommerce/Ecommerce_Sales_Prediction_Dataset.csv")
    assert not _ignorado("datasets/automobiles/README.md")           # solo se ignora el CSV, no la carpeta
