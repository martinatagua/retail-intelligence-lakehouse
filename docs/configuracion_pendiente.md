# Configuración: confirmada y pendiente

Ningún valor de esta página es inventado. Las variables del bundle se definen en [`databricks.yml`](../databricks.yml)
y se sobrescriben con `--var nombre=valor` o `BUNDLE_VAR_nombre`. La configuración del bucket (`s3_bucket`, obligatoria, sin default y
sin valor en Git) se explica en un solo sitio: [README, «Configuración»](../README.md#configuración).
Los secretos van **solo** en el environment `prod` de GitHub.
El estado de ejecución (qué se ha probado y dónde) está en el [README](../README.md#estado-del-proyecto) y en la
[checklist](checklist_cumplimiento.md).

## Valores confirmados

Confirmados por el autor sobre el entorno de ejecución, que es externo al repositorio y no se puede verificar desde él. La titularidad
del workspace y de los recursos cloud no se especifica en esta documentación y es independiente de la autoría del código (ver [Autoría y alcance](../README.md#autoría-y-alcance)).

| Elemento | Valor |
|---|---|
| Workspace | Databricks **Free Edition** en AWS: un único workspace, con cómputo **serverless** |
| Bucket S3 | Variable obligatoria `s3_bucket` ([README](../README.md#bucket-s3-s3_bucket)); su valor no se publica |
| External Location | Sobre la **raíz** del bucket, con Read, List, Write y **Delete** probados. El almacenamiento **no** está restringido a solo lectura en ninguna ruta, tampoco en `raw/` |
| Catálogo | `workspace` (default de la variable `catalog`) |
| `grant_principal` | `retail_etl_readers`, grupo con origen **Account** (usado en dev). La variable **no tiene default**: hay que pasarla siempre |

## Entornos (separación lógica en un solo workspace)

| | dev (`-t dev`, por defecto) | prod (`-t prod`) |
|---|---|---|
| Job | `[dev <usuario>] WF_DEV_ETL_RETAIL` | `WF_PROD_ETL_RETAIL` |
| Esquemas | `dev_bronze`, `dev_silver`, `dev_gold` (existen tras el run de dev) | `bronze`, `silver`, `gold` (creados a mano) |
| Tablas (Delta externas) | `s3://${s3_bucket}/lakehouse/dev/<capa>/<tabla>` | `s3://${s3_bucket}/lakehouse/prod/<capa>/<tabla>` |
| RAW (compartido; los notebooks solo lo leen) | `s3://${s3_bucket}/raw/` | igual |
| Despliegue | CLI local con un perfil de `~/.databrickscfg` | GitHub Actions (manual) |

**No son dos workspaces físicos.** Comparten el catálogo, la External Location y los permisos, y el aislamiento depende del código:
- `comun.validar_aislamiento()` hace fallar cualquier notebook que, con `entorno=dev`, reciba un esquema sin `dev_` o una ruta fuera
  de `lakehouse/dev`, y lo mismo a la inversa en prod.
- Tampoco admite que `lakehouse_root` y `raw_root` se solapen.
- `entorno` sale de `${bundle.target}` y no se puede sobrescribir con `--var`.

Una identidad con acceso a la External Location podría escribir o borrar en cualquier ruta del bucket desde fuera de estos
notebooks (ver [seguridad](../seguridad/README.md#acceso-al-almacenamiento-qué-está-restringido-y-qué-no)).

## Valores por defecto del bundle (decisiones de diseño, cambiables)

| Variable | Valor | Nota |
|---|---|---|
| `s3_bucket` | Sin default | Obligatoria; ver [README](../README.md#bucket-s3-s3_bucket). `comun.py` deriva `raw_root` y `lakehouse_root` para cada entorno |
| `raw_path_ecommerce` | `ecommerce/Ecommerce_Sales_Prediction_Dataset.csv` | Relativa a `raw_root` |
| `raw_path_automobiles` | `automobiles/Automobile_data.csv` | Relativa a `raw_root`. El archivo no está en el repositorio: hay que subirlo a RAW por separado ([datasets/README.md](../datasets/README.md#automobile-cómo-obtenerlo-y-configurarlo)) |
| `semantica_discount` | `desconocida` | Ver [esquemas_detectados.md](esquemas_detectados.md#evidencia-sobre-discount) |

## Pendiente para producción

| Elemento | Descripción | Dónde |
|---|---|---|
| Host del workspace | URL `https://<deployment>.cloud.databricks.com` | Secret `DATABRICKS_HOST` del environment `prod` |
| Autenticación de CI | Ver la sección siguiente | Secrets del environment `prod` |
| `grant_principal` en CI | `retail_etl_readers` | Variable `DATABRICKS_GRANT_PRINCIPAL` del environment `prod` |
| `s3_bucket` en CI | Solo el nombre del bucket ([README](../README.md#bucket-s3-s3_bucket)) | Variable `DATABRICKS_S3_BUCKET` del environment `prod`; requerida para validate/deploy/run. El workflow la enmascara y valida su formato |
| Privilegios de la identidad de CI | No hacen falta si esa identidad es la owner del catálogo y de la External Location | [PrepAmb/prerrequisitos_admin.sql](../PrepAmb/prerrequisitos_admin.sql) |
| Acceso al workspace de ejecución | El acceso usado hasta ahora fue temporal. Un despliegue futuro (prod o CI) requiere un acceso autorizado por el titular del workspace, o un workspace propio | — |

## Autenticación de GitHub Actions (no verificada todavía)

El CLI rechaza tener configurado más de un método a la vez ("more than one authorization method configured", comprobado en el
binario v1.19.0). Por eso `deploy-prod.yml` solo expone el PAT cuando no hay OAuth M2M.

| Opción | Secrets | Requisitos de administración | Estado en Free Edition |
|---|---|---|---|
| **A. OAuth M2M** (preferida) | `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` | Ser admin del workspace para crear el service principal y generarle un secreto OAuth. El SP necesita los privilegios de UC de PrepAmb y acceso al workspace | **Por verificar**: comprobar en Settings → Identity and access → Service principals si se puede crear un SP y generarle un secreto |
| **B. PAT** (alternativa) | `DATABRICKS_TOKEN` | Tener habilitados los tokens personales. El job se ejecuta como el usuario dueño del token | Por verificar: Settings → Developer → Access tokens |
| C. OIDC federation de GitHub | ninguno de larga duración | Política de federación a nivel de cuenta (account console) | Probablemente no disponible sin account console. Descartada por ahora |

Con la opción B, el job de prod se ejecuta como el usuario. Hay que rotar el PAT y darle la vigencia más corta posible.

## Requisitos de runtime

- Los notebooks importan `comun.py` y `transformaciones.py` desde su propia carpeta. Según el autor, funcionó en **serverless** en el run de dev (versión anterior a `s3_bucket`; ver [README](../README.md#ejecución-en-databricks-target-dev-comunicada-por-el-autor--histórica-anterior-a-la-parametrización-de-s3_bucket)).
- No se usan `.cache()`, `input_file_name()`, configuraciones de Spark ni clusters (compatible con Free Edition).

## Antes de volver a ejecutar el ETL Dev

Las 8 tablas externas de Dev se registraron en el workspace utilizado anteriormente, con una versión del bundle anterior a `s3_bucket`.
`comun.escribir_tabla_externa` **no sobrescribe** una tabla existente cuya ubicación sea distinta de la que calcula el código: falla con un error.

Antes de volver a ejecutar el ETL Dev contra ese workspace, el propietario debe:

1. Ejecutar `DESCRIBE DETAIL` sobre cada una de las 8 tablas (consultas E3 de [evidencias/consultas_evidencia.sql](../evidencias/consultas_evidencia.sql)).
2. Comprobar que la `location` de cada una es compatible con la configuración actual: el **mismo bucket** que se va a pasar en `s3_bucket`
   y la estructura de rutas `lakehouse/dev/<capa>/<tabla>` que deriva `comun.py`.
3. Si alguna no coincide, **no ejecutar** hasta decidir cómo tratarla. El código no renombra, mueve ni borra tablas ni datos.

Esta documentación no se conecta al workspace ni conoce esas ubicaciones: **no hay resultados registrados** de esa comprobación.
Las capturas de `DESCRIBE DETAIL` muestran la ruta S3: oculta el bucket antes de guardarlas (ver [evidencias/README.md](../evidencias/README.md#privacidad-repositorio-público)).
