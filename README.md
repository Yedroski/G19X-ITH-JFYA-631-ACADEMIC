# SistemaCalidadDatos

Proyecto académico TODO Academy. Repositorio: [G19X-ITH-JFYA-631-ACADEMIC](https://github.com/Yedroski/G19X-ITH-JFYA-631-ACADEMIC).

Aplicación de escritorio y consola para evaluar CSV con Python, Pandas, PySide6 y SQL Server. Integra las funcionalidades de `SistemaCalidadDatos_Referencia` sobre el historial del proyecto original.

## Inicio en Windows

1. Ejecuta `instalar.bat` con Python 3.11 o 3.12 instalado. Crea `.venv311` y conserva cualquier `.venv` anterior.
2. Abre `iniciar_demo.bat` para usar SQLite local sin configurar un servidor.
3. Selecciona `data/input/demo_clientes.csv`, carga `config/reglas_demo.json` en **Configurar reglas** y pulsa **Analizar**.
4. Revisa Dashboard, Perfilado, Resultado de reglas, Incidencias e Histórico. Puedes exportar JSON y CSV.

Para el dataset original usa `data/input/global_ai_jobs_2026.csv` con `config/reglas_empleos.json`: contiene las 16 reglas que estaban en `main.py`. Las reglas deben coincidir con las columnas del archivo elegido.

```powershell
python -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe main.py --demo
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/global_ai_jobs_2026.csv --rules config/reglas_empleos.json --anomalies
.\.venv311\Scripts\python.exe -m pytest -q
```

La solución `SistemaCalidadDatos.slnx` y su proyecto se conservan. En Visual Studio selecciona `.venv311\Scripts\python.exe` y `main.py` como inicio; usa `--demo` como argumento para trabajar con SQLite.

## Funciones

- Carga CSV con separador/codificación configurables, validación de estructura e identificadores preservados como texto.
- Perfil por columna: tipo predominante, nulos, distintos, ejemplos, frecuencias y estadísticas numéricas.
- Reglas configurables, faltantes, duplicados, consistencia numérica/de fechas y anomalías IQR opcionales.
- Quality Score: 30% completitud, 30% validez, 20% unicidad y 20% consistencia; muestra cobertura cuando faltan dimensiones.
- Recomendaciones, incidencias, historial transaccional y exportación JSON/CSV.
- Compatibilidad con `cargar_csv`, `ejecutar_reglas`, validadores en español y funciones originales de perfilado.
- Monitoreo experimental por sondeo de CSV, con alertas locales, actualización del dashboard y últimos 100 resultados de sesión.

La fuente permanece intacta. El límite es 100 MB y 100 000 registros por CSV; los conteos son completos y el detalle se limita a 2 000 incidencias. IQR señala valores a investigar, sin modificar el score ni corregir datos.

La descarga de Kaggle sigue disponible en `src/ingestion/kaggle_loader.py`; es opcional y requiere instalar `kagglehub` en el entorno. La demo y el CSV original funcionan sin esa descarga.

## SQL Server y documentación

Sigue [SQL_SERVER.md](docs/SQL_SERVER.md), configura tu `.env` sin sobrescribirlo y ejecuta `iniciar_sqlserver.bat`. `--demo` habilita SQLite explícitamente; nunca se usa como sustitución silenciosa de SQL Server.

La consola devuelve 0 si guarda el análisis, 1 por entrada/configuración inválida y 2 si genera el reporte sin persistencia. Opciones: `--keys id,sucursal`, `--sep ";"`, `--encoding cp1252`, `--output reports` y `--init-db`.

## Monitoreo experimental

En la pestaña **Tiempo real · Experimental**, configura intervalo, estabilidad mínima y umbral; pulsa **Iniciar monitoreo**. Usa el CSV y las reglas seleccionados arriba. **Detener** permite cambiar la configuración. Cada versión estable actualiza las métricas y se guarda si hay conexión a la base.

También puedes ejecutarlo por consola:

```powershell
.\.venv311\Scripts\python.exe main.py --demo --csv data/input/stream_demo.csv --rules config/reglas_demo.json --watch --interval 2 --stability 1 --threshold 90
```

En otra terminal, publica datos sintéticos en esa ruta nueva:

```powershell
.\.venv311\Scripts\python.exe scripts/simular_tiempo_real.py --salida data/input/stream_demo.csv --eventos 12 --intervalo 3
```

Ctrl+C detiene la consola. Se trata de monitoreo cercano al tiempo real de archivos locales: cada cambio se analiza como un lote completo; puede omitir versiones intermedias entre sondeos. Consulta [operación y límites](docs/MONITOREO_EXPERIMENTAL.md).

Consulta [PRD actualizado](docs/PRD.md), [arquitectura](docs/ARQUITECTURA.md), [métricas y reglas](docs/METRICAS_Y_REGLAS.md), [integración](docs/INTEGRACION.md), [pruebas](docs/PRUEBAS.md) y la copia del [PRD recibido](docs/PRD_ORIGINAL.txt).
