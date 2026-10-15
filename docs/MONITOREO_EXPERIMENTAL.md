# Monitoreo experimental de datos en tiempo real

El módulo observa un archivo CSV local y analiza sus versiones estables. Reutiliza el mismo perfilado, reglas, score, recomendaciones y persistencia que el análisis manual. Es una ampliación experimental del MVP batch, solicitada durante la integración.

## Interfaz

1. Selecciona un CSV y configura sus reglas, claves, codificación y anomalías.
2. Abre **Tiempo real · Experimental**.
3. Configura **Consultar cada** (2 s por defecto), **Estabilidad mínima** (1 s) y **Alertar bajo** (90/100).
4. Pulsa **Iniciar monitoreo**. Se muestra la última observación, errores de lectura y una tabla con las últimas 100 versiones de la sesión. Dashboard y tablas se actualizan con cada reporte.
5. Pulsa **Detener** para editar las opciones. Cerrar la ventana solicita detener el monitor y espera a que el análisis activo termine; no destruye un hilo en ejecución.

Las opciones y reglas se copian al inicio de cada sesión. No se permite ejecutar análisis manual y monitoreo simultáneamente en la misma ventana. El histórico se actualiza al detener o al pulsar su botón; no se consulta SQL Server desde la interfaz en cada sondeo. Los resultados se pueden exportar desde Dashboard. El indicador de cobertura acompaña al score: un 100 con cobertura parcial no confirma todas las dimensiones.

## Consola y simulación

```powershell
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/stream_demo.csv --rules config/reglas_demo.json --watch --interval 2 --stability 1 --threshold 90
```

El archivo puede aparecer después de iniciar el monitor. En otra terminal:

```powershell
.\.venv311\Scripts\python.exe scripts/simular_tiempo_real.py --salida data/input/stream_demo.csv --eventos 12 --intervalo 3
```

El simulador exige una ruta nueva, publica cada snapshot mediante reemplazo atómico e introduce errores controlados cada tres registros. Para repetirlo elige otra ruta; no necesita modificar el dataset original.

La CLI imprime eventos JSON (`esperando`, `sin_cambios`, `analizado`, `error`) y exporta cada resultado nuevo en `reports/<id>/`. `--max-polls N` limita el número de observaciones, incluyendo las esperas; no es un número de análisis. Códigos: 0 si hubo análisis y todos se guardaron; 1 si no hubo análisis o terminó con error de entrada; 2 si hubo reportes sin persistencia. Ctrl+C conserva las exportaciones ya realizadas. La GUI solo exporta cuando lo solicita el usuario.

## Lectura, reintentos y límites

- El monitor compara identidad, tamaño y marcas de tiempo. Deben permanecer iguales durante la estabilidad mínima; después lee un snapshot de bytes y calcula SHA-256 sobre esos mismos bytes.
- Si cambió durante lectura/análisis, descarta ese intento y espera estabilidad nuevamente. Reintenta archivos ausentes, bloqueados, vacíos, truncados o con esquema incompatible sin perder el último reporte válido.
- Si cambian las marcas de tiempo pero el contenido es idéntico al último análisis, no crea otra ejecución. La deduplicación es por sesión; reiniciar vuelve a analizar la versión inicial. Restaurar un contenido anterior después de otra versión sí representa un cambio.
- Un sondeo se realiza después de terminar el anterior: no hay análisis concurrentes ni cola ilimitada. El archivo completo tiene un límite de 100 MB y 100 000 registros; las incidencias detalladas se limitan a 2 000.
- Solo se conservan el último reporte y 100 resúmenes en memoria. Los reportes almacenados/exportados crecen con las versiones: la retención de BD y disco debe administrarse aparte.
- Un fallo de guardado se muestra y no impide consultar/exportar el resultado. No hay cola de reenvío a la BD: tras recuperar la conexión, reinicia el monitor o ejecuta un análisis manual de esa versión.
- El sondeo no garantiza observar cada escritura ni un tiempo máximo de respuesta. Una pausa del productor superior al período de estabilidad podría parecer un archivo completo: para evitarlo, el productor debe escribir en un temporal y reemplazar el CSV atómicamente, como el simulador.
- La detección depende de las marcas del sistema de archivos; no cubre cambios que preserven deliberadamente identidad, tamaño y todas las marcas. Las validaciones y conversiones son locales; no hay Kafka, conexiones a APIs, captura de cambios SQL, alertas externas ni servicio permanente en segundo plano.

Para consistencia entre lotes y monitoreo, utiliza las mismas reglas, claves y opciones. El umbral del monitor queda registrado en `monitoreo` dentro de cada reporte y se persiste sin cambios de esquema SQL.
