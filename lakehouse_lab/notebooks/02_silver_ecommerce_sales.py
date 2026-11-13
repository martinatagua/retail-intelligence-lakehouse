# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Bronze → Silver
# MAGIC **Reglas** (basadas en el perfilado de los valores reales):
# MAGIC 1. `Date` → `sale_date` con formato `dd-MM-yyyy` (confirmado: existen valores como `24-09-2025`, día > 12). Conversión con `try_to_date`/`try_cast`: un fallo produce NULL + bandera, nunca error ni descarte.
# MAGIC 2. `Price`, `Discount`, `Marketing_Spend` → `DOUBLE`; `Units_Sold` → `INT` (vía `try_cast`).
# MAGIC 3. `Product_Category`, `Customer_Segment` → `trim`; sin cambio de mayúsculas/valores.
# MAGIC 4. `Discount` → `discount_value`: **unidad NO confirmada** (rango observado 0.01–49.92, compatible con % o importe). Solo se tipa; no se interpreta.
# MAGIC 5. **No se descarta ninguna fila.** Todas pasan a Silver con banderas `dq_*`; `dq_is_valid` resume las reglas.
# MAGIC 6. Trazabilidad: `_bronze_row_id`, `_source_file`, `_ingested_at` de Bronze + `_silver_processed_at`.
# MAGIC
# MAGIC **Banderas:** `dq_null_field` (algún campo original nulo/vacío), `dq_conversion_failed` (campo no vacío que no convierte),
# MAGIC `dq_duplicate` (fila repetida respecto a los 7 campos originales; la primera ocurrencia no se marca), `dq_range_violation`
# MAGIC (`Price<=0`, `Discount<0`, `Marketing_Spend<0`, `Units_Sold<0`), `dq_is_valid` = ninguna anterior.

# COMMAND ----------

from pyspark.sql import functions as F, Window

ORIGEN = "workspace.retail_bronze.ecommerce_sales"
DESTINO = "workspace.retail_silver.ecommerce_sales"
ORIG_COLS = ["Date", "Product_Category", "Price", "Discount", "Customer_Segment", "Marketing_Spend", "Units_Sold"]

if spark.catalog.tableExists(DESTINO):
    raise RuntimeError(f"{DESTINO} ya existe ({spark.table(DESTINO).count()} filas). No se reemplaza.")
assert spark.catalog.tableExists(ORIGEN), f"Falta {ORIGEN}"

# COMMAND ----------

b = spark.table(ORIGEN)
for c in ORIG_COLS:                      # '' y espacios -> NULL (sin perder la fila)
    b = b.withColumn(c, F.when(F.trim(F.col(c)) == "", None).otherwise(F.trim(F.col(c))))

s = (b
  .withColumn("sale_date", F.expr("try_to_date(Date, 'dd-MM-yyyy')"))
  .withColumn("price", F.expr("try_cast(Price as double)"))
  .withColumn("discount_value", F.expr("try_cast(Discount as double)"))
  .withColumn("marketing_spend", F.expr("try_cast(Marketing_Spend as double)"))
  .withColumn("units_sold", F.expr("try_cast(Units_Sold as int)"))
  .withColumnRenamed("Product_Category", "product_category")
  .withColumnRenamed("Customer_Segment", "customer_segment"))

conv_fail = ((F.col("Date").isNotNull() & F.col("sale_date").isNull()) |
             (F.col("Price").isNotNull() & F.col("price").isNull()) |
             (F.col("Discount").isNotNull() & F.col("discount_value").isNull()) |
             (F.col("Marketing_Spend").isNotNull() & F.col("marketing_spend").isNull()) |
             (F.col("Units_Sold").isNotNull() & F.col("units_sold").isNull()))
any_null = F.greatest(*[F.col(c).isNull().cast("int") for c in ORIG_COLS]) == 1
w = Window.partitionBy(*ORIG_COLS).orderBy("_bronze_row_id")

s = (s.withColumn("dq_null_field", any_null)
      .withColumn("dq_conversion_failed", conv_fail)
      .withColumn("dq_duplicate", F.row_number().over(w) > 1)
      .withColumn("dq_range_violation",
                  F.coalesce((F.col("price") <= 0) | (F.col("discount_value") < 0) |
                             (F.col("marketing_spend") < 0) | (F.col("units_sold") < 0), F.lit(False)))
      .withColumn("dq_is_valid", ~(F.col("dq_null_field") | F.col("dq_conversion_failed") |
                                   F.col("dq_duplicate") | F.col("dq_range_violation")))
      .withColumn("_silver_processed_at", F.current_timestamp())
      .select("_bronze_row_id", "sale_date", "product_category", "customer_segment",
              "price", "discount_value", "marketing_spend", "units_sold",
              "dq_null_field", "dq_conversion_failed", "dq_duplicate", "dq_range_violation", "dq_is_valid",
              "_source_file", "_ingested_at", "_silver_processed_at"))

s.write.format("delta").saveAsTable(DESTINO)

# COMMAND ----------

# MAGIC %md ## Verificación y controles de calidad

# COMMAND ----------

t = spark.table(DESTINO)
n_b, n_s = spark.table(ORIGEN).count(), t.count()
assert n_b == n_s, f"Bronze={n_b} Silver={n_s}: se perdieron filas"
anti = spark.table(ORIGEN).select("_bronze_row_id").exceptAll(t.select("_bronze_row_id")).count()
assert anti == 0, "Hay filas Bronze sin correspondencia en Silver"
dq = t.agg(F.count("*").alias("filas"),
           F.sum(F.col("dq_null_field").cast("int")).alias("con_nulos"),
           F.sum(F.col("dq_conversion_failed").cast("int")).alias("conversion_fallida"),
           F.sum(F.col("dq_duplicate").cast("int")).alias("duplicados"),
           F.sum(F.col("dq_range_violation").cast("int")).alias("fuera_de_rango"),
           F.sum(F.col("dq_is_valid").cast("int")).alias("validas"))
display(dq)
print(f"Bronze={n_b} Silver={n_s}")
t.printSchema()
display(t.limit(5))
