"""Punto de entrada GUI y CLI. Ejecutar desde la carpeta del proyecto."""
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from src.database.repository import Repository
from src.service import ejecutar
from src.exporter import exportar

ROOT=Path(__file__).resolve().parent

def main():
    load_dotenv(ROOT/'.env')
    p=argparse.ArgumentParser(description='SistemaCalidadDatos · Escritorio / CLI')
    p.add_argument('--demo',action='store_true',help='Usar SQLite explícitamente para demo')
    p.add_argument('--init-db',action='store_true',help='Crear tablas en la base configurada')
    p.add_argument('--csv');p.add_argument('--rules',default=None)
    p.add_argument('--keys',default='');p.add_argument('--anomalies',action='store_true')
    p.add_argument('--sep',default=None);p.add_argument('--encoding',default='utf-8-sig')
    p.add_argument('--output',default=str(ROOT/'reports'))
    a=p.parse_args();repo=None;error=''
    try:
        repo=Repository(demo=a.demo,demo_path=ROOT/'data/demo.db');repo.init()
    except Exception:
        repo=None;error='Configura .env, crea la base y comprueba el controlador ODBC.'
    if a.init_db:
        if not repo:print(error);return 1
        print('Base conectada y tablas disponibles.');return 0
    if a.csv:
        try:
            rules=json.loads(Path(a.rules).read_text(encoding='utf-8')) if a.rules else []
            r=ejecutar(a.csv,rules,repo,[k.strip() for k in a.keys.split(',') if k.strip()],a.anomalies,a.sep,a.encoding)
            dest=exportar(r,a.output)
            print(json.dumps({'score':r['score'],'cobertura':r['cobertura'],'guardado':r['guardado'],'reporte':str(dest)},ensure_ascii=False))
            if not r['guardado']: print(r.get('error_bd',error));return 2
            return 0
        except Exception as exc:print(f'No se completó el análisis: {exc}');return 1
    from src.dashboard.app import launch
    return launch(repo,a.demo,error)
if __name__=='__main__':raise SystemExit(main())
