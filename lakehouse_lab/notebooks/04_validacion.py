# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Validación end-to-end (solo lectura)
# MAGIC Esquemas, tablas, conteos, esquemas, DQ, Gold, consulta SQL y trazabilidad RAW → Bronze → Silver → Gold.

# COMMAND ----------

import json
from pyspark.sql import functions as F
ev = {}
ev["schemas"] = sorted(r.databaseName for r in spark.sql("SHOW SCHEMAS IN workspace").collect() if r.databaseName.startswith("retail_"))
tablas = ["retail_bronze.ecommerce_sales", "retail_silver.ecommerce_sales", "retail_gold.sales_by_category",
          "retail_gold.sales_by_segment", "retail_gold.sales_by_month", "retail_gold.sales_kpi_overview"]
ev["tables"] = {}
for t in tablas:
    fq = f"workspace.{t}"
    ev["tables"][t] = {"rows": spark.table(fq).count(),
                       "format": spark.sql(f"DESCRIBE DETAIL {fq}").first()["format"],
                       "schema": [f"{c}:{d}" for c, d in spark.table(fq).dtypes]}
raw_n = spark.read.option("header", "true").csv("/Volumes/workspace/retail_raw/ecommerce_files/Ecommerce_Sales_Prediction_Dataset.csv").count()
ev["raw_rows"] = raw_n
s = spark.table("workspace.retail_silver.ecommerce_sales")
ev["silver_dq"] = s.agg(*[F.sum(F.col(c).cast("int")).alias(c) for c in
                          ["dq_null_field", "dq_conversion_failed", "dq_duplicate", "dq_range_violation", "dq_is_valid"]]).first().asDict()
b = spark.table("workspace.retail_bronze.ecommerce_sales")
ev["trace_bronze_not_in_silver"] = b.select("_bronze_row_id").exceptAll(s.select("_bronze_row_id")).count()
valid = s.filter("dq_is_valid")
g = spark.table("workspace.retail_gold.sales_kpi_overview").first()
ev["trace_gold_records_eq_silver_valid"] = (g["records"] == valid.count()) and (g["units_sold_total"] == valid.agg(F.sum("units_sold")).first()[0])
ev["sql_query"] = spark.sql("""SELECT product_category, records, units_sold_total, avg_price
                               FROM workspace.retail_gold.sales_by_category ORDER BY units_sold_total DESC""").toPandas().to_dict("records")
assert raw_n == ev["tables"]["retail_bronze.ecommerce_sales"]["rows"] == ev["tables"]["retail_silver.ecommerce_sales"]["rows"]
assert ev["trace_bronze_not_in_silver"] == 0 and ev["trace_gold_records_eq_silver_valid"]
print("VALIDATION_JSON=" + json.dumps(ev, default=str))
