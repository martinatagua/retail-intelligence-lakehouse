# Laboratorio Medallion en Databricks Free Edition (RAW en Managed Volume)

> **Arquitectura de laboratorio, distinta de la original con S3.** Aquí RAW es un **Managed Volume** de Unity Catalog
> (`/Volumes/workspace/retail_raw/ecommerce_files/`). **No** se usa S3, Storage Credential, External Location ni IAM Role, así
> que esta ejecución **no demuestra integración S3 ni cumplimiento del requisito de Managed Identity** (ver
> [D1](../docs/decisiones_y_pendientes.md)). El bundle original (`databricks.yml`, `proceso/`) no se ha modificado ni usado: depende de
> `s3_bucket`, External Locations y grants, y no es compatible con este workspace sin adaptación.

Workspace: Databricks Free Edition (perfil local `RETAIL_FREE`), catálogo `workspace`, cómputo serverless.

## Resumen

Pipeline Medallion de extremo a extremo sobre un dataset de e-commerce (1000 filas): CSV en un Managed Volume → tabla Bronze
(Delta) → Silver tipada con controles de calidad y trazabilidad → cuatro tablas Gold analíticas. Se ejecutó en Databricks y se
verificó con consultas SQL de solo lectura. Auditoría independiente: **PASS WITH OBSERVATIONS**.
Documento de cierre con diagrama, esquemas, reconciliación, consultas reproducibles y limitaciones: **[CIERRE_V1.md](CIERRE_V1.md)**.

## Capacidades demostradas

- Ingesta de un CSV desde un Managed Volume de Unity Catalog a Delta, sin inferir tipos y con metadatos de origen.
- Tipado defensivo (`try_cast`/`try_to_date`) y banderas de calidad sin descartar filas.
- Trazabilidad Bronze → Silver por clave de fila y reconciliación Silver → Gold. Cardinalidades: Bronze 1,000 filas físicas; Silver 1,000 filas
  físicas; Gold 4 tablas con 5, 3, 33 y 1 filas físicas (`sales_by_category`, `sales_by_segment`, `sales_by_month`, `sales_kpi_overview`).
  La suma de `records` en cada agregación Gold representa 1,000 registros de origen: no son 1,000 filas físicas por tabla Gold.
- Agregaciones Gold con fórmulas documentadas, sin asumir la semántica de `Discount`.
- Creación de tablas segura: comprueba existencia y nunca sobrescribe ni elimina.
- Ejecución serverless con notebooks en `lakehouse_lab/notebooks/` y validación por SQL.

## Flujo y tablas

```
RAW  Volume: Ecommerce_Sales_Prediction_Dataset.csv (1000 filas, 7 columnas; SHA-256 idéntico al CSV local)
 └─► BRONZE workspace.retail_bronze.ecommerce_sales        (Delta, 1000 filas; 7 columnas string + 4 de metadatos)
      └─► SILVER workspace.retail_silver.ecommerce_sales   (Delta, 1000 filas; tipado + banderas dq_*)
           └─► GOLD workspace.retail_gold.sales_by_category | sales_by_segment | sales_by_month | sales_kpi_overview
```

| Notebook (`lakehouse_lab/notebooks/`) | Función |
|---|---|
| `00_setup_schemas` | `CREATE SCHEMA IF NOT EXISTS` de bronze/silver/gold |
| `01_bronze_ecommerce_sales` | CSV → Delta sin inferir tipos; metadatos `_source_file`, `_source_file_modified_at`, `_ingested_at`, `_bronze_row_id` |
| `02_silver_ecommerce_sales` | Tipado, banderas de calidad, trazabilidad |
| `03_gold_ecommerce` | Agregaciones + reconciliación contra Silver |
| `04_validacion` | Validación de solo lectura (esquemas, conteos, DQ, trazabilidad) |

Reglas de creación: se comprueba antes si la tabla existe y, si existe, el notebook **falla sin reemplazarla**; `saveAsTable()` sin
modo; nunca `overwrite`/`DROP`. Verificado: relanzar Bronze falló y dejó la tabla intacta. Las tablas existentes quedan protegidas
contra sobrescritura; recrear una capa exigiría una decisión manual, pero **todavía no existe un procedimiento integral documentado,
probado y reproducible de reprocesamiento**.

## Ejecución

```bash
W=/Workspace/Users/<tu_usuario>/retail_lakehouse_lab
databricks workspace import-dir lakehouse_lab/notebooks $W --overwrite -p RETAIL_FREE
# run serverless con 5 tareas encadenadas (00→04) mediante `databricks jobs submit --json ...`
```

> **Advertencia sobre `import-dir --overwrite`.** Es una operación de **escritura sobre el workspace** y **puede reemplazar notebooks existentes** en
> el destino. Úsala solo cuando quieras actualizar deliberadamente esos recursos; **no forma parte de una validación de solo lectura**.
> No debe confundirse con la recreación o sobrescritura de tablas Delta: importar notebooks no toca las tablas, y los notebooks no sobrescriben
> tablas existentes (se detienen si ya existen).

## Transformaciones y reglas de calidad (Silver)

Perfilado previo (1000 filas, sin nulos, sin duplicados): `Date` en `dd-MM-yyyy` (hay `24-09-2025`, día > 12, así que no es `MM-dd`),
una fila por día del 2023-01-01 al 2025-09-26; 5 categorías; 3 segmentos; `Price` 14.59–999.42; `Discount` 0.01–49.92; `Marketing_Spend`
100.30–9995.62; `Units_Sold` 5–57.

- Conversión con `try_to_date` / `try_cast`: un fallo da NULL + bandera, nunca error ni descarte. Cadenas vacías → NULL.
- **No se descarta ninguna fila**; `dq_is_valid` solo marca. Gold consume únicamente `dq_is_valid = true`.
- Banderas: `dq_null_field`, `dq_conversion_failed`, `dq_duplicate` (repetición de los 7 campos originales), `dq_range_violation`
  (`price<=0`, `discount_value<0`, `marketing_spend<0`, `units_sold<0`).
- `Discount` → `discount_value DOUBLE`: **la unidad (porcentaje vs. importe) no está confirmada**; solo se tipa.
- Trazabilidad: `_bronze_row_id` (clave a Bronze), `_source_file`, `_ingested_at`, `_silver_processed_at`.

## Métricas Gold

Sobre filas válidas de Silver. `records`=COUNT(*); `units_sold_total`=SUM(units_sold); `avg_units_per_record`=AVG(units_sold);
`avg_price`=AVG(price) (media simple por registro, no ponderada); `avg_discount_value`=AVG(discount_value) (unidad original);
`marketing_spend_total`=SUM; `avg_marketing_spend`=AVG; `list_price_revenue`=SUM(price × units_sold) (**ingreso bruto a precio de lista,
sin descuento; NO es venta neta**); `marketing_spend_per_unit`=marketing_spend_total / units_sold_total.
Supuestos: `Price` es precio unitario; cada fila es un registro diario. No hay ventas netas ni uso de `Discount` hasta confirmar su semántica.

## Evidencias de ejecución (2026-11-12/13, run serverless, 5 tareas SUCCESS)

| Comprobación | Resultado |
|---|---|
| Esquemas | `retail_bronze`, `retail_silver`, `retail_gold` existen (bronze ya existía, vacío; silver/gold creados) |
| Tablas | 6 tablas `MANAGED` / `DELTA` en `information_schema.tables` |
| Conteos | RAW 1000 → Bronze 1000 → Silver 1000 → Gold (suma de `records` por categoría/segmento/mes/KPI) 1000 |
| Esquema Bronze | 7 STRING originales + `_source_file`, `_source_file_modified_at` (TIMESTAMP), `_ingested_at`, `_bronze_row_id` (LONG) |
| Esquema Silver | `sale_date DATE`, `price/discount_value/marketing_spend DOUBLE`, `units_sold INT`, 5 banderas BOOLEAN, metadatos |
| DQ Silver | nulos 0, conversión fallida 0, duplicados 0, fuera de rango 0, válidas 1000/1000; fechas 2023-01-01…2025-09-26 |
| Gold | 5 categorías, 3 segmentos, 33 meses, 1 fila KPI: 29,631 unidades, `avg_price` 505.2419, marketing 4,912,830.24, `list_price_revenue` 15,002,484.56 |
| Trazabilidad y reconciliación | 0 filas Bronze sin correspondencia en Silver (aserción en `02` y `04`). Gold por categoría, segmento y mes = Silver válido en registros, unidades y marketing (aserción en `03`); el KPI se comprueba en registros y unidades (`04`). Detalle y límites en [CIERRE_V1.md](CIERRE_V1.md#7-métricas-y-reconciliación) |
| SQL | Todas las tablas consultadas con éxito vía SQL Warehouse serverless (Statement API) |
| Anti-sobrescritura | Reejecutar Bronze → FAILED por diseño; tabla intacta (1000 filas) |

Con estos datos limpios las banderas DQ salen a 0: el control está implementado y ejecutado, pero no se ha ejercitado con datos sucios.

## Limitaciones conocidas

Lista completa y razonada en la sección 11 de [CIERRE_V1.md](CIERRE_V1.md). Resumen:

- Los controles de calidad solo tienen validación positiva (sin pruebas negativas) y las reglas de rango/dominio tienen cobertura limitada.
- No existe un procedimiento de reprocesamiento documentado, probado y reproducible; las tablas están protegidas contra sobrescritura, lo que impide una segunda ejecución normal.
- `Price` como precio unitario y "una fila = un registro diario" son hipótesis, no hechos confirmados.
- `scripts/validar_repo.py` terminó sin errores, pero no valida directamente `lakehouse_lab/`. No hay pruebas automatizadas específicas del laboratorio.
- Free Edition: solo cómputo serverless, un workspace, cuotas limitadas; sin separación dev/prod física.
- `Discount`: confirmar unidad con la fuente del dataset antes de calcular ventas netas.
- El Silver de este laboratorio sigue el esquema `retail_*`; el pipeline S3 original usa `bronze/silver/gold` y nombres distintos: no hay integración entre ambos.
- Los notebooks no están empaquetados como Asset Bundle para este workspace (se importaron con CLI); pendiente si se desea CI/CD.
- Las pruebas de calidad con datos defectuosos (nulos, duplicados, fechas inválidas) no están automatizadas.
