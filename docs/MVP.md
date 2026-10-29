# MVP entregable — Sistema Inteligente de Calidad de Datos

Versión de alcance: 29 de octubre de 2026. Prototipo académico local de escritorio y consola. Entrada principal: `iniciar_mvp.bat`; `iniciar_demo.bat` es un alias de la misma aplicación. `iniciar_sqlserver.bat` abre esa interfaz con SQL Server.

## Qué entra y cómo se demuestra

| Entrega | Demostración y aceptación | Evidencia |
|---|---|---|
| CSV genérico y vista previa | Datos → Elegir CSV; conserva `001`, permite separador/codificación y rechaza estructura inválida. No modifica la fuente. | `test_core.py`, `test_mvp.py`; SHA-256 |
| Dashboard del MVP | Probar con datos de ejemplo: 1 000 filas, siete reglas, score 97.3843, cobertura 100%, barras y acciones. | `test_demo_un_clic_exporta_y_recupera_historial` |
| Reglas intuitivas | Formulario para obligatorio, único, rango, catálogo, correo, fecha, regex y comparación; cargar/guardar JSON sigue disponible. | `test_formulario_produce_reglas_ejecutables_y_valida_antes_de_agregar` |
| Métricas verificables | Completitud, validez, unicidad y consistencia; N/D y cobertura cuando faltan dimensiones. Caso manual score 63.125. | `test_core.py` |
| Anomalías IQR | Casilla independiente en Reglas; valores extremos, sin afectar el score. | `test_core.py`, `test_intelligence.py` |
| Componente inteligente | Probar detección inteligente → Resultados → Detección inteligente. Isolation Forest detecta combinaciones 401 y 402 del ejemplo, registra parámetros y puntuaciones. | `scripts/validar_inteligencia.py`, `docs/validacion_inteligencia.json` |
| Control del modelo | Revisar columnas y proporción estimada; mínimo dos variables y 20 filas completas. Datos insuficientes muestran motivo. | `test_intelligence.py`, `test_mvp.py` |
| Incidencias e histórico | Filtrar, abrir una ejecución guardada y recuperar reglas, métricas y modelo. Datos de referencia y archivos fuente intactos. | SQLite transaccional, `test_core.py`, `test_intelligence.py` |
| Exportación | JSON completo, CSV de perfil/reglas/incidencias y tabla de anomalías inteligentes con registro, valores y puntuaciones. | `test_servicio_exportacion_historico_y_monitor_conservan_evidencia` |
| Monitoreo experimental | Tiempo real → iniciar; cada cambio estable actualiza dashboard y alertas locales. Detener, reiniciar y cerrar sin solapar análisis. | `test_monitoring.py`, `test_gui.py`, `test_cli.py` |
| Compatibilidad | Dataset de empleos, 16 reglas originales, API en español y consola continúan funcionando. | `test_compatibility.py` |

Las rutas de las pruebas son relativas a `tests/`. El resultado completo y las restricciones de validación se registran en [PRUEBAS.md](PRUEBAS.md).

## Qué queda fuera

- Ingesta de Excel, APIs, bases operativas o flujos distribuidos; la entrada es CSV local.
- Certificar exactitud factual, corregir/eliminar registros automáticamente o aprobar reglas de negocio sin un responsable.
- Modelos supervisados, LLM, sugerencia automática de reglas, entrenamiento incremental, detección de deriva o un modelo productivo persistente. Se eligió **Isolation Forest** como componente inteligente acotado.
- Garantizar que todos los atípicos sean errores: con la proporción por defecto se señalan también registros legítimos. El caso sintético no acredita precisión productiva.
- Usuarios/roles, SSO, servicio web, notificaciones externas, SLA, streaming real, capturar todas las escrituras y retención automática.
- Ejecutable empaquetado y despliegue corporativo. Se entrega fuente Python; SQL Server necesita una instancia configurada y su prueba optativa.

## Guion de exposición (8–10 minutos)

1. Instalar dependencias con `instalar.bat` y abrir `iniciar_mvp.bat`. Mostrar que el acceso demo lleva al mismo producto.
2. Pulsar **Probar con datos de ejemplo**. Explicar score, cobertura y diferencias entre faltantes, reglas y anomalías. Crear una regla visual, analizar y mostrar su resultado.
3. Pulsar **Probar detección inteligente**. Mostrar los dos grupos sintéticos: unidades cerca de 30 con importe cerca de 60, y unidades cerca de 70 con importe cerca de 140. Los registros 401 y 402 cruzan las combinaciones.
4. En **Resultados → Detección inteligente**, localizar ambos registros, columnas, puntuación, decisión, semilla y proporción. IQR no encontró extremos. Con 5% se señalan 21 filas: dos sembradas y 19 falsos positivos respecto de esas etiquetas. No llamar a ese resultado «100% de precisión».
5. Desactivar Isolation Forest y repetir: score 100 y cobertura 50% en ese ejemplo sin reglas, aunque desaparezcan sus hallazgos. El modelo complementa la revisión; no certifica el score.
6. Exportar y recuperar el reporte desde Histórico. Mostrar el JSON con parámetros y `anomalias_inteligentes.csv`.
7. Demostrar el monitor con el simulador y una ruta nueva, siguiendo [MONITOREO_EXPERIMENTAL.md](MONITOREO_EXPERIMENTAL.md). Para GUI, cargar el archivo una vez que el simulador haya creado su primer snapshot. Detener permite volver a editar y exportar.
8. Mostrar pruebas, R-09 actualizada y atribución de referencia/Codex del README. Explicar qué se construyó antes de la integración y qué se incorporó con asistencia.

## Reproducción sin interfaz

```powershell
.\.venv311\Scripts\python.exe scripts/validar_inteligencia.py
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/demo_inteligente.csv --intelligent --anomalies --anomaly-columns unidades,importe
.\.venv311\Scripts\python.exe -m pytest -q
```

Límites: 100 MB/100 000 filas, 2 000 detalles por tabla, histórico de últimas 500 ejecuciones y 100 versiones de monitor en memoria. SQL Server no se da por validado mediante SQLite. La autoría/proveedor del ZIP de referencia requiere confirmación del alumno: está identificada como pendiente, sin adjudicarla a una persona sin evidencia.
