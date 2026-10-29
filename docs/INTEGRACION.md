# Integración sobre el proyecto original

Base: commit `c7b5bb2` en `master`, precedido por `ccbf147`, `7e5fe2e`, `8c00514` y `80c4237`. Los nuevos commits son descendientes de esa base; no se reemplaza `.git` ni se reescribe su historial. La referencia se encontró en `../SistemaCalidadDatos_Referencia/SistemaCalidadDatos_Referencia`, sin repositorio Git.

Se incorporaron ingesta robusta, motor de métricas, reglas declarativas, IQR, recomendaciones, servicio, exportaciones, interfaz PySide6, repositorio SQL Server/SQLite demo, SQL, generador sintético y pruebas. No se importaron la base demo ya poblada, cachés, capturas, manifiestos ni resultados de rendimiento ajenos al equipo actual.

Se conservan el CSV original, la solución `.slnx`, el GUID del proyecto Visual Studio, `.env` y el entorno `.venv`. Las 16 reglas originales se trasladaron a `config/reglas_empleos.json`. La API en español sigue disponible y las reglas originales se normalizan antes de usar el motor común. `fecha_anterior` conserva la comparación inclusiva `<=` y usa ISO `%Y-%m-%d` por defecto; puede configurarse `formato`.

Los valores numéricos/fechas no convertibles ahora fallan sus reglas en vez de pasar silenciosamente. Los nulos se omiten excepto en reglas obligatorias. El porcentaje de la API original conserva su denominador de filas totales; los reportes del motor distinguen evaluaciones y omisiones. `cargar_csv` devuelve columnas como texto para conservar ceros iniciales; las funciones de perfilado y reglas realizan conversiones temporales.

Se sustituyeron archivos vacíos con nombres `init.py`, `-init-.py` y `--init--.py` por paquetes `__init__.py`. `requiremetns.txt` permanece como alias de `requirements.txt`. El proyecto de Visual Studio incluye los módulos, pruebas y scripts nuevos.

Cambios locales preexistentes en `.vs`: `.suo`, `DocumentLayout.json` y `SemanticSymbols.db`. No se incluyeron en los commits de integración ni se modificaron deliberadamente. Siguen apareciendo en `git status` porque ya estaban versionados antes de esta integración, aunque `.vs/` figura en `.gitignore`.

El PRD recibido se conserva íntegro en `docs/PRD_ORIGINAL.txt`. Las decisiones de alcance y el módulo experimental se documentan en el PRD actualizado, sin presentar monitoreo por sondeo como una plataforma de streaming distribuido.

## Unificación del 29 de octubre de 2026

Se guardó primero el avance local de dashboard/formulario/ejemplo del MVP en `51fa99e` y se subió a `origin/main`. Ese punto inicial tenía una prueba fallida por buscar «correo» cuando la columna era `email`; se corrigió en la unificación. Los archivos personales `.vs` no forman parte de estos cambios.

La única ventana vigente es `dashboard/mvp.py`; `dashboard/app.py` reexporta esa ventana para importaciones anteriores. `iniciar_mvp.bat` es el acceso principal e `iniciar_demo.bat` lo invoca. Ambos conservan SQLite explícita, mientras que SQL Server usa la misma interfaz con su configuración propia. El monitoreo se trasladó a esta ventana junto con IQR.

Se añadió `anomalies/isolation_forest.py` con aprendizaje multivariado, configuración, trazabilidad y prueba sintética; no procede de la referencia. Se integró en motor, servicio, CLI, monitor, GUI, histórico y exportación. El README distingue historial original, referencia externa y asistencia de Codex, incluida la del 15 de octubre y esta entrega. El autor/proveedor del ZIP no consta en el material local y requiere confirmación del alumno; no se atribuye sin evidencia.
