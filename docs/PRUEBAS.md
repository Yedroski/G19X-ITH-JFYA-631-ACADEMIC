# Validación de la integración

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
