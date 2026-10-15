# Arquitectura y decisiones

Capas: presentación (`dashboard`) → servicio (`service.py`) → dominio (`profiling`, `quality`, `anomalies`, `remediation`) → persistencia (`database`). El cargador y el exportador son adaptadores de entrada/salida. La interfaz no contiene fórmulas de calidad.

El trabajador QThread carga, analiza y guarda; entrega el reporte por señales. Solo el hilo principal actualiza widgets. Se impide cerrar la ventana durante un análisis manual. El monitor experimental usa otro QThread secuencial y un Event para detener la espera: al cerrar, termina el análisis activo antes de liberar la ventana. Ambos modos se excluyen en la misma ventana. Los trabajadores pertenecen a la ventana y se liberan al reemplazarlos o destruirla. El histórico se consulta manualmente en el hilo de interfaz y al terminar una sesión; puede demorar si SQL Server remoto responde lentamente.

SQLAlchemy representa el mismo esquema para SQL Server principal y SQLite demo. El script `sql/02_tablas.sql` proviene de la referencia y usa el dialecto mssql. Cada ejecución tiene UUID, fecha UTC, SHA-256 de los bytes analizados, reglas, opciones, métricas, resúmenes y muestras. Los metadatos de monitoreo se guardan dentro del payload existente. No se ejecuta SQL construido a partir del CSV.

`monitoring/monitor.py` contiene la lógica de sondeo sin depender de Qt. Observa cambios de identidad/tamaño/marcas de tiempo, espera estabilidad, toma un snapshot, comprueba que la fuente no cambió durante el análisis y deduplica por hash. CLI y `dashboard/monitor.py` consumen los mismos eventos. La sesión conserva el último reporte y hasta 100 resúmenes; no hay cola de ingesta ni recuperación de versiones intermedias. Detalles en [MONITOREO_EXPERIMENTAL.md](MONITOREO_EXPERIMENTAL.md).

## Stack efectivamente usado

| Componente | Elección |
|---|---|
| Lenguaje | Python 3.11/3.12; integración validada con 3.11 en Windows |
| Escritorio | PySide6 |
| Datos | Pandas / NumPy (dependencia de Pandas) |
| BD principal | SQL Server |
| Acceso BD | SQLAlchemy 2.x + pyodbc |
| Configuración | python-dotenv y JSON |
| Pruebas | pytest y QtTest |
| Demo local | SQLite, solo con --demo |
| Gráficos | Barras Qt nativas |

No se añadieron Matplotlib, Pydantic, scikit-learn o PyInstaller porque el flujo implementado no los necesita. Las validaciones son explícitas, las anomalías usan IQR y la entrega es fuente. No es una interfaz web ni depende de Streamlit.

## Datos y seguridad del prototipo

Se incluyen únicamente datos sintéticos de example.com. La app no transmite CSV a servicios externos. Kaggle es una descarga opcional invocada aparte. Los CSV de salida neutralizan prefijos de fórmula para abrirse en hojas de cálculo. La configuración SQL queda en `.env`, excluida de Git. Los reportes contienen nombres de columnas, perfiles y posiciones de incidencias; no se deben tratar como anonimizados de forma certificada.

La aplicación carga el CSV completo en memoria y limita la entrada a 100 MB y 100 000 registros. No existe cifrado de archivos local, gestión de usuarios, permisos por pantalla, migraciones incrementales, ejecución distribuida ni SLA de producción. Las reglas regex deben ser confiables; no hay timeout individual de expresiones regulares.

## Fuentes técnicas consultadas

- Qt, QThread y señales: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html
- SQLAlchemy 2.0, SQL Server y pyodbc: https://docs.sqlalchemy.org/en/20/dialects/mssql.html

La documentación técnica respalda el uso de hilos/señales y conexión ODBC; las métricas y decisiones de negocio son definiciones explícitas de este prototipo.
