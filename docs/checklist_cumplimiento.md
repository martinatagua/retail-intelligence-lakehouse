# Checklist de cumplimiento

> **El PDF del profesor manda.** Requisitos que se sabe que exige: Medallion, PySpark, al menos 2 fuentes, CI/CD, notebooks de
> producción en `proceso/` y la estructura de carpetas `datasets/`, `dashboard/`, `reversion/`, `.github/workflows/`,
> `seguridad/`, `PrepAmb/`, `proceso/`, `certificaciones/` y `evidencias/`. **Contrasta esta lista con el PDF antes de entregar.**
> Las diferencias conocidas con el enunciado están en [decisiones_y_pendientes.md](decisiones_y_pendientes.md).

Leyenda:
- `[x]` hecho. **(L)**: implementación verificada en el repositorio o con comprobaciones locales. **(W)**: ejecución en Databricks
  **comunicada por el autor**, sin captura ni log guardados en el repositorio (no es evidencia independiente).
- `[~]` hecho, pero con la comprobación o la evidencia incompleta (se indica qué falta).
- `[ ]` pendiente o no ejecutado.

El **cumplimiento académico** (secciones 6 y 7) está pendiente de contrastarse con el PDF original del enunciado.

## 1. Infraestructura (comunicada por el autor; recursos externos al repositorio; titularidad no documentada)
- [x] (W) Free Edition con cómputo serverless
- [x] (W) Bucket S3 configurado externamente y External Location sobre su raíz, con Read/List/Write/Delete correctos.
  **No** es de solo lectura: el código limita las escrituras a `lakehouse/` (ver [seguridad](../seguridad/README.md#acceso-al-almacenamiento-qué-está-restringido-y-qué-no))
- [x] (W) Lectura de los dos CSV de RAW desde el workspace: 1000 filas (E-commerce) y 205 (Automobiles)
- [x] (W) Escritura Delta y registro en Unity Catalog
- [x] (W) Catálogo `workspace` con los esquemas `bronze`, `silver` y `gold` creados
- [x] (W) Grupo `retail_etl_readers` con origen **Account**, elegido como `grant_principal`

## 2. Ejecución en Databricks
### Target dev (ejecución comunicada por el autor; sin evidencia almacenada)
> **Histórico, anterior a la parametrización de `s3_bucket`.** Los resultados de este apartado se conservan tal como los comunicó el autor,
> pero se obtuvieron con una versión que fijaba `raw_root` y `lakehouse_root` como variables del bundle. **No validan el bundle actual**,
> que deriva ambas rutas de `s3_bucket` y requiere `BUNDLE_VAR_s3_bucket` o `--var="s3_bucket=<nombre-del-bucket>"` ([README](../README.md#configuración)).

- [ ] (W) **Revalidar con el bundle actual:** comprobar con `DESCRIBE DETAIL` las ubicaciones de las 8 tablas existentes
  ([procedimiento](configuracion_pendiente.md#antes-de-volver-a-ejecutar-el-etl-dev)) y repetir `validate`, `deploy` y run de Dev. **Pendiente**
- [x] (W) *(histórico)* `databricks bundle validate -t dev --var="grant_principal=retail_etl_readers" --strict` → `Validation OK`
- [x] (W) *(histórico)* `databricks bundle deploy -t dev`
- [x] (W) *(histórico)* Run de `WF_DEV_ETL_RETAIL` (recurso `wf_prod_etl_retail`) → `TERMINATED SUCCESS`, con las 7 tareas terminadas sin errores reportados
- [x] (W) 8 tablas **Delta externas** en `workspace.dev_bronze`, `workspace.dev_silver` y `workspace.dev_gold`
- [x] (W) *(histórico)* RAW en la ruta de esa versión (`raw_root` + `raw_path_*`; hoy se deriva de `s3_bucket` + `raw_path_*`): confirmado de forma indirecta, porque `00_prep_amb` y las dos tareas Extract terminaron bien
- [x] (W) *(histórico)* Conteos de las 8 tablas comprobados. Valores esperados según las pruebas locales: 1000, 205, 1000, 205, 165, 15, 22 y 9.
  Falta guardar la captura (`evidencias/DEV_CONTEOS_TABLAS.png`)
- [ ] (W) Ruta exacta de cada tabla en `lakehouse/dev/<capa>/<tabla>` (`DESCRIBE DETAIL`), documentada como evidencia
- [x] (W) Concesiones a `retail_etl_readers` comprobadas: `USE CATALOG`, `USE SCHEMA` sobre `dev_gold` y `SELECT` sobre las 4 tablas Gold
- [ ] (W) Opcional: una consulta real de un miembro de `retail_etl_readers` sobre Gold

### Target prod
- [ ] (W) `bundle validate -t prod`, `deploy` y run de `WF_PROD_ETL_RETAIL`. **No se ha desplegado ni ejecutado**
- [ ] (W) Validación de permisos sobre `workspace.gold`

## 3. Arquitectura, datos y job
- [x] (L) Dos fuentes independientes, sin fusionarlas en ninguna capa
- [x] (L) RAW se lee con `spark.read` sobre una URI `s3://`, sin DBFS ni Volúmenes (`validar_repo.py`)
- [x] (L) Transformaciones de negocio con la API DataFrame de PySpark (`proceso/transformaciones.py`)
- [x] (L) Validaciones de conteos, tipos, nulos y conciliación Gold, en los notebooks y en `tests/`
- [x] (L) Escrituras solo a `lakehouse/` vía `comun.ruta_tabla`. En `proceso/` no hay borrado de archivos, DROP ni DELETE (`validar_repo.py`)
- [x] (L) Aislamiento dev/prod forzado en el código (`comun.validar_aislamiento`, con pruebas)
- [x] (L) Notebooks de producción solo en `proceso/`, en formato fuente Databricks
- [x] (L) Job: PrepAmb → Extract ×2 en paralelo → Transform ×2 → Load → Grants, sin schedule y serverless
- [x] (L) Los parámetros del job coinciden con los widgets de cada notebook (`validar_repo.py`)
- [x] (L) Bundle conforme al JSON Schema oficial del CLI v1.19.0 (offline)
- [x] (L) `s3_bucket`: declaración única sin default; nombre validado con las reglas de buckets S3 de propósito general (`comun.validar_nombre_bucket`, con pruebas); sin URI `s3://` literales en archivos publicables (`validar_repo.py`)
- [x] (L) Las salidas de los notebooks no muestran el bucket ni URI `s3://` completas (`comun.ocultar`; pruebas en `tests/test_salidas.py` y comprobación estática en `validar_repo.py`)
- [x] (L) Validaciones locales comunicadas por el autor, **anteriores a la parametrización de `s3_bucket`** (salidas de terminal, sin log persistente en el repositorio):
  `validar_repo.py` → `CORRECTO: 0 error(es)`; compilación sin errores; pruebas sin Spark `25 passed`;
  suite completa con Java 17 en WSL2 `40 passed in 27.11s`

## 4. Seguridad y reversión
- [x] (L) `PrepAmb/prerrequisitos_admin.sql` distingue las operaciones [ADMIN] de las del [JOB] y no es destructivo
- [x] (L) Permisos de ejecución (PrepAmb, manual) separados de los GRANT de consumo: `04_grants` solo concede
  `USE CATALOG`, `USE SCHEMA` y `SELECT` a `grant_principal`, y rechaza `admins`, `users` y grupos locales (`validar_repo.py`)
- [x] (L) `seguridad/` y `reversion/` quedan fuera del job
- [ ] (W) `reversion/01_revoke.py` y `reversion/02_drop_tablas.py` (con confirmación explícita, sin DROP de catálogo ni borrado de S3): no ejecutados
- [x] (L) Sin credenciales ni correos en los archivos publicables; principal e identidad enmascarados en los logs de Actions (`validar_repo.py`)

## 5. CI/CD
- [x] (L) `ci.yml` separado del despliegue: sin secretos, con acciones fijadas a SHA y los mismos comandos `uv` que en local.
  Su `git diff --check` se reprodujo en una copia temporal con commit: pasa gracias a `.gitattributes` (sin él, los CRLF de los CSV lo harían fallar)
- [x] (L) `deploy-prod.yml`: solo manual; validate → deploy → run en ese orden, y un fallo corta el resto
- [x] (L) `deploy-prod.yml`: el primer paso enmascara el bucket y el principal y falla si faltan; el formato del bucket se valida antes de cualquier
  `databricks bundle`; ningún paso imprime esos valores (reglas estáticas en `validar_repo.py`). No se ha ejecutado en GitHub: el comportamiento real de los logs está sin comprobar
- [ ] GitHub Actions **nunca se ha ejecutado**: falta un run verde de `CI (validación local)`
- [ ] (W) Elegir y configurar la autenticación de CI, OAuth M2M o PAT ([configuración](configuracion_pendiente.md#autenticación-de-github-actions-no-verificada-todavía))
- [ ] (W) Run verde de `Deploy PROD (manual)` con `deploy-and-run`

## 6. Entregables (estructura del PDF)
- [~] `datasets/`: el CSV de E-commerce está versionado; el de Automobile **se excluye del repositorio** por decisión de distribución (queda en el equipo local, ignorado por Git). Qué exige el enunciado sobre los datasets de entrega está sin confirmar ([D2](decisiones_y_pendientes.md#d2-datasets-e-commerce-y-automobiles-frente-a-los-del-ejemplo), [D8](decisiones_y_pendientes.md#d8-distribución-de-los-datasets))
- [x] Procedencia y condiciones de licencia declaradas documentadas en [datasets/README.md](../datasets/README.md); no hay capturas archivadas y la revisión de redistribución de Automobiles sigue pendiente.
- [x] (L) Entorno local reproducible con `uv` (`pyproject.toml` + `uv.lock`)
- [x] (L) Las pruebas públicas no necesitan el CSV de Automobile: usan datos sintéticos (`tests/datos_sinteticos.py`); las pruebas sobre el CSV original son opcionales y locales, y se omiten con un motivo explícito si falta
- [x] (L) README con la arquitectura, los entornos, el estado y la ejecución
- [~] `dashboard/`: 6 consultas sobre Gold, probadas en local (`tests/test_dashboard_sql.py`), e instrucciones de montaje
  ([dashboard/README.md](../dashboard/README.md)). **El dashboard no está creado** y no hay capturas
- [~] `evidencias/`: checklist de capturas y consultas de solo lectura preparadas ([evidencias/README.md](../evidencias/README.md)).
  **Ninguna captura guardada**
- [~] `certificaciones/`: índice preparado ([certificaciones/README.md](../certificaciones/README.md)). **Ningún certificado aportado**;
  hay que confirmar con el PDF cuáles se exigen
- [x] (L) Diagramas de arquitectura, job y Medallion en Mermaid editable ([diagramas.md](diagramas.md)). `validar_repo.py` comprueba
  su coherencia con el job y las tablas; la sintaxis se revisó con el parser de Mermaid 11.4.1 en un entorno temporal
- [ ] Repositorio **público** en GitHub: pendiente de publicar
- [~] Implementación del autor con el repositorio `Enrykiel/databricks_project` como referencia académica y conceptual (atribuido en el README).
  No se ha hecho una comparación de código ni de originalidad con ese repositorio; no se incorpora código externo según el autor

## 7. Por confirmar con el profesor o evaluador
- [ ] Si el IAM Role de AWS cubre el requisito «Managed Identity» del enunciado ([D1](decisiones_y_pendientes.md#d1-acceso-a-raw-managed-identity-enunciado-frente-a-iam-role-de-aws-implementación))
- [ ] Si los datasets E-commerce y Automobiles se aceptan frente al enunciado ([D2](decisiones_y_pendientes.md#d2-datasets-e-commerce-y-automobiles-frente-a-los-del-ejemplo))
- [ ] Política del curso sobre el uso de herramientas de IA en el desarrollo y su declaración ([D7](decisiones_y_pendientes.md#d7-política-del-curso-sobre-asistencia-de-ia)). **No resuelta**
- [ ] Redistribución de Automobile: **excluido** del repositorio por decisión del propietario; su revisión de condiciones sigue pendiente ([datasets/README.md](../datasets/README.md), [D3](decisiones_y_pendientes.md#d3-licencias-de-los-csv), [D8](decisiones_y_pendientes.md#d8-distribución-de-los-datasets)).
