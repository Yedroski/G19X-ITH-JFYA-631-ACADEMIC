# Validación del MVP unificado

## Entrega del 29 de octubre de 2026

Windows AMD64, Python 3.11.0, `.venv311`; scikit-learn 1.8.0. Suite final: **96 passed, 1 skipped en 40.50 s**, salida 0. `pip check`: **No broken requirements found**. Se conserva omitida la prueba optativa de SQL Server real: no hay validación contra una instancia configurada en esta sesión.

```powershell
.\.venv311\Scripts\python.exe -m pytest -q
.\.venv311\Scripts\python.exe -m pip check
.\.venv311\Scripts\python.exe scripts/validar_inteligencia.py
.\.venv311\Scripts\python.exe scripts/benchmark.py --intelligent --repeticiones 3 --salida reports/benchmark_inteligente.json
```

- Interfaz única: entrada por defecto y alias `--mvp`, dashboard, ejemplo, formulario de reglas y compatibilidad de importación anterior.
- Monitor integrado: bloquea edición/análisis/consulta concurrentes, conserva el último reporte ante un cambio de esquema, recupera, detiene, reinicia y cierra limpiamente sin cambiar de pestaña.
- Isolation Forest: ambas combinaciones sembradas detectadas sin hallazgos IQR; score y datos intactos; mismo resultado al repetir con semilla/versión fijadas; datos insuficientes, nulos, infinitos, columnas y proporciones inválidas; conteos completos con detalle limitado.
- Flujo completo del modelo: ejemplo de un clic, casilla para desactivar, tabla y parámetros visibles, persistencia SQLite y exportación JSON/CSV, consola y monitoreo; apertura de históricos anteriores sin campo `inteligencia`.
- Regresión: ingesta, API y 16 reglas originales, oráculo manual, persistencia transaccional, fuente sin cambios, errores recuperables y cierre de trabajadores.

Evidencia de detección: [validacion_inteligencia.json](validacion_inteligencia.json). Detectó las filas 401 y 402 y señaló otras 19 con la proporción por defecto del 5%; esas 19 son falsos positivos respecto de las etiquetas sembradas. La interpretación y limitaciones constan en [COMPONENTE_INTELIGENTE.md](COMPONENTE_INTELIGENTE.md).

Revisión visual mediante Qt offscreen con el bucle real `QApplication.exec()`: dashboard, formulario de reglas y detección inteligente. Capturas locales en `reports/validacion_unificada/{dashboard,inteligencia,reglas}.png`, ignoradas por Git. El flujo de ejemplo inteligente completó lectura, entrenamiento y render en 3.52 s en esa ejecución. Esto no acredita interacción con los diálogos nativos ni SQL Server.

### Rendimiento con el componente inteligente

Carga + siete reglas + IQR + Isolation Forest + guardado SQLite, sin generación ni exportación. La primera ejecución incluye la importación inicial de scikit-learn. Evidencia completa: [benchmark_inteligente.json](benchmark_inteligente.json).

| Filas | Tres ejecuciones (s) | Mediana (s) |
|---|---|---|
| 10 000 | 3.4671, 1.5502, 1.5615 | 1.5615 |
| 100 000 | 9.4942, 9.2926, 9.0083 | 9.2926 |

Cumple el objetivo orientativo local de 10 000 filas en menos de 30 s con el modelo activado. No constituye SLA ni predice tiempos de una instancia remota o archivos más anchos.

## Evidencia histórica de la integración del 15 de octubre

Fecha: 15 de octubre de 2026. Equipo local Windows AMD64, Python 3.11.0, entorno aislado `.venv311`. Versiones directas en `requirements-tested.txt`.

## Suite automática

```powershell
.\.venv311\Scripts\python.exe -m pytest -q
```

Resultado final: **58 passed, 1 skipped**, 18.70 s; **código de salida 0**. `pip check`: sin dependencias rotas.

- Ingesta: separadores, IDs con ceros, NA literal, nulos, encabezados, ancho, límites y hash de los bytes leídos.
- Perfil/motor: estadísticas, tipo predominante, API original, las 16 reglas originales sobre el CSV conservado, caso manual QS=63.125, reglas inválidas, duplicados, fechas, anomalías y registros afectados sin doble conteo.
- Persistencia/exportación: round-trip SQLite, rollback y reporte disponible ante caída de BD.
- Monitor: estabilidad, versiones nuevas, deduplicación de contenido, umbral configurable, snapshot de reglas, errores de fuente/esquema, recuperación, archivo bloqueado, cambios durante análisis, memoria acotada y detención.
- Interfaz Qt offscreen: análisis en hilo, tablas/filtros/histórico, monitor en vivo, actualización sin cambiar de pestaña, exclusión de análisis simultáneos, parada, reinicio y cierre limpio. Se corrigió la liberación de ventanas/hilos detectada en Windows durante la validación.
- CLI: análisis batch, monitoreo acotado, exportaciones, falta de persistencia y argumentos inválidos. Las pruebas dejan margen para la resolución del reloj de Windows al comprobar estabilidad.

La prueba omitida es `test_sqlserver_real`: requiere `TEST_SQLSERVER=1` y una instancia real configurada. No se afirma validación de SQL Server ni de los diálogos nativos de Windows a partir de las pruebas Qt offscreen.

## Comprobaciones ejecutables adicionales

| Caso | Resultado |
|---|---|
| CLI demo, 1 000 registros, reglas demo e IQR | score 97.3843; cobertura 100%; guardado y exportado; salida 0 |
| CLI dataset original y 16 reglas originales | score 100; cobertura 100%; guardado y exportado; salida 0 |
| Simulador y CLI monitor como procesos separados | ambos salida 0; 35 sondeos, 3 reportes observados de 2, 3 y 4 registros; alertas ACEPTABLE/REVISAR; ningún hash duplicado |
| Revisión visual del monitor offscreen | captura local `reports/validacion/monitor.png`, con Segoe UI cargada para el render offscreen |
| Historial Git | `c7b5bb2` sigue siendo ancestro; los cinco commits iniciales se conservan |
| Datos/solución originales | sin diferencias respecto a la base para el CSV de empleos y `.slnx` |

El simulador confirma el carácter del sondeo: puede omitir versiones que ocurren antes de la primera observación o entre observaciones. Los reportes y bases de validación están en `reports/` y `data/demo.db`, ignorados por Git; no son datos productivos ni un respaldo SQL Server.

## Rendimiento reproducible

```powershell
.\.venv311\Scripts\python.exe scripts/benchmark.py --repeticiones 3 --salida reports/benchmark.json
```

Se generan CSV sintéticos con siete columnas y se mide carga + análisis con siete reglas e IQR + guardado SQLite. Se excluyen generación, inicio del intérprete y exportación.

| Registros | Tres ejecuciones (s) | Mediana (s) |
|---|---|---|
| 10 000 | 0.7643, 0.7496, 0.7553 | 0.7553 |
| 100 000 | 6.2252, 6.2923, 6.2098 | 6.2252 |

Evidencia legible por máquina: [benchmark.json](benchmark.json). Se cumple el objetivo orientativo de 10 000 filas en menos de 30 s en este equipo. No se extrapola a SQL Server remoto, CSV más anchos ni archivos con reglas más costosas.

El benchmark deja archivos sintéticos y una base aislada en una carpeta nueva de `reports/`; no modifica entradas existentes. La prueba SQL Server opt-in y la aceptación de reglas de negocio siguen pendientes del entorno correspondiente.
