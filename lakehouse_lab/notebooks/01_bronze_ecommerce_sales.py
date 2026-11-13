# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · RAW (Managed Volume) → Bronze
# MAGIC Lee el CSV del Volume **sin inferir tipos** (todo `string`, sin conversiones destructivas), conserva los 7 campos
# MAGIC originales y añade metadatos: `_bronze_row_id`, `_source_file`, `_source_file_modified_at`, `_ingested_at`.
# MAGIC Crea la tabla con `saveAsTable()` sin modo. Si la tabla ya existe, **se detiene sin reemplazarla**.

# COMMAND ----------

from pyspark.sql import functions as F

ORIGEN = "/Volumes/workspace/retail_raw/ecommerce_files/Ecommerce_Sales_Prediction_Dataset.csv"
DESTINO = "workspace.retail_bronze.ecommerce_sales"
COLUMNAS = ["Date", "Product_Category", "Price", "Discount", "Customer_Segment", "Marketing_Spend", "Units_Sold"]

if spark.catalog.tableExists(DESTINO):
    n = spark.table(DESTINO).count()
    raise RuntimeError(f"{DESTINO} ya existe ({n} filas). No se reemplaza; revisar manualmente.")

# COMMAND ----------

df_raw = (spark.read.format("csv")
          .option("header", "true").option("inferSchema", "false")
          .option("mode", "FAILFAST").option("encoding", "UTF-8")
          .load(ORIGEN))
assert df_raw.columns == COLUMNAS, f"Columnas inesperadas: {df_raw.columns}"

df_bronze = (df_raw
    .select(*COLUMNAS,
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias("_source_file_modified_at"))
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_bronze_row_id", F.monotonically_increasing_id()))

df_bronze.write.format("delta").saveAsTable(DESTINO)

# COMMAND ----------

# MAGIC %md ## Verificación

# COMMAND ----------

n_raw = df_raw.count()
t = spark.table(DESTINO)
n_b = t.count()
assert n_raw == n_b == 1000, f"RAW={n_raw}, Bronze={n_b}"
assert all(dt == "string" for c, dt in t.dtypes if c in COLUMNAS), "Bronze debe conservar strings"
assert t.select("_bronze_row_id").distinct().count() == n_b
print(f"RAW={n_raw} Bronze={n_b} columnas_originales={len(COLUMNAS)}")
t.printSchema()
display(spark.sql(f"DESCRIBE DETAIL {DESTINO}").select("format", "numFiles"))
display(t.limit(5))
