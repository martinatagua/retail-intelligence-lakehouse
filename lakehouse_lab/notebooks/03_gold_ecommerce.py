# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Silver → Gold
# MAGIC Entrada: filas de Silver con `dq_is_valid = true`. **No se calculan ventas netas** ni se aplica `Discount`
# MAGIC (unidad no confirmada).
# MAGIC
# MAGIC **Métricas** (por grupo): `records` = COUNT(*); `units_sold_total` = SUM(units_sold); `avg_units_per_record` = AVG(units_sold);
# MAGIC `avg_price` = AVG(price) (media simple por registro); `avg_discount_value` = AVG(discount_value) (en la unidad original, sin interpretar);
# MAGIC `marketing_spend_total` = SUM(marketing_spend); `avg_marketing_spend`; `list_price_revenue` = SUM(price × units_sold)
# MAGIC (**ingreso a precio de lista, bruto, sin descuento**; no es venta neta); `marketing_spend_per_unit` = marketing_spend_total / units_sold_total.
# MAGIC
# MAGIC **Supuesto:** cada fila es un registro diario de una categoría/segmento (1 fila por fecha); `Price` es precio unitario.
# MAGIC Gold: `sales_by_category`, `sales_by_segment`, `sales_by_month`, `sales_kpi_overview`.

# COMMAND ----------

from pyspark.sql import functions as F

SILVER = "workspace.retail_silver.ecommerce_sales"
GOLD = "workspace.retail_gold"
destinos = {n: f"{GOLD}.{n}" for n in ["sales_by_category", "sales_by_segment", "sales_by_month", "sales_kpi_overview"]}
existentes = [d for d in destinos.values() if spark.catalog.tableExists(d)]
if existentes:
    raise RuntimeError(f"Ya existen {existentes}. No se reemplazan; revisar manualmente.")

base = spark.table(SILVER).filter("dq_is_valid")

def agg(df, *keys):
    g = df.groupBy(*keys) if keys else df.groupBy()
    return g.agg(
        F.count("*").alias("records"),
        F.sum("units_sold").alias("units_sold_total"),
        F.round(F.avg("units_sold"), 4).alias("avg_units_per_record"),
        F.round(F.avg("price"), 4).alias("avg_price"),
        F.round(F.avg("discount_value"), 4).alias("avg_discount_value"),
        F.round(F.sum("marketing_spend"), 2).alias("marketing_spend_total"),
        F.round(F.avg("marketing_spend"), 4).alias("avg_marketing_spend"),
        F.round(F.sum(F.col("price") * F.col("units_sold")), 2).alias("list_price_revenue"),
    ).withColumn("marketing_spend_per_unit", F.round(F.col("marketing_spend_total") / F.col("units_sold_total"), 4))

by_cat = agg(base, "product_category")
by_seg = agg(base, "customer_segment")
by_month = agg(base.withColumn("year_month", F.date_format("sale_date", "yyyy-MM")), "year_month")
kpi = agg(base).withColumn("date_min", F.lit(base.agg(F.min("sale_date")).first()[0])) \
               .withColumn("date_max", F.lit(base.agg(F.max("sale_date")).first()[0]))
resultados = {"sales_by_category": by_cat, "sales_by_segment": by_seg,
              "sales_by_month": by_month, "sales_kpi_overview": kpi}
for n, df in resultados.items():
    df.withColumn("_gold_processed_at", F.current_timestamp()).write.format("delta").saveAsTable(destinos[n])

# COMMAND ----------

# MAGIC %md ## Verificación (reconciliación con Silver)

# COMMAND ----------

tot = base.agg(F.count("*"), F.sum("units_sold"), F.round(F.sum("marketing_spend"), 2)).first()
for n in ["sales_by_category", "sales_by_segment", "sales_by_month"]:
    r = spark.table(destinos[n]).agg(F.sum("records"), F.sum("units_sold_total"), F.round(F.sum("marketing_spend_total"), 2)).first()
    assert tuple(r) == tuple(tot), f"{n}: {tuple(r)} != Silver {tuple(tot)}"
    print(n, "OK", tuple(r))
for n, d in destinos.items():
    print("\n==", d); display(spark.table(d).orderBy(spark.table(d).columns[0]))
