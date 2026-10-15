# Integración sobre el proyecto original

Base: commit `c7b5bb2` en `master`, precedido por `ccbf147`, `7e5fe2e`, `8c00514` y `80c4237`. Los nuevos commits son descendientes de esa base; no se reemplaza `.git` ni se reescribe su historial. La referencia se encontró en `../SistemaCalidadDatos_Referencia/SistemaCalidadDatos_Referencia`, sin repositorio Git.

Se incorporaron ingesta robusta, motor de métricas, reglas declarativas, IQR, recomendaciones, servicio, exportaciones, interfaz PySide6, repositorio SQL Server/SQLite demo, SQL, generador sintético y pruebas. No se importaron la base demo ya poblada, cachés, capturas, manifiestos ni resultados de rendimiento ajenos al equipo actual.

Se conservan el CSV original, la solución `.slnx`, el GUID del proyecto Visual Studio, `.env` y el entorno `.venv`. Las 16 reglas originales se trasladaron a `config/reglas_empleos.json`. La API en español sigue disponible y las reglas originales se normalizan antes de usar el motor común. `fecha_anterior` conserva la comparación inclusiva `<=` y usa ISO `%Y-%m-%d` por defecto; puede configurarse `formato`.

Los valores numéricos/fechas no convertibles ahora fallan sus reglas en vez de pasar silenciosamente. Los nulos se omiten excepto en reglas obligatorias. El porcentaje de la API original conserva su denominador de filas totales; los reportes del motor distinguen evaluaciones y omisiones. `cargar_csv` devuelve columnas como texto para conservar ceros iniciales; las funciones de perfilado y reglas realizan conversiones temporales.

Se sustituyeron archivos vacíos con nombres `init.py`, `-init-.py` y `--init--.py` por paquetes `__init__.py`. `requiremetns.txt` permanece como alias de `requirements.txt`. El proyecto de Visual Studio incluye los módulos, pruebas y scripts nuevos.

Cambios locales preexistentes en `.vs`: `.suo`, `DocumentLayout.json` y `SemanticSymbols.db`. No se incluyeron en los commits de integración ni se modificaron deliberadamente. Siguen apareciendo en `git status` porque ya estaban versionados antes de esta integración, aunque `.vs/` figura en `.gitignore`.

El PRD recibido se conserva íntegro en `docs/PRD_ORIGINAL.txt`. Las decisiones de alcance y el módulo experimental se documentan en el PRD actualizado, sin presentar monitoreo por sondeo como una plataforma de streaming distribuido.
