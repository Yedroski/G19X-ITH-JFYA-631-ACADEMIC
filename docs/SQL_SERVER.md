# Base de datos SQL Server

## Preparación

Necesitas una instancia SQL Server accesible y Microsoft ODBC Driver 18 for SQL Server de 64 bits. SSMS es el cliente de administración, no sustituye al motor. El driver ODBC se instala en Windows; `pip install pyodbc` solo instala el adaptador Python.

1. Conecta SSMS a tu instancia.
2. Ejecuta `sql/01_crear_base.sql` con permisos de creación de bases.
3. Ejecuta `sql/02_tablas.sql` dentro de `SistemaCalidadDatos`. No borra tablas existentes.
4. Copia `.env.example` a `.env`.
5. Cambia `SERVER` al nombre que utilizas en SSMS: por ejemplo `localhost\SQLEXPRESS`, `localhost` o `(localdb)\MSSQLLocalDB` si realmente usas LocalDB.
6. Conserva `Trusted_Connection=yes` para autenticación Windows. La cuenta que ejecuta Python necesita acceso a la BD.
7. Prueba:

```powershell
.\.venv311\Scripts\python.exe main.py --init-db
.\.venv311\Scripts\python.exe main.py
```

Para desarrollo local se incluye `Encrypt=yes;TrustServerCertificate=yes`. En un servidor con certificado válido usa `TrustServerCertificate=no`. No subas `.env` a Git. Si usas autenticación SQL, reemplaza `Trusted_Connection=yes` por `UID=tu_usuario;PWD=tu_clave` dentro de `.env`; no escribas credenciales en el código.

La inicialización comprueba/crea tablas mediante SQLAlchemy. Para bases previamente provisionadas basta con permisos de lectura y escritura de tablas. No hay migraciones de versiones futuras en este prototipo; los scripts no modifican tablas existentes.

## Tablas

| Tabla | Clave / relación | Datos |
|---|---|---|
| fuentes | id UUID textual | Nombre y SHA-256 de la versión analizada |
| ejecuciones | id; fuente_id FK | Fecha UTC, filas, score y reporte JSON completo |
| reglas | id entero; ejecucion_id FK | Snapshot de cada regla aplicada |
| metricas | id entero; ejecucion_id FK | Dimensión y valor nullable |
| resultados | id entero; ejecucion_id FK | Resumen por regla como JSON |

Una fuente representa un snapshot por ejecución; no un catálogo deduplicado de sistemas corporativos. Los perfiles y muestras de incidencias se almacenan dentro del payload de la ejecución. No se cargan todas las filas originales en la BD. Esta decisión simplifica el prototipo y permite reproducir los resultados con el CSV original y su hash.

Todo el guardado ocurre en una transacción: una falla revierte la ejecución completa. Nunca cambia silenciosamente de SQL Server a SQLite. `--demo` debe solicitarse explícitamente.

## Prueba real de integración

```powershell
$env:TEST_SQLSERVER="1"
.\.venv311\Scripts\python.exe -m pytest tests/test_sqlserver.py -v
Remove-Item Env:TEST_SQLSERVER
```

La prueba inserta una ejecución identificada como `prueba_integracion` y comprueba su recuperación. No elimina ni trunca información existente. Ejecútala en tu BD de desarrollo.

## Diagnóstico

- `IM002` / driver no encontrado: instala ODBC Driver 18 de la arquitectura correcta.
- Instancia no encontrada: comprueba el servidor que funciona en SSMS y que el motor esté iniciado.
- Login failed: verifica autenticación y permisos del usuario de Windows/SQL.
- Base inexistente: ejecuta `01_crear_base.sql`.
- Error de certificado: revisa certificados o la configuración de desarrollo local.
- La app indica sin persistencia: el análisis puede exportarse, pero no aparece en histórico. Corrige la conexión y reinicia antes de repetirlo.

## Respaldo

El responsable de la BD debe programar respaldos con SQL Server/SSMS, comprobar su restauración y definir retención. Los JSON exportados respaldan resultados, no sustituyen un backup completo de SQL Server. En demo cierra la aplicación antes de copiar `data/demo.db`.
