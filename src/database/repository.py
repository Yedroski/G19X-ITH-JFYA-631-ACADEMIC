"""Persistencia transaccional. SQL Server principal; SQLite solo demo explícita."""
import json
import os
from pathlib import Path
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Unicode,
                        UnicodeText, Integer, Float, ForeignKey, select, insert)
from sqlalchemy.engine import URL

metadata = MetaData()
fuentes = Table('fuentes', metadata, Column('id', String(36), primary_key=True),
                Column('nombre', Unicode(260), nullable=False), Column('sha256', String(64), nullable=False))
ejecuciones = Table('ejecuciones', metadata, Column('id', String(36), primary_key=True),
    Column('fuente_id', String(36), ForeignKey('fuentes.id'), nullable=False),
    Column('fecha', String(40), nullable=False), Column('filas', Integer, nullable=False),
    Column('score', Float, nullable=False), Column('payload', UnicodeText, nullable=False))
reglas = Table('reglas', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ejecucion_id', String(36), ForeignKey('ejecuciones.id'), nullable=False),
    Column('codigo', Unicode(100), nullable=False), Column('configuracion', UnicodeText, nullable=False))
metricas = Table('metricas', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ejecucion_id', String(36), ForeignKey('ejecuciones.id'), nullable=False),
    Column('nombre', String(30), nullable=False), Column('valor', Float, nullable=True))
resultados = Table('resultados', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ejecucion_id', String(36), ForeignKey('ejecuciones.id'), nullable=False),
    Column('detalle', UnicodeText, nullable=False))

class Repository:
    def __init__(self, demo=False, demo_path='data/demo.db'):
        if demo:
            Path(demo_path).parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine(URL.create('sqlite', database=str(demo_path)))
        else:
            conn = os.getenv('SQLSERVER_ODBC', '')
            if not conn:
                raise ValueError('Configura SQLSERVER_ODBC en .env o inicia con --demo explícitamente.')
            self.engine = create_engine(URL.create('mssql+pyodbc', query={'odbc_connect': conn}),
                                        pool_pre_ping=True, connect_args={'timeout': 8})

    def init(self):
        metadata.create_all(self.engine)

    def save(self, report):
        fid = report['id']
        # Una fuente/snapshot por ejecución: no confunde archivos homónimos.
        with self.engine.begin() as con:
            con.execute(insert(fuentes).values(id=fid, nombre=Path(report['fuente']).name[:260],
                                               sha256=report.get('sha256', 'memoria')))
            con.execute(insert(ejecuciones).values(id=fid, fuente_id=fid, fecha=report['fecha'],
                        filas=report['filas'], score=report['score'],
                        payload=json.dumps(report, ensure_ascii=False, allow_nan=False)))
            for r in report['reglas']:
                con.execute(insert(reglas).values(ejecucion_id=fid, codigo=r['id'][:100],
                            configuracion=json.dumps(r, ensure_ascii=False)))
            for name, value in report['metricas'].items():
                con.execute(insert(metricas).values(ejecucion_id=fid, nombre=name, valor=value))
            for result in report['resultados_reglas']:
                con.execute(insert(resultados).values(ejecucion_id=fid,
                            detalle=json.dumps(result, ensure_ascii=False)))

    def history(self):
        with self.engine.connect() as con:
            rows = con.execute(select(ejecuciones.c.id, ejecuciones.c.fecha, fuentes.c.nombre,
                                      ejecuciones.c.filas, ejecuciones.c.score)
                               .join(fuentes).order_by(ejecuciones.c.fecha.desc()).limit(500))
            return [dict(r._mapping) for r in rows]

    def load(self, run_id):
        with self.engine.connect() as con:
            value = con.execute(select(ejecuciones.c.payload).where(ejecuciones.c.id == run_id)).scalar_one()
            return json.loads(value)
