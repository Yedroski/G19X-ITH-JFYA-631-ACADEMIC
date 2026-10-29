# SistemaCalidadDatos

Proyecto académico TODO Academy. Repositorio: [G19X-ITH-JFYA-631-ACADEMIC](https://github.com/Yedroski/G19X-ITH-JFYA-631-ACADEMIC).

Aplicación de escritorio y consola para evaluar CSV con Python, Pandas, PySide6 y SQL Server. El componente inteligente usa **Isolation Forest de scikit-learn** para aprender patrones multivariados del archivo e identificar registros atípicos para revisión humana. IQR y las reglas de calidad siguen disponibles por separado.

## Inicio en Windows

1. Ejecuta `instalar.bat` con Python 3.11 o 3.12 instalado. Crea `.venv311` y conserva cualquier `.venv` anterior.
2. Abre **`iniciar_mvp.bat`**, el acceso principal a la versión definitiva, con histórico SQLite local. `iniciar_demo.bat` redirige a esa misma aplicación; ya no hay dos interfaces.
3. Pulsa **Probar con datos de ejemplo** para analizar clientes con siete reglas, o **Probar detección inteligente** para demostrar combinaciones atípicas que IQR no señala.
4. Para un CSV propio: **Datos → Elegir CSV → Reglas**. Crea reglas mediante el formulario (obligatorio, único, rango, catálogo, correo, fechas o comparaciones); también puedes importar/exportar JSON.
5. En **Reglas**, activa **Anomalías IQR** y/o **Detección inteligente · Isolation Forest**, revisa las columnas y la proporción estimada de atípicos. Pulsa **Analizar y ver resultados**.
6. Consulta el dashboard, perfilado, reglas, incidencias y **Detección inteligente** dentro de Resultados. Exporta JSON/CSV y recupera reportes desde Histórico. **Tiempo real · Experimental** usa la misma configuración.

Si ya tienes el entorno instalado, actualiza las dependencias antes de iniciar: `.\.venv311\Scripts\python.exe -m pip install -r requirements.txt`.

Para el dataset original usa `data/input/global_ai_jobs_2026.csv` con `config/reglas_empleos.json`: contiene las 16 reglas que estaban en `main.py`. Las reglas deben coincidir con las columnas del archivo elegido.

```powershell
python -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe main.py --demo
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/global_ai_jobs_2026.csv --rules config/reglas_empleos.json --anomalies
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/demo_inteligente.csv --anomalies --intelligent --anomaly-columns unidades,importe
.\.venv311\Scripts\python.exe scripts/validar_inteligencia.py
.\.venv311\Scripts\python.exe -m pytest -q
```

La solución `SistemaCalidadDatos.slnx` y su proyecto se conservan. En Visual Studio selecciona `.venv311\Scripts\python.exe` y `main.py` como inicio; usa `--demo` como argumento para trabajar con SQLite.

## Funciones

- Carga CSV con separador/codificación configurables, validación de estructura e identificadores preservados como texto.
- Perfil por columna: tipo predominante, nulos, distintos, ejemplos, frecuencias y estadísticas numéricas.
- Reglas configurables, faltantes, duplicados, consistencia numérica/de fechas y anomalías IQR opcionales.
- Aprendizaje no supervisado multivariado con Isolation Forest: selección de variables, umbral configurable, puntuaciones y parámetros trazables en pantalla, histórico y exportación.
- Quality Score: 30% completitud, 30% validez, 20% unicidad y 20% consistencia; muestra cobertura cuando faltan dimensiones.
- Recomendaciones, incidencias, historial transaccional y exportación JSON/CSV.
- Compatibilidad con `cargar_csv`, `ejecutar_reglas`, validadores en español y funciones originales de perfilado.
- Monitoreo experimental por sondeo de CSV, con alertas locales, actualización del dashboard y últimos 100 resultados de sesión.

La fuente permanece intacta. El límite es 100 MB y 100 000 registros por CSV; los conteos son completos y cada tabla de detalle se limita a 2 000 hallazgos. IQR e Isolation Forest señalan valores a investigar, sin modificar el score ni corregir datos. El modelo necesita dos columnas numéricas variables y 20 filas completas. La proporción de atípicos (5% por defecto) puede generar falsos positivos; no representa una probabilidad de error. Consulta la [demostración, evidencia y límites del componente inteligente](docs/COMPONENTE_INTELIGENTE.md).

La descarga de Kaggle sigue disponible en `src/ingestion/kaggle_loader.py`; es opcional y requiere instalar `kagglehub` en el entorno. La demo y el CSV original funcionan sin esa descarga.

## SQL Server y documentación

Sigue [SQL_SERVER.md](docs/SQL_SERVER.md), configura tu `.env` sin sobrescribirlo y ejecuta `iniciar_sqlserver.bat`. `--demo` habilita SQLite explícitamente; nunca se usa como sustitución silenciosa de SQL Server.

La consola devuelve 0 si guarda el análisis, 1 por entrada/configuración inválida y 2 si genera el reporte sin persistencia. Opciones: `--keys id,sucursal`, `--sep ";"`, `--encoding cp1252`, `--output reports` y `--init-db`.

## Monitoreo experimental

En la pestaña **Tiempo real · Experimental**, configura intervalo, estabilidad mínima y umbral; pulsa **Iniciar monitoreo**. Usa el CSV cargado en Datos y la configuración de Reglas, incluidos IQR e Isolation Forest. **Detener** permite cambiar la configuración y exportar. Cada versión estable actualiza las métricas y se guarda si hay conexión a la base. Después de cambios en el CSV, vuelve a cargarlo antes de analizar manualmente.

También puedes ejecutarlo por consola:

```powershell
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/stream_demo.csv --rules config/reglas_demo.json --watch --interval 2 --stability 1 --threshold 90
```

En otra terminal, publica datos sintéticos en esa ruta nueva:

```powershell
.\.venv311\Scripts\python.exe scripts/simular_tiempo_real.py --salida data/input/stream_demo.csv --eventos 12 --intervalo 3
```

Ctrl+C detiene la consola. Se trata de monitoreo cercano al tiempo real de archivos locales: cada cambio se analiza como un lote completo; puede omitir versiones intermedias entre sondeos. Consulta [operación y límites](docs/MONITOREO_EXPERIMENTAL.md).

## Procedencia, autoría y asistencia de IA

El proyecto original corresponde a José Amaya (cuenta GitHub **Yedroski**, autor registrado como `jose amaya` en Git). Los commits `80c4237`, `8c00514`, `7e5fe2e`, `ccbf147` y `c7b5bb2`, del 2 y 3 de octubre de 2026, documentan configuración del proyecto, ingesta CSV, perfilado y reglas. Se conservan ese historial, la solución Visual Studio, el CSV original y la compatibilidad de sus funciones. Esta atribución se basa en el historial; no implica que todo el código posterior haya sido escrito manualmente por el alumno.

`SistemaCalidadDatos_Referencia` es un prototipo de referencia distribuido como ZIP y extraído en `../SistemaCalidadDatos_Referencia/SistemaCalidadDatos_Referencia`, separado del proyecto original y sin repositorio Git. Su README lo describe como una implementación de referencia para comparar y adaptar. De allí se incorporaron ingesta robusta, motor de métricas, reglas declarativas, IQR, recomendaciones, servicio, exportación, interfaz, repositorio SQL Server/SQLite y pruebas. **El material local no acredita el autor ni el proveedor del ZIP; queda pendiente su confirmación por el alumno. No se presenta esa referencia como desarrollo original propio.**

**Se utilizó OpenAI Codex en los commits del 15 de octubre de 2026**: `d34bf9c` (integración y compatibilidad), `20b3636` (monitoreo experimental), `d5ac217` (PRD y validación) y `3e9c992` (integración con el repositorio académico). Git los registra como `CodexSandboxOffline`. También se utilizó Codex para conservar el avance local del MVP y realizar esta unificación, el módulo Isolation Forest, las pruebas y la documentación del 29 de octubre. Las decisiones de requisitos corresponden al alumno; los cambios asistidos por IA quedan identificados en los commits y sujetos a su revisión y defensa académica.

Consulta [alcance y demostración del MVP](docs/MVP.md), [PRD actualizado](docs/PRD.md), [arquitectura](docs/ARQUITECTURA.md), [métricas y reglas](docs/METRICAS_Y_REGLAS.md), [integración](docs/INTEGRACION.md), [pruebas](docs/PRUEBAS.md) y la copia del [PRD recibido](docs/PRD_ORIGINAL.txt).
