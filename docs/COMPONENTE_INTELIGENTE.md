# Componente inteligente: anomalías multivariadas con Isolation Forest

La decisión para el prototipo es **aprendizaje no supervisado con `sklearn.ensemble.IsolationForest`**, implementado en `src/anomalies/isolation_forest.py`. Entrena un conjunto de árboles aleatorios con los datos del snapshot y estima qué registros se aíslan con mayor facilidad. Su entrenamiento sobre los valores observados constituye el componente de aprendizaje automático del título. Las reglas siguen expresando requisitos declarados y el IQR analiza extremos de una sola columna. El modelo usa varias variables a la vez. La [documentación oficial de IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) define el algoritmo y sus puntuaciones.

## Flujo implementado

1. Leer el snapshot sin modificarlo. GUI/CLI/monitor comparten el motor.
2. Seleccionar variables. La selección automática evita texto, columnas constantes, valores no finitos, identificadores reconocibles por nombre/ceros iniciales y claves/reglas `unique` conocidas por el motor. Es una heurística: revisar siempre las columnas. La GUI propone candidatas y permite desmarcarlas; la CLI admite `--anomaly-columns unidades,importe` para selección explícita, incluso cuando hay valores inválidos que deben omitirse.
3. Convertir temporalmente a números. Se omiten las filas con nulos, texto no convertible o infinitos en las columnas seleccionadas. No hay imputación ni escritura sobre la fuente. Se requieren dos columnas variables en las filas completas y al menos 20 filas completas; en caso contrario se devuelve **No evaluado** con un motivo, conservando el resto del análisis.
4. Escalar cada columna por su máximo absoluto antes de la conversión interna a float32 para evitar overflow; guardar las escalas. Ajustar 200 árboles con `max_samples=min(256, filas completas)`, `random_state=42`, `n_jobs=1` y `contamination=0.05` por defecto. La proporción puede cambiarse en la GUI (0.1–50%) o CLI (mayor que 0 hasta 0.5).
5. Evaluar el mismo snapshot: `decision = score_samples - offset_`. Señalar si `decision < 0`. Mostrar `-score_samples` como puntuación de anomalía: mayor = más atípico. **No es una probabilidad de error ni una explicación causal.**
6. Contar todos los hallazgos, ordenar el detalle por puntuación y conservar hasta 2 000 registros. Cada registro usa posición basada en 1, sin contar el encabezado; no es un número físico de línea cuando un CSV contiene saltos dentro de celdas. En el ejemplo coincide con el ID numérico.
7. Registrar método, parámetros, selección, columnas excluidas, omisiones, versión de scikit-learn, escalas, umbral y valores observados. Persistir en el JSON del histórico y exportar además `anomalias_inteligentes.csv`.

El modelo se activa por defecto en la GUI y se puede desmarcar; la CLI requiere `--intelligent`. IQR conserva su casilla independiente. Reabrir históricos anteriores no ejecuta el modelo retroactivamente. En monitoreo se reentrena por lote; no se persisten árboles ni hay aprendizaje incremental. Las anomalías suman hallazgos y registros afectados, pero **no cambian las cuatro dimensiones, cobertura ni Quality Score**.

## Demostración reproducible y resultado real

`data/input/demo_inteligente.csv` contiene 402 filas sintéticas generadas con semilla 42 por `scripts/generar_demo_inteligente.py`. Los primeros 400 registros pertenecen a dos grupos: unidades alrededor de 30 con importe alrededor de 60, y unidades alrededor de 70 con importe alrededor de 140. Las dos filas finales combinan `(30, 140)` y `(70, 60)`: valores habituales individualmente, combinaciones poco frecuentes. El ID no entra al modelo y no se entrega ninguna etiqueta de anomalía como variable.

```powershell
.\.venv311\Scripts\python.exe scripts/validar_inteligencia.py
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/demo_inteligente.csv --anomalies --intelligent --anomaly-columns unidades,importe
```

También se demuestra con **Probar detección inteligente → Resultados → Detección inteligente**. Resultado validado con scikit-learn 1.8.0, parámetros por defecto y el hash registrado en [validacion_inteligencia.json](validacion_inteligencia.json):

| Evidencia | Resultado |
|---|---|
| Registros sembrados | 401 y 402 |
| Sembrados detectados por Isolation Forest | Ambos |
| Hallazgos IQR | 0 |
| Total señalado por Isolation Forest | 21 |
| Otros registros señalados | 19 falsos positivos respecto de las etiquetas sembradas |
| Recall respecto de esas dos etiquetas | 2/2; solo este ejemplo |
| Precisión respecto de esas etiquetas | 2/21 ≈ 9.52%; no usar el recall como «exactitud» |
| Score / cobertura | 100 / 50%, porque el ejemplo no tiene reglas de validez/consistencia |
| Fuente modificada | No; SHA-256 idéntico |

La proporción estimada del 5% fija un umbral que puede señalar datos legítimos incluso en un archivo sin errores. Este ejemplo demuestra aprendizaje multivariado y trazabilidad; **no acredita calidad predictiva en un dominio real**. Cambiar la proporción afecta falsos positivos y omisiones; hay que calibrarla con revisión humana y datos representativos antes de cualquier uso operativo. No se afirma superioridad general de Isolation Forest frente a IQR a partir de este caso construido.

## Límites y pruebas

Se aprende y evalúa en el mismo lote, como detección exploratoria de atípicos; no se presenta como evaluación de generalización sobre datos nuevos. La distinción está explicada en la [guía oficial de detección de anomalías de scikit-learn](https://scikit-learn.org/stable/modules/outlier_detection.html). No existen etiquetas empresariales verificadas, validación productiva, análisis de sesgo, deriva, explicación por variable, corrección automática ni certificación de exactitud.

`tests/test_intelligence.py` verifica las dos combinaciones, reproducibilidad, score intacto, exclusión de claves, nulos/infinitos, índices de registro, datos insuficientes, parámetros inválidos, muestras acotadas y persistencia/exportación/monitor. `tests/test_mvp.py` y `tests/test_cli.py` verifican la integración. El script de evidencia conserva explícitamente los falsos positivos. Los parámetros y versión se registran porque resultados de versiones diferentes de scikit-learn pueden variar.
