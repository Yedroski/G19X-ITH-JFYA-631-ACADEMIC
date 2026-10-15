# PRD — Sistema Inteligente de Calidad de Datos

Revisión de integración: 15 de octubre de 2026. Fuente: `PRD.txt` recibido en la carpeta de trabajo, conservado íntegramente en `docs/PRD_ORIGINAL.txt`. Este documento es la versión vigente y versionada; el archivo `PRD.txt` junto a las dos carpetas de proyectos contiene una copia de esta revisión.

## Propósito y usuarios

Permitir que analistas y responsables de calidad inspeccionen datos tabulares, identifiquen problemas verificables y conserven evidencia para corregirlos en la fuente. Calidad significa adecuación al uso: completitud, validez, unicidad y consistencia medibles. La exactitud factual, fiabilidad de la fuente e integridad entre sistemas necesitan contexto y referencias externas; no se deben inferir del score.

No se dispone de reglas empresariales validadas, propietarios ni fuentes operativas definidas. Se utilizan datos sintéticos y un CSV de empleos ya incluido en el proyecto. Las reglas de ejemplo son demostrativas. El responsable de negocio debe aprobar catálogos, formatos, rangos, claves y umbrales antes de uso operativo.

## Alcance y flujo

CSV → lectura de snapshot → perfilado → motor de reglas → anomalías opcionales → dimensiones y Quality Score → incidencias/recomendaciones → dashboard, histórico y exportaciones.

El flujo principal sigue siendo batch bajo demanda. Se añade una opción experimental de monitoreo cercano al tiempo real mediante sondeo de un CSV local. Cada versión estable se procesa como un lote completo. Esta extensión reemplaza la exclusión absoluta de tiempo real de la restricción R-04 del PRD original.

## Requerimientos funcionales

| ID | Requerimiento y aceptación | Implementación |
|---|---|---|
| RF-01 | Cargar un archivo CSV genérico, sin exigir un ID específico. | GUI/CLI, `ingestion` |
| RF-02 | Validar extensión, codificación, encabezados, ancho, vacíos y límites. | `cargar_snapshot` |
| RF-03 | Mostrar filas y columnas del dataset. | Perfil/dashboard |
| RF-04 | Inferir tipo predominante por columna sin alterar sus valores. | Numérico, fecha ISO, booleano, texto o sin datos |
| RF-05 | Calcular cantidad y porcentaje de nulos por columna. | Perfilado |
| RF-06 | Calcular valores distintos por columna. | Perfilado |
| RF-07 | Detectar duplicados de filas completas o claves seleccionadas. | Motor; excedentes para unicidad |
| RF-08 | Mostrar mínimo, máximo, media, desviación, mediana y cuartiles numéricos. | Perfil; solo valores convertibles finitos |
| RF-09 | Mostrar hasta cinco ejemplos y valores más frecuentes. | Perfilado |
| RF-10 | Configurar reglas y guardarlas/cargarlas en JSON. | Editor, formato español y canónico |
| RF-11 | Validar configuración y evaluar las reglas seleccionadas. | Motor común |
| RF-12 | Identificar registros que incumplen cada regla. | Conteos completos y muestra acotada |
| RF-13 | Detectar anomalías numéricas exploratorias mediante IQR opcional. | `anomalies` |
| RF-14 | Calcular Quality Score y cobertura de dimensiones evaluadas. | `quality/engine.py` |
| RF-15 | Mostrar resultados en dashboard de escritorio. | PySide6 |
| RF-16 | Resumir problemas, registros afectados y reglas incumplidas. | KPIs y tablas |
| RF-17 | Generar recomendaciones por clase de hallazgo. | `remediation` |
| RF-18 | Consultar y filtrar detalles de incidencias. | GUI; hasta 2 000 detalles por ejecución |
| RF-19 | Guardar y recuperar ejecuciones, métricas y reglas. | SQL Server; SQLite demo explícita |
| RF-20 | Exportar JSON completo y tablas CSV. | `exporter` |
| RF-21 | Iniciar/detener monitoreo experimental de un CSV. | GUI/CLI; intervalo y estabilidad configurables |
| RF-22 | Actualizar dashboard y alertar localmente ante score bajo el umbral. | Monitor; umbral configurable 0–100 |
| RF-23 | Reintentar cambios inestables/errores de fuente y conservar el último resultado válido. | Monitor y pruebas de recuperación |
| RF-24 | Registrar metadatos del monitoreo e histórico de versiones. | Payload persistido y últimas 100 versiones de sesión |

## Métricas y decisiones de cálculo

| Dimensión | Fórmula |
|---|---|
| Completitud C | `100 × (1 − celdas faltantes / celdas totales)` |
| Unicidad U | `100 × (1 − duplicados excedentes / filas)` |
| Validez V | `100 × (1 − fallos de reglas de validez / evaluaciones elegibles)` |
| Consistencia I | `100 × (1 − fallos de reglas de consistencia / evaluaciones elegibles)` |
| Quality Score | `0.30 C + 0.30 V + 0.20 U + 0.20 I`, cuando todas están disponibles |

La completitud global considera todas las celdas; los campos obligatorios se definen además mediante reglas. En validez/consistencia la unidad es una evaluación de regla, por lo que una fila puede tener varias evaluaciones. Esta decisión precisa los denominadores propuestos de forma genérica en el PRD original.

Si una dimensión no tiene evaluaciones, se muestra N/D y se renormalizan los pesos disponibles. Se muestra cobertura: suma de pesos evaluados en porcentaje. Las anomalías no afectan el score. Umbral orientativo por defecto: score menor a 90; el monitor permite cambiarlo. Los registros con hallazgos se cuentan sin duplicar filas e incluyen anomalías exploratorias si se activaron.

Vacíos y espacios son nulos; `NA`/`NULL` se conservan como texto. Los identificadores mantienen ceros iniciales. Salvo `required`, las reglas omiten nulos; valores presentes pero no convertibles fallan las reglas numéricas/de fecha. La unicidad global cuenta excedentes; `unique` marca todos los miembros no nulos de cada grupo repetido. El tipo predominante requiere mayoría estricta (>50% de valores no nulos); la inferencia no sustituye reglas de negocio.

KPIs: filas, columnas, faltantes, duplicados, reglas ejecutadas/incumplidas, registros con hallazgos y su porcentaje, anomalías y duración del motor. Los detalles de incidencias pueden estar muestreados, los conteos y KPIs no.

## Requerimientos no funcionales

La sección original repetía los RF; se sustituye por requisitos verificables:

| ID | Requisito | Validación |
|---|---|---|
| RNF-01 | Interfaz receptiva durante lectura/análisis/guardado. | Trabajadores Qt; las consultas manuales de histórico pueden esperar a la BD |
| RNF-02 | No modificar los CSV originales. | Snapshot de lectura, pruebas de hash; simulador separado |
| RNF-03 | Guardado atómico de una ejecución. | Transacción y prueba de rollback |
| RNF-04 | Uso acotado de entrada/detalle/sesión. | 100 MB, 100 000 filas, 2 000 incidencias, 100 resúmenes de sesión |
| RNF-05 | Trazabilidad reproducible. | UUID, UTC, SHA-256, reglas y opciones por ejecución |
| RNF-06 | Errores y falta de persistencia visibles. | GUI/CLI y pruebas de fallos |
| RNF-07 | Cierre seguro y ausencia de análisis solapados. | Event/QThread, pruebas de parada y reinicio |
| RNF-08 | Instalación reproducible y fuentes editables. | Python 3.11/3.12, requirements, scripts, solución Visual Studio |
| RNF-09 | Objetivo orientativo de 10 000 registros en menos de 30 s. | Medición local documentada; sin SLA universal |
| RNF-10 | Configuración SQL fuera del repositorio. | `.env` ignorado; `.env.example` sin credenciales |

## Restricciones vigentes

- R-02/R-08: evaluación básica verificable; sin certificación automática de exactitud factual.
- R-03/R-15: datos tabulares CSV; SQL Server es repositorio de resultados, no conector de ingesta.
- R-04 revisada: batch estable más monitoreo experimental optativo por sondeo local; sin streaming distribuido ni garantía de capturar cada escritura.
- R-05/R-06: hasta 100 000 filas y 100 MB por snapshot; un equipo, archivo completo en memoria y capacidad dependiente del hardware.
- R-07/R-16: reglas limitadas configuradas por responsables; regex confiables, sin timeout individual.
- R-09: anomalías IQR, sin entrenamiento ni modelos avanzados de IA. El nombre del proyecto no implica IA implementada.
- R-10: recomendaciones; sin corrección automática ni escritura sobre la fuente.
- R-11/R-12/R-13: escritorio local para pocos usuarios, sin SSO/MFA, servicio web ni roles corporativos.
- R-14: histórico básico implementado; lista de últimas 500 ejecuciones. Sin retención automática, migraciones ni sincronización offline. Reiniciar el monitor inicia una sesión nueva.
- No hay notificaciones externas, SLA, procesamiento incremental ni agentes permanentes. El productor debe publicar snapshots atómicos si necesita evitar lecturas de escrituras pausadas.

## Arquitectura y stack

Presentación PySide6/CLI → servicios de análisis/monitoreo → ingesta, perfilado, reglas, IQR y recomendaciones → repositorio SQLAlchemy/pyodbc y SQL Server. SQLite solo en modo `--demo`. Pruebas con pytest y QtTest. Versionado Git conservando el historial original.

Se usan Pandas/NumPy, configuración JSON/python-dotenv y barras Qt nativas. No se añaden Matplotlib, Pydantic, scikit-learn o PyInstaller mientras no aporten una necesidad concreta al prototipo. El entregable es código ejecutable desde Python con la solución Visual Studio existente.

## Aceptación

1. La demo CSV permite cargar, configurar, analizar, consultar, guardar y exportar.
2. El dataset y las 16 reglas originales siguen funcionando con la API previa y el motor integrado.
3. El caso manual de métricas conserva score 63.125 y cobertura 100%.
4. Un CSV actualizado produce un nuevo reporte; contenido sin cambios no duplica ejecuciones en una sesión.
5. Archivos incompletos, ausentes, bloqueados o con esquema cambiado muestran error recuperable y preservan el último reporte.
6. Detener/reiniciar/cerrar el monitor termina limpiamente; GUI y CLI usan el mismo motor.
7. Se registra evidencia local de pruebas y rendimiento; la integración real SQL Server requiere una instancia configurada y se distingue de la demo.
