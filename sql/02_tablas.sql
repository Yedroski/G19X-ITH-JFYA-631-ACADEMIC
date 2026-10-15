-- Esquema generado desde el mismo modelo usado por la aplicación.

USE SistemaCalidadDatos;
GO

IF OBJECT_ID(N'dbo.fuentes', N'U') IS NULL
BEGIN

CREATE TABLE fuentes (
	id VARCHAR(36) NOT NULL,
	nombre NVARCHAR(260) NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	PRIMARY KEY (id)
)


END;
GO

IF OBJECT_ID(N'dbo.ejecuciones', N'U') IS NULL
BEGIN

CREATE TABLE ejecuciones (
	id VARCHAR(36) NOT NULL,
	fuente_id VARCHAR(36) NOT NULL,
	fecha VARCHAR(40) NOT NULL,
	filas INTEGER NOT NULL,
	score FLOAT NOT NULL,
	payload NTEXT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(fuente_id) REFERENCES fuentes (id)
)


END;
GO

IF OBJECT_ID(N'dbo.metricas', N'U') IS NULL
BEGIN

CREATE TABLE metricas (
	id INTEGER NOT NULL IDENTITY,
	ejecucion_id VARCHAR(36) NOT NULL,
	nombre VARCHAR(30) NOT NULL,
	valor FLOAT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones (id)
)


END;
GO

IF OBJECT_ID(N'dbo.reglas', N'U') IS NULL
BEGIN

CREATE TABLE reglas (
	id INTEGER NOT NULL IDENTITY,
	ejecucion_id VARCHAR(36) NOT NULL,
	codigo NVARCHAR(100) NOT NULL,
	configuracion NTEXT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones (id)
)


END;
GO

IF OBJECT_ID(N'dbo.resultados', N'U') IS NULL
BEGIN

CREATE TABLE resultados (
	id INTEGER NOT NULL IDENTITY,
	ejecucion_id VARCHAR(36) NOT NULL,
	detalle NTEXT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones (id)
)


END;
GO
