# DATASETS — procedencia, licencias y decisión de publicación

Este documento es la referencia de procedencia y licencias de los datos del proyecto. Detalle técnico adicional (esquemas, forma de
obtener Automobile, pruebas): [datasets/README.md](datasets/README.md).

**Los datasets no son obra del autor del proyecto**, que no reclama derechos sobre ellos. Cada dataset se rige por las condiciones de su
fuente, no por la licencia MIT del código.

## Resumen

| Dataset | Fuente | Autor / titular declarado | Licencia declarada por la fuente | Identidad del archivo local | Decisión de publicación |
|---|---|---|---|---|---|
| E-commerce Sales Prediction Dataset (`datasets/ecommerce/Ecommerce_Sales_Prediction_Dataset.csv`) | Kaggle | Nevil Dhinoja | CC0 1.0 (declarada en Kaggle) | **BYTE IDENTICAL** a la descarga oficial de Kaggle (verificado el 2026-11-13) | **Incluido** en el repositorio, con atribución |
| Automobile (`datasets/automobiles/Automobile_data.csv`) | UCI Machine Learning Repository (referencia) | Jeffrey Schlimmer | CC BY 4.0 (declarada por UCI) | **No verificada** frente a la distribución de UCI | **EXCLUDED FROM INITIAL PUBLICATION** |

## E-commerce Sales Prediction Dataset

| | |
|---|---|
| Título | *E-commerce Sales Prediction Dataset* |
| Autor / propietario declarado | Nevil Dhinoja (propietario y creador según la ficha de Kaggle) |
| Fuente oficial | <https://www.kaggle.com/datasets/nevildhinoja/e-commerce-sales-prediction-dataset> |
| Licencia declarada en Kaggle | **CC0 1.0** (campo de licencia de la ficha: «CC0: Public Domain») |
| Texto de la licencia | <https://creativecommons.org/publicdomain/zero/1.0/> |
| Versión y fecha | v1, «Initial release», publicada el 2024-12-14 (única versión disponible en la comprobación) |
| Fecha de verificación | 2026-11-13 |
| Archivo | `datasets/ecommerce/Ecommerce_Sales_Prediction_Dataset.csv` |
| Tamaño exacto | 52 879 bytes (1000 filas de datos y 7 columnas, finales de línea CRLF) |
| SHA-256 del archivo local | `db6b4ebe74af038cb0671b2cadb4f0ffcd69311e6ec999d1ee0265e4b51d7162` |
| SHA-256 del archivo descargado de Kaggle | `db6b4ebe74af038cb0671b2cadb4f0ffcd69311e6ec999d1ee0265e4b51d7162` |
| Resultado de la comparación | **BYTE IDENTICAL** (SHA-256 idéntico y comparación binaria con `cmp`) |

**Cómo se verificó.** El 2026-11-13 se descargó el archivo desde la distribución pública oficial de Kaggle, sin credenciales, en un
directorio temporal fuera del repositorio, y se comparó con la copia local mediante SHA-256 y `cmp`. Los metadatos de la ficha
(propietario, licencia, versión, tamaño total) se leyeron del API público de Kaggle. No se archivó la respuesta ni capturas dentro del
repositorio, de modo que esta verificación es reproducible pero no está documentada con evidencia almacenada.

**Naturaleza de los datos.** Según la descripción de su autor, los datos son **sintéticos**: «synthetically generated», generados con
NumPy y Pandas, y no proceden de ninguna plataforma real de comercio electrónico. Es una declaración del autor de la publicación.
La ficha describe `Discount` como porcentaje, pero los datos no lo confirman y el proyecto no lo interpreta (ver
[datasets/README.md](datasets/README.md)).

**Alcance de CC0.** La licencia es la **declarada por el propietario de la publicación** en Kaggle. CC0 pretende liberar los derechos de
autor, conexos, de bases de datos y de extracción que el titular pueda tener, pero:

- **no resuelve automáticamente derechos de terceros** (el propio texto de CC0 dice que quien lo aplica no se hace responsable de
  obtener permisos de otras personas), ni marcas o patentes;
- el dataset se ofrece «tal cual», sin garantías;
- esta documentación **no garantiza la titularidad absoluta** sobre todos los derechos posibles: no hay evidencia independiente de la
  titularidad, más allá de la declaración del propietario en Kaggle.

**Atribución.** CC0 no exige atribución; se incluye por trazabilidad:

> Dhinoja, N. (2024). *E-commerce Sales Prediction Dataset* (v1) [Dataset]. Kaggle.
> <https://www.kaggle.com/datasets/nevildhinoja/e-commerce-sales-prediction-dataset>. Licencia declarada: CC0 1.0.

**La licencia MIT del proyecto no se aplica a este archivo.**

## Automobile

**Estado: EXCLUDED FROM INITIAL PUBLICATION.** El CSV no se incluye en la publicación inicial: está ignorado por Git, no está rastreado
y no figura en el historial. Se conserva únicamente en el equipo local del autor.

| | |
|---|---|
| Fuente de referencia | UCI Machine Learning Repository: <https://archive.ics.uci.edu/dataset/10/automobile> |
| Título | *Automobile* |
| Autor | Jeffrey Schlimmer |
| DOI | [10.24432/C5B01C](https://doi.org/10.24432/C5B01C) |
| Licencia declarada por UCI | **CC BY 4.0**: <https://creativecommons.org/licenses/by/4.0/> |
| Copia local | `datasets/automobiles/Automobile_data.csv` (205 × 26; 25 070 bytes; SHA-256 `2c7c43bd00c53112d7766dd825b986b57aa15a0450815ef568d60216fbe5e587`) |
| Identidad de la copia local | **No confirmada.** No se ha demostrado que sea idéntica a la distribución original de UCI, y su procedencia inmediata (una publicación de Kaggle de un tercero que declara CC0) no está verificada |

**La copia local no queda cubierta automáticamente por CC BY 4.0**, ni se considera redistribuible porque una copia en Kaggle declare CC0:
esa declaración es de un tercero y no sustituye a la de la fuente original ni prueba la identidad del archivo.

**Requisito de atribución (CC BY 4.0, para la obra original):** reconocer a la autoría, enlazar la licencia e indicar los cambios. Atribución
mantenida:

> Schlimmer, J. (1985). *Automobile* [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5B01C>.
> Licencia CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>).

**Material analítico derivado.** Las consultas de `dashboard/sql/` y las descripciones de esquema y conteos de `docs/` que se refieren a
Automobile describen el dataset o resumen sus datos; no lo contienen. Se mantienen únicamente con la atribución anterior y dejando clara su
procedencia: la fuente de referencia es UCI (Schlimmer) y no se afirma que la copia local sea idéntica a ella.

Quien clone el repositorio y necesite Automobile debe obtenerlo de la fuente original y revisar allí sus condiciones
([instrucciones](datasets/README.md#automobile-cómo-obtenerlo-y-configurarlo)).

## Alcance de las licencias

No se concede una licencia única e indiscriminada para todo el contenido del repositorio.

| Material | Licencia o condiciones |
|---|---|
| Código original del proyecto (`proceso/`, `reversion/`, `scripts/`, `tests/`, `resources/`, `.github/`, `lakehouse_lab/`, etc.) | **MIT**, ver [LICENSE](LICENSE) |
| Dataset E-commerce | **CC0 1.0**, conforme a la licencia declarada por su fuente (Kaggle); **no** MIT |
| Dataset Automobile | **CC BY 4.0** para la distribución oficial de UCI; la copia local no está incluida ni se considera cubierta automáticamente |
| Materiales de terceros (referencias, marcas, documentación de herramientas) | Conservan sus propias condiciones |

La licencia MIT se aplica al código original del proyecto y **no** cubre los datasets ni otros materiales de terceros.
