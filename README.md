# Retail Intelligence Lakehouse

> **Proyecto individual de formación en ingeniería de datos.** El nombre técnico del bundle y de los recursos de Databricks
> es `databricks-aws-retail-etl`.

Pipeline ETL de extremo a extremo con **arquitectura Medallion (Bronze → Silver → Gold)** sobre
**Databricks + Unity Catalog en AWS**. RAW está en **Amazon S3** y se lee directamente con una External Location.
Las transformaciones usan la **API DataFrame de PySpark**, las tablas son Delta y el despliegue usa **Declarative Automation Bundles**.
La ejecución de producción está preparada para lanzarse a mano desde **GitHub Actions**, pero todavía no se ha ejecutado.

El flujo conceptual (Medallion sobre Databricks con CI/CD) toma como referencia académica el repositorio del curso
([Enrykiel/databricks_project](https://github.com/Enrykiel/databricks_project); ver [Autoría y alcance](#autoría-y-alcance)),
que usa Azure. Diferencias principales entre esa referencia y este proyecto, que usa AWS:

| Referencia (Azure) | Este proyecto (AWS) |
|---|---|
| ADLS Gen2, contenedor `raw` | Bucket `<nombre-del-bucket>`, prefijo `raw/` |
| Access Connector (Managed Identity) | IAM Role → Storage Credential → External Location (ya existentes). No es el mismo mecanismo; ver [D1](docs/decisiones_y_pendientes.md#d1-acceso-a-raw-managed-identity-enunciado-frente-a-iam-role-de-aws-implementación) |
| Notebooks exportados de un workspace origen | Notebooks versionados en Git y sincronizados por el bundle |
| Borrar y recrear el job con `curl` | `databricks bundle deploy`, que actualiza el job y conserva su historial |
| Despliegue en cada push a `main` | Despliegue solo manual (`workflow_dispatch`) en un environment protegido |
| Acciones de GitHub por tag mutable | Acciones fijadas a SHA de commit |
| Cluster buscado por nombre, catálogo `catalog_dev` fijo en prod | Serverless y parámetros por variable |

## Autoría y alcance

- **Autor y responsable del proyecto:** Martin Atagua. Proyecto académico **individual**, desarrollado con asistencia de herramientas de IA (ver más abajo).
- **Desarrollo técnico:** el autor definió el diseño y dirigió la implementación del pipeline (notebooks, transformaciones, bundle,
  workflows, validaciones de calidad y aislamiento, seguridad y permisos, reversión y pruebas), y asume la responsabilidad final del
  proyecto. La implementación se realizó **con asistencia de herramientas de IA** (ver [Uso de herramientas de IA](#uso-de-herramientas-de-ia)):
  no se afirma que el autor haya escrito manualmente cada fragmento de código ni se acredita la autoría de fragmentos concretos.
- **Referencia académica:** se utilizó como referencia académica el repositorio
  [Enrykiel/databricks_project](https://github.com/Enrykiel/databricks_project), que pertenece a su autor. La comparación realizada
  (2026-11-13, ramas `main` y `dev`) **no encontró reutilización material de código**: solo coincidencias con patrones habituales de
  Databricks y PySpark y con la estructura de carpetas del curso. Su README declara MIT y enlaza a un archivo `LICENSE` que **no se
  encontró en las ramas examinadas** (la API de GitHub devolvió `license: null`), por lo que no se verificó el texto íntegro de dicha
  licencia. La conclusión se limita a esa comparación: no es una certificación de originalidad frente a cualquier otra fuente. No es
  una dependencia, no es el repositorio de publicación y no se le atribuye autoría de este código (ver la [checklist](docs/checklist_cumplimiento.md)).
- **Infraestructura de ejecución:** las ejecuciones documentadas usaron recursos externos a este repositorio:
  - un **workspace de Databricks**, al que el autor tuvo acceso temporal;
  - **recursos de AWS**: el bucket S3 y el IAM Role;
  - **recursos de Unity Catalog**: el catálogo `workspace`, la Storage Credential, la External Location y el grupo `retail_etl_readers`.

  Esta documentación **no afirma la titularidad** de ninguno de estos recursos: es independiente de la autoría del código y queda
  pendiente de confirmación.
- **Datasets:** son de terceros; su procedencia, licencias y decisión de publicación están en **[DATASETS.md](DATASETS.md)** (detalle técnico en
  [datasets/README.md](datasets/README.md)). El autor no reclama derechos sobre ellos.
  **E-commerce** (Nevil Dhinoja, Kaggle, CC0 1.0 declarada por la fuente; archivo verificado byte a byte frente a la descarga oficial) **está incluido**.
  **Automobile** (UCI, Jeffrey Schlimmer, CC BY 4.0) **queda excluido de la publicación inicial**: su copia local está fuera de Git y no se ha confirmado su identidad con la distribución de UCI.
- **Licencia del código:** MIT, **exclusivamente para el código original de este proyecto**. No cubre ni modifica los datasets ni los materiales de terceros, que conservan sus propias condiciones ([DATASETS.md](DATASETS.md)). No hay una licencia única para todo el contenido del repositorio.
- **Alcance:** proyecto de formación. No es experiencia laboral comercial y no incluye mediciones de rendimiento, ahorro ni impacto de negocio.
- **Dos arquitecturas separadas:** (1) el **pipeline original con AWS S3** (`proceso/`, `databricks.yml`) y (2) el **laboratorio independiente en
  Databricks Free Edition con RAW en un Managed Volume** ([lakehouse_lab/README.md](lakehouse_lab/README.md)), ejecutado en un workspace personal
  distinto. No forman una única ejecución integrada y el laboratorio no demuestra integración S3 ni Managed Identity.

### Uso de herramientas de IA

Este proyecto fue desarrollado por su autor con asistencia de herramientas de IA: **Claude Code** en implementación y documentación,
**Codex** en revisiones y auditorías técnicas, y **ChatGPT** en planificación y orientación técnica. El autor definió los objetivos, tomó las
decisiones de diseño, supervisó las implementaciones y validaciones, revisó los resultados y asume la responsabilidad final del proyecto.
Las revisiones realizadas mediante herramientas de IA son asistidas y automatizadas y no sustituyen una auditoría humana independiente.
Esta declaración no sustituye las obligaciones académicas aplicables al proyecto ([D7](docs/decisiones_y_pendientes.md#d7-política-del-curso-sobre-asistencia-de-ia)).

## Estado del proyecto

Última revisión de esta documentación: 2026-11-13

Esta documentación distingue tres niveles:
- **Implementado:** verificable leyendo el código de este repositorio.
- **Comunicado por el autor:** salidas de terminal y comprobaciones en Databricks. No hay capturas ni logs originales guardados en el
  repositorio, así que **no son evidencia independiente**.
- **Pendiente:** no ejecutado o sin evidencia.

### Implementación completada

AWS S3 como RAW, Databricks sobre AWS, PySpark (API DataFrame), Delta Lake, Unity Catalog, arquitectura Bronze → Silver → Gold,
Databricks Asset Bundles, un workflow de siete tareas, validaciones de calidad y aislamiento, scripts de seguridad y permisos,
scripts de reversión y seis consultas SQL para un futuro dashboard.

### Ejecución en Databricks (target dev), comunicada por el autor — **histórica, anterior a la parametrización de `s3_bucket`**

El autor comunicó los resultados siguientes, obtenidos en el workspace externo descrito en [Autoría y alcance](#autoría-y-alcance).
Constan en esta documentación como **confirmados por el autor**; no hay capturas ni logs guardados en `evidencias/`.

> **No validan el bundle actual.** Se obtuvieron con una versión anterior, que fijaba las rutas S3 en variables propias (`raw_root`,
> `lakehouse_root`). El bundle actual deriva ambas rutas de `s3_bucket`, y con él **todavía no se ha ejecutado** `bundle validate`,
> `deploy` ni el run en Dev. Para tenerlo, primero comprueba las ubicaciones de las tablas existentes
> ([docs/configuracion_pendiente.md](docs/configuracion_pendiente.md#antes-de-volver-a-ejecutar-el-etl-dev)) y repite la validación.

- Free Edition con cómputo serverless.
- External Location sobre la raíz del bucket, con lectura, escritura y borrado probados.
- Lectura de los dos CSV de RAW desde S3: 1000 y 205 filas.
- Escritura Delta y registro en Unity Catalog.
- Catálogo `workspace`, y grupo `retail_etl_readers` con origen Account.
- **Target dev:**
  - `databricks bundle validate -t dev --var="grant_principal=retail_etl_readers" --strict` → `Validation OK`;
  - `databricks bundle deploy -t dev`;
  - run del job `WF_DEV_ETL_RETAIL` (recurso `wf_prod_etl_retail`) → `TERMINATED SUCCESS`, con **las 7 tareas** terminadas sin errores reportados;
  - **8 tablas Delta externas** en `workspace.dev_bronze`, `workspace.dev_silver` y `workspace.dev_gold`, con los **conteos de las 8 tablas comprobados**;
  - concesiones a `retail_etl_readers` comprobadas: `USE CATALOG`, `USE SCHEMA` sobre `dev_gold` y `SELECT` sobre las 4 tablas Gold.

### Validaciones locales (sin Databricks)

Salidas de terminal comunicadas por el autor. No hay un log persistente de estas ejecuciones en el repositorio:
- `scripts/validar_repo.py`: `CORRECTO: 0 error(es)`;
- compilación de Python sin errores.

**Cifras de pruebas retiradas.** Este README citaba antes resultados históricos de pruebas (`25 passed` sin Spark y `40 passed` con la suite
completa). Se retiraron porque no se conserva el comando, la versión del código evaluada ni un log que las respalde, y no se han reproducido.
No se publica ninguna cifra de pruebas aprobadas. La suite está en `tests/` y se lanza con `uv run pytest` (requiere Java para las pruebas con
PySpark); las pruebas de `tests/` cubren el pipeline S3 original y **no** el laboratorio de `lakehouse_lab/`.

Esos resultados son los comunicados antes de esta parametrización. El bundle actual requiere además `BUNDLE_VAR_s3_bucket`
(o `--var="s3_bucket=<nombre-del-bucket>"`); el workflow manual de producción requiere `DATABRICKS_S3_BUCKET` en el environment `prod`.

Otras comprobaciones locales documentadas:
- Pruebas PySpark sobre el CSV de E-commerce (1000 filas) y sobre datos **sintéticos** de Automobiles (`tests/datos_sinteticos.py`), con la conciliación Gold con Silver. Las pruebas sobre el CSV
  original de Automobiles (205 filas) son opcionales y locales: solo se ejecutan si el archivo está presente, y en un clon limpio se omiten.
- Ejecución de los 7 notebooks con un `dbutils` simulado y el catálogo local de Spark. Se hizo con un arnés temporal que **no está en
  el repositorio**, así que no se puede reproducir desde aquí; las pruebas reproducibles son las de `tests/`.
- Consultas del dashboard (`dashboard/sql/`), ejecutadas contra las tablas Gold generadas en local (`tests/test_dashboard_sql.py`).
- Sintaxis de los diagramas Mermaid (`docs/diagramas.md`), revisada con el parser oficial de Mermaid 11.4.1 en un entorno temporal.
- Bundle frente al JSON Schema oficial del CLI v1.19.0.
- Consistencia de bundle, job, notebooks, workflows, privacidad y enlaces con `scripts/validar_repo.py`.

### Pendiente (acción manual en Databricks)

- **Revalidar Dev con el bundle actual** (`s3_bucket`): comprobar las ubicaciones de las 8 tablas existentes con `DESCRIBE DETAIL` y repetir
  `validate`, `deploy` y run ([detalle](docs/configuracion_pendiente.md#antes-de-volver-a-ejecutar-el-etl-dev)).
- **Dashboard:** las consultas y las instrucciones están listas ([dashboard/README.md](dashboard/README.md)), pero el dashboard **no existe todavía**.
- **Evidencias:** no hay ninguna captura guardada. La checklist y las consultas están en [evidencias/README.md](evidencias/README.md).
- Ruta exacta de cada tabla en `lakehouse/dev/…` (`DESCRIBE DETAIL`), documentada como evidencia.
- Evidencia del acceso efectivo de un miembro de `retail_etl_readers` sobre Gold (opcional; no hay evidencia hasta ahora).

### No desplegado o no ejecutado

- **Producción** (`-t prod`, `WF_PROD_ETL_RETAIL`): no desplegada ni ejecutada.
- **GitHub Actions** (`CI (validación local)` y `Deploy PROD (manual)`): nunca ejecutado.
- **Scripts de reversión** (`reversion/`): no ejecutados.

Las cuestiones abiertas están en [docs/decisiones_y_pendientes.md](docs/decisiones_y_pendientes.md):
- Managed Identity frente al IAM Role;
- la aceptación de los datasets;
- Automobile, que queda **excluido de la publicación inicial**; incluirlo en el futuro exigiría confirmar la identidad de la copia y las condiciones descritas en [DATASETS.md](DATASETS.md).

## Fuentes de datos

| Fuente | Archivo | Filas × columnas | Particularidades |
|---|---|---|---|
| E-commerce | `Ecommerce_Sales_Prediction_Dataset.csv` | 1000 × 7 | Fecha `dd-MM-yyyy`; unidad de `Discount` sin verificar |
| Automobiles | `Automobile_data.csv` (**no incluido en el repositorio**) | 205 × 26 | Nulos marcados con `?`; sin clave natural |

Las dos fuentes **no comparten columnas** y no se combinan en ninguna capa. Ver [docs/esquemas_detectados.md](docs/esquemas_detectados.md)
para los esquemas y [DATASETS.md](DATASETS.md) (y [datasets/README.md](datasets/README.md)) para la procedencia, atribución y condiciones de licencia declaradas.

## Arquitectura

Diagramas editables (Mermaid) de la arquitectura, el job y el flujo Medallion: [docs/diagramas.md](docs/diagramas.md).

```
s3://<nombre-del-bucket>/
├── raw/                                   ← RAW (lectura directa, External Location de UC)
│   ├── ecommerce/Ecommerce_Sales_Prediction_Dataset.csv
│   └── automobiles/Automobile_data.csv
└── lakehouse/                             ← tablas Delta externas registradas en UC
    ├── prod/                              ← esquemas bronze | silver | gold
    │   ├── bronze/{ecommerce_ventas, automobiles_specs}
    │   ├── silver/{ecommerce_ventas, automobiles_specs}
    │   └── gold/{ecommerce_ventas_mensuales_categoria, ecommerce_ventas_segmento_categoria,
    │             automobiles_resumen_marca, automobiles_resumen_carroceria_combustible}
    └── dev/                               ← esquemas dev_bronze | dev_silver | dev_gold (misma estructura)
```

### Entornos: un solo workspace (Free Edition)

`dev` y `prod` son **una separación lógica dentro del mismo workspace y del mismo catálogo**, no dos workspaces físicos.
Cada target usa sus propios esquemas, rutas en `lakehouse/` y nombre de job. RAW es compartido y los notebooks solo lo leen.
El bucket (`s3_bucket`) no tiene valor predeterminado ni se guarda en el repositorio: ver [Configuración](#configuración).

Cada notebook valida el aislamiento con `comun.validar_aislamiento`:
- los notebooks de dev se niegan a escribir en esquemas o rutas de prod;
- ninguno escribe dentro de `raw/`.

Es una garantía **del código, no del almacenamiento**, porque la External Location cubre la raíz del bucket con lectura,
escritura y borrado. Ver [seguridad/README.md](seguridad/README.md#acceso-al-almacenamiento-qué-está-restringido-y-qué-no) y
[docs/configuracion_pendiente.md](docs/configuracion_pendiente.md#entornos-separación-lógica-en-un-solo-workspace).

### Job

`WF_DEV_ETL_RETAIL` / `WF_PROD_ETL_RETAIL`, definido en [resources/wf_prod_etl_retail.job.yml](resources/wf_prod_etl_retail.job.yml):

```
PrepAmb ─┬─ Extract_ecommerce ─── Transform_ecommerce ───┬─ Load ── Grants
         └─ Extract_automobiles ─ Transform_automobiles ─┘
```

| Capa | Notebook | Qué hace |
|---|---|---|
| PrepAmb | `proceso/00_prep_amb.py` | Verifica el catálogo (no lo crea), crea los esquemas del entorno si faltan y comprueba RAW en S3, la separación RAW/lakehouse y el aislamiento |
| Bronze | `proceso/01_extract_*.py` | CSV → Delta, todo `string`, con auditoría (`_archivo_origen`, `_fecha_ingesta`, `_ejecucion_id`) |
| Silver | `proceso/02_transform_*.py` | Tipos explícitos, `?` → nulo y validaciones **antes** de escribir |
| Gold | `proceso/03_load_gold.py` | Agregados por fuente, conciliados con Silver |
| Grants | `proceso/04_grants.py` | `USE CATALOG`, `USE SCHEMA` y `SELECT` sobre Gold, solo para `grant_principal`. Nunca `admins` ni `users` ([detalle](seguridad/README.md#principal-lector-grant_principal)) |

La lógica de negocio está en `proceso/transformaciones.py` (funciones puras de DataFrame) y las utilidades en `proceso/comun.py`.
Los parámetros llegan a los notebooks como **parámetros del job → widgets** (`dbutils.widgets.get`); las variables del bundle
no existen en Python. La ejecución normal **no** hace DROP ni borra rutas: las escrituras sobrescriben las tablas como una
nueva versión Delta y conservan el historial.

## Estructura del repositorio

```
.github/workflows/  ci.yml (validación local, sin secretos) · deploy-prod.yml (manual)
PrepAmb/            prerrequisitos_admin.sql: lo que hace un admin una sola vez (documental)
proceso/            notebooks de producción + comun.py + transformaciones.py
seguridad/          modelo de permisos + verificar_permisos.sql (solo consultas)
reversion/          01_revoke.py · 02_drop_tablas.py (manuales, con confirmación)
datasets/           CSV de E-commerce (versionado) + README técnico. El CSV de Automobile queda fuera de Git (.gitignore). Procedencia y licencias: DATASETS.md (raíz)
docs/               esquemas, checklist, configuración, decisiones y pendientes, diagramas (Mermaid)
resources/          definición del job
tests/              pruebas PySpark (CSV de E-commerce y datos sintéticos de Automobiles), aislamiento, principal, salidas y validador
scripts/            perfilar_csv.py · validar_repo.py
dashboard/          sql/ (6 consultas sobre Gold) + README para montar el dashboard (aún no creado)
evidencias/         checklist de capturas reales + consultas_evidencia.sql (ninguna captura todavía)
certificaciones/    índice de certificados (ninguno aportado todavía)
databricks.yml · pyproject.toml · uv.lock · .python-version · .gitattributes (CSV sin normalizar ni comprobación de espacios)
```

## Configuración

Esta sección es la **fuente principal** de la configuración del bucket; el resto de la documentación enlaza aquí. La lista completa de
variables está en [docs/configuracion_pendiente.md](docs/configuracion_pendiente.md).

### Bucket S3 (`s3_bucket`)

- Variable **obligatoria** del bundle, sin valor predeterminado y sin valor en el repositorio. Se pasa solo con `BUNDLE_VAR_s3_bucket`
  o con `--var="s3_bucket=<nombre-del-bucket>"`. Lleva **solo el nombre** del bucket: sin `s3://` y sin ruta.
- `comun.py` deriva de él `raw_root` (`s3://<nombre-del-bucket>/raw`) y `lakehouse_root` (`…/lakehouse/<entorno>`). Si falta o no es un nombre
  de bucket válido, cada notebook que lo necesita falla al empezar con un mensaje que no reproduce el valor. El formato sigue las reglas de nombres de
  buckets S3 de propósito general (3 a 63 caracteres, minúsculas, números, puntos y guiones, sin puntos consecutivos, sin formato IPv4 y sin los
  prefijos y sufijos reservados). **Solo se valida el formato:** no se comprueba que el bucket exista ni su unicidad global.
- **Dev (CLI local):** `export BUNDLE_VAR_s3_bucket="<nombre-del-bucket>"` antes de `databricks bundle validate|deploy|run -t dev`
  (o `--var`). La variable de entorno local no se incorpora a Git.
- **Prod (GitHub Actions):** variable `DATABRICKS_S3_BUCKET` del environment `prod`. El workflow la recibe como `BUNDLE_VAR_s3_bucket`, la
  enmascara en su primer paso, falla si falta o su formato no es válido y no la imprime. Es una variable de GitHub (`vars`) y no un secreto:
  es un identificador de configuración.
- **Mismo bucket en dev y prod.** RAW es compartido por diseño, así que ambos entornos deben configurarse con el bucket de ese diseño compartido.
  **Nada en el repositorio comprueba que los dos valores coincidan** (dev lo lee del entorno local y prod de GitHub): confírmalo tú.
- Los notebooks no imprimen el bucket ni URI `s3://` completas: se muestran como `s3://<bucket>/…`. El procesamiento sí usa los valores reales.
- Convención de marcadores: `<nombre-del-bucket>` en la documentación; `example-retail-bucket` solo en `tests/`.

### Otras variables y secretos

- `grant_principal` no tiene valor por defecto y hay que pasarlo siempre (en dev se usó `retail_etl_readers`).
- Para producción faltan los secrets del environment `prod` de GitHub (host y autenticación, OAuth M2M o PAT) y las variables
  `DATABRICKS_GRANT_PRINCIPAL` y `DATABRICKS_S3_BUCKET`.
- Los secretos nunca se versionan.

## Validación local

Requisitos:
- [uv](https://docs.astral.sh/uv/), que instala Python 3.12 y las dependencias exactas de `uv.lock`;
- **Java 17**, para las pruebas con Spark;
- el Databricks CLI, solo para el JSON Schema del bundle.

Nada de esto contacta con Databricks ni con AWS.

```bash
uv sync --locked                                          # entorno .venv a partir de uv.lock
uv run python scripts/validar_repo.py                     # YAML estricto, bundle, job, workflows, privacidad, enlaces (sin Spark)
databricks bundle schema > /tmp/bundle_schema.json        # offline, sin credenciales
uv run python scripts/validar_repo.py --schema /tmp/bundle_schema.json
uv run python -m py_compile proceso/*.py reversion/*.py scripts/*.py tests/*.py
PYFLAKES_BUILTINS=spark,dbutils,display uv run python -m pyflakes proceso reversion scripts tests
uv run pytest -q                                          # requiere Java 17 (JAVA_HOME o java en PATH)
uv run pytest -q tests/test_comun.py tests/test_validar_repo.py   # subconjunto sin Spark ni Java
```

`.github/workflows/ci.yml` ejecuta `uv sync --locked`, `py_compile`, `pyflakes`, `validar_repo.py --schema` y `pytest -q`,
igual que en este bloque. Además ejecuta `git diff --check "$(git hash-object -t tree /dev/null)" HEAD`, que necesita al menos
un commit. Sin commits, el equivalente local es `git diff --no-index --check /dev/null <archivo>` para cada archivo nuevo.
Los CSV tienen finales de línea CRLF; `.gitattributes` los excluye de esa comprobación y evita que se normalicen, de modo que
sus SHA-256 se conservan.

**Un clon limpio no necesita el CSV de Automobile** para instalar, validar ni ejecutar las pruebas públicas: las de Automobiles usan datos sintéticos.
Las pruebas `*_csv_real` y la variante `real` de `test_dashboard_sql.py` son opcionales y locales; sin el archivo se omiten y `pytest` indica el motivo
(`-rs`). No cuentan como ejecutadas.

## Despliegue

1. Revisa [PrepAmb/prerrequisitos_admin.sql](PrepAmb/prerrequisitos_admin.sql): las comprobaciones [ADMIN] y los privilegios, si hacen falta.
2. Los CSV deben estar en `s3://<nombre-del-bucket>/raw/{ecommerce,automobiles}/`. El de E-commerce viene en `datasets/`; **el de Automobile no está en el
   repositorio** y debe obtenerse y subirse por separado ([datasets/README.md](datasets/README.md#automobile-cómo-obtenerlo-y-configurarlo)): sin él, las tareas de Automobiles del
   job no pueden ejecutarse. Configura el bucket como se explica en [Configuración](#configuración).
3. **dev** se despliega desde el CLI local. Según el autor se ejecutó una vez con éxito, con una versión anterior a `s3_bucket` y sin captura
   guardada; antes de repetirlo contra el workspace anterior, lee
   [Antes de volver a ejecutar el ETL Dev](docs/configuracion_pendiente.md#antes-de-volver-a-ejecutar-el-etl-dev):
   ```bash
   databricks bundle validate -t dev --profile <perfil> --var="grant_principal=retail_etl_readers" --strict
   databricks bundle deploy   -t dev --profile <perfil> --var="grant_principal=retail_etl_readers"
   databricks bundle run      -t dev --profile <perfil> --var="grant_principal=retail_etl_readers" wf_prod_etl_retail
   ```
4. **prod** (no ejecutado): configura el environment `prod` en GitHub. Después, Actions → **Deploy PROD (manual)** → `validate` y,
   por último, `deploy-and-run`.

## Cumplimiento, pendientes y decisiones

- [docs/checklist_cumplimiento.md](docs/checklist_cumplimiento.md): requisitos y su estado (local, workspace o pendiente).
- [docs/decisiones_y_pendientes.md](docs/decisiones_y_pendientes.md): diferencias con el enunciado que necesitan confirmación humana.
- [seguridad/README.md](seguridad/README.md): modelo de permisos, aislamiento, autoría e infraestructura, datos personales y secretos.


## Laboratorio Free Edition (Medallion sobre Managed Volume)

Implementación alternativa y separada de la arquitectura S3, ejecutada en Databricks Free Edition: ver [lakehouse_lab/README.md](lakehouse_lab/README.md). No demuestra integración S3 ni Managed Identity.
