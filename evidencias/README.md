# evidencias/

Carpeta de entrega **requerida**. Contiene las capturas de ejecuciones **reales**. Ahora mismo **no hay ninguna guardada**.
El autor comunicó haber hecho varias comprobaciones en Databricks (ver la columna «Comunicado por el autor»), pero no hay captura ni
log en el repositorio todavía, así que no son evidencia independiente. Las consultas para reproducirlas están en [`consultas_evidencia.sql`](consultas_evidencia.sql) y
[`../seguridad/verificar_permisos.sql`](../seguridad/verificar_permisos.sql), y todas son de solo lectura.

## Checklist de capturas

Marca la casilla solo cuando el archivo `.png` esté guardado en esta carpeta y revisado según las reglas de privacidad.

### Infraestructura

| ✓ | Archivo sugerido | Qué debe mostrar | Comunicado por el autor |
|---|---|---|---|
| [ ] | `S3_BUCKET_RAW.png` | Bucket `<nombre-del-bucket>` con `raw/ecommerce/` y `raw/automobiles/`, **con el nombre del bucket y los identificadores de cuenta ocultos** | Sí (lectura de RAW) |
| [ ] | `UC_EXTERNAL_LOCATION.png` | External Location sobre la raíz del bucket y su prueba de conexión | Sí |

### Target dev

| ✓ | Archivo sugerido | Qué debe mostrar | Comunicado por el autor |
|---|---|---|---|
| [ ] | `DEV_BUNDLE_VALIDATE.png` | Salida de `databricks bundle validate -t dev … --strict` con `Validation OK` | Sí |
| [ ] | `DEV_JOB_RUN_SUCCESS.png` | Run de `WF_DEV_ETL_RETAIL` con el DAG de 7 tareas en verde y `Succeeded` | Sí |
| [ ] | `DEV_CONTEOS_TABLAS.png` | Resultado de la consulta E1: conteo de las 8 tablas | Sí (conteos comprobados) |
| [ ] | `DEV_TIPO_TABLAS.png` | Resultado de E2: las 8 tablas con `table_type = EXTERNAL` | Sí (8 tablas Delta externas) |
| [ ] | `DEV_UBICACIONES_DELTA.png` | `DESCRIBE DETAIL` (E3): `format = delta` y `location` en `lakehouse/dev/<capa>/<tabla>`, con el bucket oculto | Ruta exacta sin documentar |
| [ ] | `S3_LAKEHOUSE_DEV.png` | Prefijos `lakehouse/dev/{bronze,silver,gold}/` en S3, con el nombre del bucket oculto | No |
| [ ] | `DEV_GRANTS_GOLD.png` | `SHOW GRANTS` de `retail_etl_readers`: `USE CATALOG`, `USE SCHEMA` sobre `dev_gold` y `SELECT` sobre las 4 tablas Gold | Sí (concesiones comprobadas) |
| [ ] | `UC_GRUPO_READERS.png` | Grupo `retail_etl_readers` con origen **Account**, sin la lista de miembros | Sí |

### Dashboard (ver [`../dashboard/README.md`](../dashboard/README.md))

| ✓ | Archivo sugerido | Qué debe mostrar | Comunicado por el autor |
|---|---|---|---|
| [ ] | `../dashboard/DASHBOARD_ECOMMERCE.png` y `../dashboard/DASHBOARD_AUTOMOBILES.png` | El dashboard real sobre Gold | **No: el dashboard no existe todavía** |

### Cuando ocurran (todavía no han ocurrido)

| ✓ | Archivo sugerido | Qué debe mostrar | Comunicado por el autor |
|---|---|---|---|
| [ ] | `GITHUB_ACTION_CI.png` | Ejecución verde de `CI (validación local)` | **No ejecutado** |
| [ ] | `GITHUB_ACTION_DEPLOY.png` | Ejecución verde de `Deploy PROD (manual)` con `deploy-and-run` | **No ejecutado** |
| [ ] | `PROD_JOB_RUN_SUCCESS.png` | Run de `WF_PROD_ETL_RETAIL` con las 7 tareas en verde | **No ejecutado** |
| [ ] | `PROD_CONTEOS_TABLAS.png`, `PROD_UBICACIONES_DELTA.png`, `PROD_GRANTS_GOLD.png` | Como los de dev, sobre `bronze/silver/gold` y `lakehouse/prod/` | **No ejecutado** |

## Privacidad (repositorio público)

Antes de guardar cualquier captura, **recórtala u oculta**:
- correos, nombres y avatares de usuarios, incluidos los del titular del workspace y los de los miembros del grupo;
- la URL o el ID del workspace, los ID de cuenta de AWS o Databricks, ARN completos, External IDs, ID de jobs y runs, y application IDs;
- tokens, client secrets y cualquier valor de los secrets de GitHub;
- las rutas de usuario (`/Workspace/Users/<correo>/…`) que aparecen en el bundle y en los jobs;
- **nombres de buckets S3** y cualquier URI `s3://…` o `s3a://…`, completa o parcial (por ejemplo en `DESCRIBE DETAIL`, `location`, la External Location, errores de Spark o la columna `_archivo_origen`);
- las **rutas internas** del almacenamiento que incluyan el bucket, y el nombre del IAM Role, de la Storage Credential y de la External Location si identifican la cuenta o la organización;
- otros identificadores de infraestructura: ID de metastore, de catálogo o de esquema internos, de cluster, de SQL warehouse y de dashboard.

Deja visible solo lo que prueba la evidencia: nombres de tablas, esquemas, estados, conteos y privilegios.

Los notebooks del proyecto ya muestran el bucket y las URI como `s3://<bucket>/…`, pero eso **no cubre** las salidas que genera Databricks
(`DESCRIBE DETAIL`, el explorador de S3 o de la External Location, mensajes de error nativos de Spark o de Unity Catalog) ni los datos de las
tablas: Bronze y Silver guardan en `_archivo_origen` la URI completa del CSV. Revisa cada captura antes de guardarla.
