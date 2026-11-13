# Decisiones arquitectónicas y cuestiones por confirmar

Aquí se registran las diferencias con el enunciado o con el repositorio de referencia. **No están resueltas en el código**:
cada una necesita una confirmación humana (del profesor o evaluador del curso, o del autor del proyecto). No se ha cambiado nada para «resolverlas» por cuenta propia.

## D1. Acceso a RAW: Managed Identity (enunciado) frente a IAM Role de AWS (implementación)

**Pendiente de confirmar con el profesor.**

El enunciado menciona **Managed Identity** para acceder a Raw, que es el mecanismo de Azure (Access Connector para Azure
Databricks con identidad administrada sobre ADLS Gen2). El proyecto se implementó sobre **AWS S3** como almacenamiento, así que la
implementación usa el mecanismo análogo de AWS en Unity Catalog (que no es el mismo, como se explica después):

| | Enunciado (Azure) | Implementación actual (AWS) |
|---|---|---|
| Almacenamiento | ADLS Gen2 | Amazon S3; bucket configurado localmente mediante `s3_bucket` |
| Identidad hacia el almacenamiento | Managed Identity del Access Connector | **IAM Role** de AWS, con trust policy hacia Unity Catalog y External ID |
| Objeto de UC | Storage Credential (Managed Identity) + External Location | Storage Credential (IAM Role) + External Location sobre la raíz del bucket |
| Claves en notebooks | Ninguna | Ninguna |

**No son mecanismos idénticos.** Los dos evitan secretos en el código y delegan la autorización en Unity Catalog, pero difieren en
la nube, en el tipo de identidad (una identidad administrada de Entra ID frente a un rol asumido mediante STS) y en la configuración
(Access Connector frente a trust policy con External ID). Que el IAM Role satisfaga el requisito «Managed Identity» lo tiene que
confirmar el profesor. Si exige Azure, haría falta otro workspace y otro almacenamiento; eso no se ha hecho.

## D2. Datasets: E-commerce y Automobiles frente a los del ejemplo

**Pendiente de confirmar contra el enunciado completo.**

- El proyecto usa **dos fuentes independientes, E-commerce y Automobiles**, elegidas para cumplir el requisito «al menos dos fuentes» (según la lista de requisitos conocida; pendiente de contrastar con el PDF).
- Se ha señalado que el material del profesor muestra `matriculados.csv` y `placement (1).csv`. En el repositorio de referencia
  `Enrykiel/databricks_project`, consultado el 2026-10-21 en sus ramas `main` y `dev`, **esos dos nombres no aparecen**: su `datasets/`
  contiene `ps_enrollment-1.csv`, `ps_enrollment-2.csv`, `ps_enrollment-3.csv`, `ps_prog_tbl.csv` y `ps_term_tbl.csv`. Esos nombres
  podrían venir del PDF o de otra versión del ejemplo.
- Falta confirmar si el enunciado **exige** datasets concretos o solo «al menos dos fuentes». No se han cambiado los datasets.

## D3. Licencias de los CSV

**Procedencia documentada. E-commerce verificado byte a byte (2026-11-13); Automobile excluido de la publicación inicial.** Las fuentes, las licencias declaradas y la decisión de publicación
están en [DATASETS.md](../DATASETS.md), con el detalle técnico en [datasets/README.md](../datasets/README.md). No se han archivado capturas de las páginas.

Esto no resuelve **D2**: que la procedencia esté documentada no significa que el profesor acepte estos datasets.

## D4. Almacenamiento sin restricción de solo lectura

**Decisión aceptada, con endurecimiento opcional.** La External Location cubre la raíz del bucket con lectura, escritura y borrado.
Los notebooks solo leen RAW y escriben en `lakehouse/`, pero eso lo garantiza el código, no el almacenamiento
(ver [seguridad/README.md](../seguridad/README.md#acceso-al-almacenamiento-qué-está-restringido-y-qué-no)).

## D5. dev y prod en un solo workspace

**Decisión aceptada.** Free Edition ofrece un único workspace. dev y prod se separan lógicamente (esquemas `dev_*` frente a
`bronze/silver/gold`, y `lakehouse/dev` frente a `lakehouse/prod`) dentro del catálogo `workspace`. No son dos workspaces físicos.

## D6. Producción y CI/CD sin ejecutar

**Pendiente.**
- Producción no se ha desplegado ni ejecutado. En dev, el autor comunicó `validate --strict`, `deploy` y run correctos con una **versión anterior a `s3_bucket`**, sin capturas ni logs originales almacenados en el repositorio (ver el [README](../README.md#estado-del-proyecto)). Falta repetir la validación con el bundle actual, tras comprobar las ubicaciones de las tablas ([procedimiento](configuracion_pendiente.md#antes-de-volver-a-ejecutar-el-etl-dev)).
- GitHub Actions no se ha ejecutado nunca.
- Está sin decidir la autenticación de CI, OAuth M2M o PAT (ver [configuracion_pendiente.md](configuracion_pendiente.md#autenticación-de-github-actions-no-verificada-todavía)).

## D7. Política del curso sobre asistencia de IA

**Declaración resuelta el 2026-11-13; consulta de la política del curso, pendiente.** *(El texto siguiente, hasta la actualización fechada, es la decisión original y se conserva como historial.)*

No consta en el repositorio ninguna política del curso sobre el uso de herramientas de IA (el PDF del enunciado no está
en el repositorio). Por eso esta documentación **no declara ni niega** que se hayan utilizado esas herramientas: es una decisión del
propietario, tras consultar la política aplicable al curso. Hasta entonces, las afirmaciones de autoría del [README](../README.md#autoría-y-alcance)
describen la autoría declarada por el propietario y no resuelven esta cuestión.

### Actualización 2026-11-13

- **Decisión del propietario:** declarar el uso de herramientas de IA en el proyecto. La posición anterior («ni declara ni niega») queda superada en cuanto a la declaración.
- **Herramientas y funciones declaradas:** Claude Code (implementación y documentación), Codex (revisiones y auditorías técnicas) y ChatGPT (planificación y orientación técnica).
  El autor definió los objetivos, tomó las decisiones de diseño, supervisó implementaciones y validaciones, revisó los resultados y asume la responsabilidad final.
- **Texto incorporado:** sección «Uso de herramientas de IA» del [README](../README.md#uso-de-herramientas-de-ia). La sección de autoría del README se ajustó para que no
  atribuya en exclusiva al autor el desarrollo ni acredite la autoría de fragmentos concretos.
- **Razón:** una declaración de autoría sin mención de la asistencia de IA contradecía el desarrollo real del proyecto y la decisión de transparencia del propietario.
  La declaración no atribuye a una herramienta tareas que no realizó, y las revisiones de IA se presentan como asistidas y automatizadas, no como auditoría humana independiente.
- **Política académica:** sigue **sin constar** en el repositorio ninguna política del curso sobre IA, y no hay evidencia de que permita cualquier uso. Esta declaración
  de transparencia **no sustituye ni resuelve** las obligaciones académicas externas: el propietario debe consultar y respetar la política aplicable. Esa consulta sigue pendiente.

## D8. Distribución de los datasets

**Decisión del propietario aplicada (actualizada el 2026-11-13).** Automobile queda **excluido de la publicación inicial**.
- **E-commerce se incluye** en el repositorio, con atribución a Nevil Dhinoja (Kaggle) y la licencia CC0 1.0 declarada por la fuente. Su archivo es **BYTE IDENTICAL** a la descarga oficial de Kaggle (verificado el 2026-11-13). CC0 es una declaración del propietario de la publicación, no una garantía de titularidad absoluta ([DATASETS.md](../DATASETS.md)).
- **Automobile se excluye** de la publicación inicial (`.gitignore`; no rastreado y fuera del historial; se conserva en el equipo local). La copia local no tiene identidad confirmada frente a la distribución de UCI (Schlimmer, CC BY 4.0, DOI 10.24432/C5B01C) y no se considera cubierta automáticamente por ninguna licencia.
- Consecuencia: un clon no trae Automobile. Las pruebas públicas usan datos sintéticos y el flujo completo exige obtener el CSV por separado
  ([datasets/README.md](../datasets/README.md#automobile-cómo-obtenerlo-y-configurarlo)).
- Sigue sin confirmarse con el profesor si el enunciado acepta esta forma de entrega de los datasets ([D2](#d2-datasets-e-commerce-y-automobiles-frente-a-los-del-ejemplo)).
- La documentación y consultas derivadas de Automobile (esquema y conteos en `docs/esquemas_detectados.md`, cifras y consultas de `dashboard/`) describen el dataset, no lo contienen. El propietario decidió mantenerlas únicamente con atribución apropiada a la fuente UCI y dejando clara su procedencia ([DATASETS.md](../DATASETS.md)).
