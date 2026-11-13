# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup de esquemas (laboratorio Free Edition)
# MAGIC Crea `retail_bronze`, `retail_silver` y `retail_gold` en el catálogo `workspace` **solo si no existen**
# MAGIC (`CREATE SCHEMA IF NOT EXISTS`). No elimina ni modifica esquemas existentes.

# COMMAND ----------

CATALOGO = "workspace"
COMENTARIOS = {
    "retail_bronze": "Bronze layer - Retail Intelligence Lakehouse",
    "retail_silver": "Silver layer - Retail Intelligence Lakehouse (tipado y calidad)",
    "retail_gold": "Gold layer - Retail Intelligence Lakehouse (tablas analiticas)",
}
for esquema, comentario in COMENTARIOS.items():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOGO}.{esquema} COMMENT '{comentario}'")

existentes = {r.databaseName for r in spark.sql(f"SHOW SCHEMAS IN {CATALOGO}").collect()}
faltan = set(COMENTARIOS) - existentes
assert not faltan, f"Faltan esquemas: {faltan}"
print("Esquemas OK:", sorted(set(COMENTARIOS) & existentes))
