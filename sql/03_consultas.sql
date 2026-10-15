USE SistemaCalidadDatos;
GO
SELECT TOP (50) e.id,e.fecha,f.nombre,e.filas,e.score
FROM ejecuciones e JOIN fuentes f ON f.id=e.fuente_id ORDER BY e.fecha DESC;
SELECT e.fecha,m.nombre,m.valor FROM metricas m
JOIN ejecuciones e ON e.id=m.ejecucion_id ORDER BY e.fecha DESC;
SELECT codigo,configuracion FROM reglas;
SELECT ejecucion_id,detalle FROM resultados;
