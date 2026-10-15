-- Ejecutar en SSMS con una cuenta que pueda crear bases.
USE master;
GO
IF DB_ID(N'SistemaCalidadDatos') IS NULL
    CREATE DATABASE SistemaCalidadDatos;
GO
USE SistemaCalidadDatos;
GO
-- El script 02 crea tablas; también puede usarse python main.py --init-db.
