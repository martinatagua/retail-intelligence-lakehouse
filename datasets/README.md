# datasets/

Carpeta **requerida** por la estructura del enunciado. La **fuente principal** de procedencia, atribución, licencias y decisión de publicación
es [DATASETS.md](../DATASETS.md) (raíz del repositorio); este archivo aporta el detalle técnico y debe leerse de forma coherente con él.

**Qué incluye el repositorio versionado** (decisión de distribución del propietario):

- **E-commerce: incluido.** `ecommerce/Ecommerce_Sales_Prediction_Dataset.csv`.
- **Automobile: EXCLUDED FROM INITIAL PUBLICATION.** `automobiles/Automobile_data.csv` **no se versiona**: `.gitignore` lo excluye (solo ese CSV, no la carpeta), no está
  rastreado y no figura en el historial Git. El autor lo conserva en su equipo local. Su identidad frente a la distribución de UCI no está confirmada.
  Quien clone el repositorio debe obtenerlo por separado (ver [Automobile: cómo obtenerlo](#automobile-cómo-obtenerlo-y-configurarlo)).

Los datasets son de terceros y el autor del proyecto no reclama derechos sobre ellos. **La licencia MIT de la raíz cubre exclusivamente el
código original del proyecto: no se aplica a ninguno de estos datasets** ni a otros materiales de terceros, y no sustituye ni modifica las
condiciones que cada fuente declare. Las licencias que se indican abajo son las **declaradas por las fuentes**, no una verificación legal.
E-commerce y Automobile **no tienen la misma situación**: el primero se incluye (CC0 1.0 declarada por su fuente, archivo verificado byte a byte);
el segundo se excluye de la publicación inicial.

El pipeline **no** lee los CSV desde esta carpeta: se suben a `s3://<nombre-del-bucket>/raw/` y se leen directamente desde S3.
Aquí, E-commerce sirve para las pruebas locales (`tests/`) y como referencia del esquema ([docs/esquemas_detectados.md](../docs/esquemas_detectados.md)).
Las pruebas públicas de Automobile usan **datos sintéticos** (`tests/datos_sinteticos.py`), no este dataset, de modo que un clon sin el CSV de
Automobile puede validarse y ejecutar sus pruebas.

| Archivo | Filas × columnas | Bytes | SHA-256 |
|---|---|---|---|
| `automobiles/Automobile_data.csv` (**no versionado**: copia local del autor) | 205 × 26 | 25 070 | `2c7c43bd00c53112d7766dd825b986b57aa15a0450815ef568d60216fbe5e587` |
| `ecommerce/Ecommerce_Sales_Prediction_Dataset.csv` | 1000 × 7 | 52 879 | `db6b4ebe74af038cb0671b2cadb4f0ffcd69311e6ec999d1ee0265e4b51d7162` |

El SHA-256 es la **huella de la copia local** de cada archivo. Para E-commerce **sí coincide** con el de la descarga oficial de Kaggle (BYTE IDENTICAL,
verificado el 2026-11-13; ver [DATASETS.md](../DATASETS.md)). Para Automobile **no prueba** que coincida con la distribución de UCI, cuyo SHA-256 no se conserva.

## Fuentes, atribución y estado de las licencias

Actualizado el 2026-11-13. Estas licencias son las que **declaran las fuentes**, no el resultado de una revisión legal independiente.
Para E-commerce, los metadatos de la ficha de Kaggle (propietario, licencia, versión) se leyeron del API público el 2026-11-13. El PDF del enunciado
lo aportó el propietario del proyecto. No hay capturas archivadas de las páginas de licencia; esta documentación informa lo declarado en las fuentes
y no presenta una resolución jurídica.

| Archivo | Fuente inmediata (publicador) | Licencia declarada por esa fuente | Origen declarado | Pendiente |
|---|---|---|---|---|
| Automobiles | Descarga obtenida desde Kaggle; publicación de Sumaya23 Abdul, *Automobile Database* | La página de Kaggle declara **CC0: Public Domain** | Correspondencia identificada con el dataset *Automobile* de UCI, Jeffrey C. Schlimmer (1985); UCI declara **CC BY 4.0** | Revisar las condiciones aplicables antes de redistribuir; no se afirma que una declaración sustituya a la otra |
| E-commerce | Descarga directa desde Kaggle; publicación de Nevil Dhinoja, *E-commerce Sales Prediction Dataset* (v1, 2024-12-14) | Kaggle declara **CC0 1.0** | Sintético, según la descripción del autor | Ninguna captura archivada |

Los dos CSV se conservan sin modificar. Decisión del propietario: **E-commerce se incluye** en el repositorio, con su atribución y la
licencia CC0 1.0 que Kaggle declara (declaración de la fuente, sin captura archivada ni verificación legal independiente); **Automobile se excluye
de la publicación inicial**. Esta documentación **no declara Automobile autorizado para publicación** ni lo considera cubierto por CC BY 4.0 o por la CC0 de un tercero.

### Qué está y qué no está establecido

| Aspecto | E-commerce | Automobiles |
|---|---|---|
| Procedencia identificada | Kaggle, publicado por Nevil Dhinoja | Kaggle, publicado por Sumaya23 Abdul; correspondencia identificada con *Automobile* de UCI (Schlimmer, 1985) |
| Equivalencia de contenido con el original, verificada | **Sí: BYTE IDENTICAL** con la descarga oficial de Kaggle (2026-11-13) | **No** verificada de forma reproducible |
| Atribución documentada | Sí | Sí |
| Licencia declarada por la fuente de descarga | CC0 1.0 (Kaggle, propietario de la publicación); sin captura archivada | CC0 (Kaggle, publicación de un tercero); sin captura archivada |
| Licencia declarada por la fuente original identificada | No aplica | CC BY 4.0 (UCI); sin captura archivada |
| Condiciones de redistribución verificadas | Licencia declarada por la fuente primaria confirmada en el API de Kaggle; **no** es una verificación jurídica independiente | **No** |
| Incluido en el repositorio versionado | **Sí** (decisión del propietario) | **No**: EXCLUDED FROM INITIAL PUBLICATION (`.gitignore`) |
| Redistribución de Automobile | No aplica a este punto | No autorizada ni afirmada: la copia local no está cubierta automáticamente por CC BY 4.0 |

### Automobiles: `Automobile_data.csv`

| | |
|---|---|
| Fuente de descarga del CSV | Kaggle: [*Automobile Database*](https://www.kaggle.com/datasets/sumaya23abdul/automobile-database), publicada por Sumaya23 Abdul. Esta es la fuente de descarga utilizada. |
| Declaración de la publicación de Kaggle | La página de Kaggle declara **CC0: Public Domain** para esa distribución. No hay captura archivada de la página. |
| Procedencia identificada | Correspondencia con *Automobile*, UCI Machine Learning Repository, atribuido a Jeffrey C. Schlimmer (1985): [página del dataset UCI](https://archive.ics.uci.edu/dataset/10/automobile), [DOI 10.24432/C5B01C](https://doi.org/10.24432/C5B01C). |
| Licencia declarada por UCI | **CC BY 4.0** ("This dataset is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license") |
| Relación con UCI | **Procedencia identificada; equivalencia de contenido no verificada de forma reproducible.** El CSV tiene la misma forma que el dataset de UCI (205 filas × 26 columnas, con fila de cabecera). El repositorio no conserva una comparación de valores contra `imports-85.data` (ni su procedimiento, ni su fecha, ni un hash del archivo de UCI), así que no se afirma que los valores coincidan |
| **Contexto de las declaraciones** | Kaggle declara CC0 para su publicación y UCI declara CC BY 4.0 para el dataset original atribuido a Schlimmer. Son declaraciones de fuentes distintas. Se conserva la atribución a UCI; no se presentan como incompatibles, no se afirma que una sustituya a la otra y no se formula una conclusión jurídica sobre redistribución. |

Atribución mantenida (CC BY 4.0, licencia de la obra original):

> Schlimmer, J. (1985). *Automobile* [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5B01C>.
> Licencia CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>). Obtenido a través de Kaggle (Sumaya23 Abdul), que declara CC0.
> Cambios: la copia descargada incluye una fila de cabecera (comprobable en el CSV); no se ha verificado si existen otras diferencias con el archivo
> original de UCI. El proyecto no modifica el archivo.

### Automobile: cómo obtenerlo y configurarlo

El flujo completo (notebooks `01_extract_automobiles` y `02_transform_automobiles`) espera el archivo en RAW:
`s3://<nombre-del-bucket>/raw/automobiles/Automobile_data.csv` (variable `raw_path_automobiles`). Quien clone el repositorio debe:

1. Obtener el dataset por su cuenta desde la fuente de descarga (Kaggle, enlace en la sección anterior) o desde UCI, y revisar allí sus condiciones.
2. Dejar un CSV con **cabecera** y las 26 columnas que declara `COLS_RAW_AUTOMOBILES` en `proceso/transformaciones.py` (el notebook falla con un mensaje claro si no
   coinciden). El archivo de UCI (`imports-85.data`) no trae cabecera. El SHA-256 de arriba corresponde a la copia local del autor; una descarga nueva puede diferir.
3. Subirlo a la ruta RAW anterior. Opcionalmente, copiarlo a `datasets/automobiles/Automobile_data.csv` para ejecutar las pruebas locales opcionales:
   `.gitignore` lo mantiene fuera del repositorio.

Sin ese archivo **no se pueden ejecutar** las tareas de Automobiles del job, pero sí el resto: la instalación, el validador y las pruebas públicas no lo necesitan.
Las pruebas `*_csv_real` y la variante `real` de las pruebas del dashboard solo se ejecutan si el archivo está presente; en un clon limpio se omiten con un
motivo explícito y no cuentan como ejecutadas.

### E-commerce: `Ecommerce_Sales_Prediction_Dataset.csv`

Se incluye en el repositorio por decisión del propietario. **La licencia MIT de la raíz no se aplica a este archivo**; se rige por las condiciones de su fuente
(CC0 1.0 declarada por Kaggle, sin verificación legal independiente). Ver [DATASETS.md](../DATASETS.md).

| | |
|---|---|
| Fuente | *E-commerce Sales Prediction Dataset*, de Nevil Dhinoja, en Kaggle: [kaggle.com/datasets/nevildhinoja/e-commerce-sales-prediction-dataset](https://www.kaggle.com/datasets/nevildhinoja/e-commerce-sales-prediction-dataset) |
| Fuente de descarga y publicador | Descarga directa desde Kaggle: [*E-commerce Sales Prediction Dataset*](https://www.kaggle.com/datasets/nevildhinoja/e-commerce-sales-prediction-dataset), publicado por Nevil Dhinoja. |
| Huella de esta copia | SHA-256 `db6b4ebe74af038cb0671b2cadb4f0ffcd69311e6ec999d1ee0265e4b51d7162`, 52 879 bytes. **BYTE IDENTICAL** al archivo de la descarga oficial pública de Kaggle (SHA-256 y `cmp`), comprobado el 2026-11-13 con una descarga hecha fuera del repositorio. |
| Licencia declarada por Kaggle | **CC0 1.0** (<https://creativecommons.org/publicdomain/zero/1.0/>), declarada por el propietario de la publicación (v1, 2024-12-14). Es una declaración de la fuente, no una verificación legal independiente ni una garantía de titularidad absoluta; CC0 no resuelve derechos de terceros. |
| Naturaleza | **Datos sintéticos, no obtenidos de una plataforma real**, según la descripción del autor en Kaggle (generados con NumPy y Pandas) |
| `Discount` | El publicador lo describe como **porcentaje**. Se documenta como **información declarada por la fuente**: los datos no lo confirman ([esquemas_detectados.md](../docs/esquemas_detectados.md#evidencia-sobre-discount)) y el pipeline mantiene `semantica_discount = desconocida` |
| Estadísticas de la ficha | **No se copian.** Se observaron discrepancias entre el resumen textual de `Price` en la ficha y los datos del CSV. Las estadísticas de este repositorio se calculan sobre el CSV |
| Pendiente | Opcional: archivar una captura de la ficha de Kaggle que muestre la licencia declarada, sin datos de la cuenta de quien descarga |

Atribución (CC0 no la exige; se incluye como referencia de la fuente):

> Dhinoja, N. *E-commerce Sales Prediction Dataset*. Kaggle. Licencia declarada en la fuente: CC0. (El año de publicación no se ha verificado, por lo que no se indica.)

## Antes de publicar

1. Conservar la atribución a Nevil Dhinoja y Kaggle para E-commerce, y a UCI/Jeffrey C. Schlimmer (DOI 10.24432/C5B01C, CC BY 4.0) para Automobile, según [DATASETS.md](../DATASETS.md).
2. Automobile está **excluido de la publicación inicial** y permanece fuera del repositorio versionado: no se declara autorizado ni cubierto automáticamente por CC BY 4.0. La documentación no concluye que las declaraciones CC0 (Kaggle) y CC BY 4.0 (UCI) sean incompatibles ni que una reemplace a la otra.
3. E-commerce se incluye por decisión del propietario; su licencia es la declarada por Kaggle, sin verificación legal independiente. No se han archivado capturas de páginas de licencia.
4. Si más adelante se decide incluir Automobile, habrá que confirmar antes la identidad de la copia frente a UCI, retirar la regla de `.gitignore` y actualizar esta página, `DATASETS.md` y la checklist; hoy el validador (`scripts/validar_repo.py`) falla si una copia de Automobile llega a los archivos publicables.
