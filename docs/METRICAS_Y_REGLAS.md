# Métricas y semántica de evaluación

Se utiliza la ponderación del PRD: **30% completitud, 30% validez, 20% unicidad, 20% consistencia**. Los pesos están centralizados en `src/quality/engine.py`.

| Dimensión | Cálculo |
|---|---|
| Completitud C | 100 × (1 − celdas faltantes / celdas totales) |
| Unicidad U | 100 × (1 − filas duplicadas excedentes / filas totales) |
| Validez V | 100 × (1 − fallos de reglas de validez / evaluaciones elegibles de esas reglas) |
| Consistencia I | 100 × (1 − fallos de reglas de consistencia / evaluaciones elegibles de esas reglas) |

Con las cuatro dimensiones disponibles: `QS = 0.30 C + 0.30 V + 0.20 U + 0.20 I`.

Si no hay evaluaciones elegibles para una dimensión, su valor es N/D. El score divide la suma ponderada disponible entre la suma de sus pesos. La cobertura indica qué porcentaje del peso original pudo evaluarse. Un 100 con cobertura del 50% no significa que se haya comprobado validez y consistencia. El umbral ilustrativo de alerta es 90; no es un criterio empresarial validado.

**No es exactitud factual**: el sistema no sabe si una dirección o una venta es verdadera; solo comprueba presencia, formatos, reglas y relaciones configuradas. El responsable de negocio define los límites y catálogos.

## Duplicados y valores faltantes

- Por defecto compara filas completas. Con claves compara exclusivamente esas columnas.
- De un grupo de tres filas iguales, cuenta dos excedentes para unicidad (`keep='first'`).
- Una regla `unique` marca todos los participantes no nulos de un grupo duplicado: tres fallos. Es deliberadamente distinta del conteo anterior.
- Vacío y espacios son faltantes; las cadenas `NA`, `NULL`, `N/A` no se convierten silenciosamente en nulos.
- Las reglas distintas de `required` omiten los nulos. `compare` omite registros con cualquiera de los dos campos ausentes. Combina `required` si necesitas exigir presencia.
- `required` participa también en la dimensión configurada; un faltante puede afectar completitud y una regla. Los hallazgos no son un conteo de filas únicas afectadas.
- Se preserva texto original: identificadores `001` no se convierten en `1`. Los numéricos se convierten temporalmente para comprobar reglas. Se espera punto decimal.
- El índice `registro` en incidencias empieza en 1 tras los encabezados. No equivale a la línea física si hay campos multilínea.

## Configuración JSON

Cada regla necesita `id` único, `type` y `column`. `dimension` es opcional (`validez` por defecto, o `consistencia`). Los nombres de columnas son exactos y sensibles a mayúsculas.

```json
[
  {"id":"R1", "type":"required", "column":"cliente"},
  {"id":"R2", "type":"unique", "column":"id"},
  {"id":"R3", "type":"range", "column":"edad", "min":18, "max":100},
  {"id":"R4", "type":"allowed", "column":"estado", "values":["pagado","pendiente"]},
  {"id":"R5", "type":"regex", "column":"codigo", "pattern":"[A-Z]{3}[0-9]{4}"},
  {"id":"R6", "type":"date", "column":"fecha", "format":"%Y-%m-%d"},
  {"id":"R7", "type":"compare", "column":"descuento", "other":"total", "op":"<=", "dimension":"consistencia"}
]
```

`range` es inclusivo y puede tener solo un límite. `regex` exige coincidencia completa. `compare` es una comparación numérica entre dos columnas y admite `<=`, `>=`, `==`; no interpreta fórmulas arbitrarias. `date` usa la semántica de parsing de Pandas con formato explícito. Una configuración inválida detiene el análisis, no se ignora silenciosamente.

`compare` admite además `"value_type":"date"` junto con `"format":"%Y-%m-%d"` para comparar fechas. Los valores presentes no convertibles y los números infinitos fallan sus reglas. Los límites deben ser finitos. También se aceptan las reglas originales con `tipo`, `columna`, `minimo`, `maximo`, `valores`, `columna_izquierda/derecha` y `columna_inicio/fin`; se normalizan antes del análisis. Ejemplo completo: `config/reglas_empleos.json`.

Guarda los JSON desde la interfaz para reutilizarlos. Cada ejecución almacena un snapshot y hash de sus reglas; editar un archivo no cambia análisis anteriores. No se incluye un catálogo central de reglas con roles o aprobaciones.

## Anomalías exploratorias

IQR marca valores numéricos fuera de `[Q1−1.5 IQR, Q3+1.5 IQR]`. Requiere al menos ocho valores no nulos, todos convertibles a número, e IQR mayor que cero. No entra en el score. Evita interpretar identificadores numéricos o precios legítimamente extremos como errores confirmados. No hay entrenamiento ML ni corrección automática.

## Muestras y límites

Se calculan conteos sobre el archivo completo y se conservan hasta 2 000 incidencias detalladas en total, en orden: faltantes, duplicados, reglas, anomalías. En archivos con muchos problemas, la muestra puede agotarse antes de las últimas categorías; los resúmenes de reglas y conteos siguen completos. El filtro de interfaz solo consulta la muestra. JSON guarda `muestra_limitada` y `conteos`. Para análisis exhaustivo por registro se necesita ampliar este diseño a almacenamiento/paginación de incidencias.

`registros_con_errores` y su porcentaje cuentan posiciones únicas afectadas, independientemente del límite de muestra; incluyen anomalías si están activas. `reglas_incumplidas` cuenta reglas con uno o más fallos. El perfil añade porcentaje de nulos, media, desviación muestral, cuartiles, mediana, ejemplos y frecuencias; los cálculos numéricos excluyen valores no convertibles o no finitos. El tipo inferido exige mayoría estricta entre los valores no nulos (numérico, fecha ISO, booleano; en otro caso texto). No se convierte el CSV original.

## Complemento inteligente del MVP

Isolation Forest aprende patrones conjuntos de varias columnas y registra sus hallazgos bajo `anomalia_multivariada`; el detalle se conserva en `inteligencia`. No modifica las fórmulas del Quality Score ni la cobertura. El total `anomalias` suma hallazgos IQR (puede haber varios por fila) y hallazgos multivariados (uno por fila); `registros_con_errores` cuenta filas afectadas sin duplicarlas entre reglas o detectores. Un registro atípico puede ser correcto. Véase [COMPONENTE_INTELIGENTE.md](COMPONENTE_INTELIGENTE.md).
