"""Entrada de escritorio, análisis batch y monitor experimental de CSV."""
import argparse
import json
from pathlib import Path
from threading import Event

from dotenv import load_dotenv

from src.database.repository import Repository
from src.exporter import exportar
from src.monitoring.monitor import MonitorCSV
from src.service import ejecutar

ROOT = Path(__file__).resolve().parent


def monitor_cli(args, rules, repo):
    monitor = MonitorCSV(args.csv, rules, repo, keys=args.keys,
                         anomalies=args.anomalies, sep=args.sep, encoding=args.encoding,
                         interval=args.interval, stable_seconds=args.stability, threshold=args.threshold)
    stop = Event()
    exit_code = 0
    reports = 0
    last_event = None
    try:
        for event in monitor.events(stop, args.max_polls):
            report = event.pop('reporte')
            last_event = event
            if report is not None:
                destination = exportar(report, args.output)
                reports += 1
                event.update(id=report['id'], score=report['score'], cobertura=report['cobertura'],
                             guardado=report['guardado'], reporte=str(destination))
                if not report['guardado']:
                    exit_code = 2
            print(json.dumps(event, ensure_ascii=False), flush=True)
    except KeyboardInterrupt:
        print('Monitoreo detenido.', flush=True)
    finally:
        stop.set()
    if last_event and last_event['estado'] == 'error':
        return 1
    return exit_code if reports else 1


def main(argv=None):
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description='SistemaCalidadDatos · Escritorio / CLI')
    parser.add_argument('--demo', action='store_true', help='Usar SQLite explícitamente para demo')
    parser.add_argument('--mvp', action='store_true', help='Abrir la interfaz guiada del MVP')
    parser.add_argument('--init-db', action='store_true', help='Crear tablas en la base configurada')
    parser.add_argument('--csv')
    parser.add_argument('--rules', default=None)
    parser.add_argument('--keys', default='')
    parser.add_argument('--anomalies', action='store_true')
    parser.add_argument('--sep', default=None)
    parser.add_argument('--encoding', default='utf-8-sig')
    parser.add_argument('--output', default=str(ROOT / 'reports'))
    parser.add_argument('--watch', action='store_true', help='Monitorear cambios en --csv (experimental)')
    parser.add_argument('--interval', type=float, default=2, help='Segundos entre sondeos; mínimo 0.1')
    parser.add_argument('--stability', type=float, default=1, help='Segundos de estabilidad antes de analizar')
    parser.add_argument('--threshold', type=float, default=90, help='Umbral de alerta del monitor, 0 a 100')
    parser.add_argument('--max-polls', type=int, help='Detener tras N sondeos (para pruebas o ejecución acotada)')
    args = parser.parse_args(argv)
    if args.mvp and (args.csv or args.watch or args.init_db):
        parser.error('--mvp abre la interfaz y no se combina con --csv, --watch ni --init-db.')
    if args.watch and (not args.csv or args.init_db):
        parser.error('--watch requiere --csv y no se combina con --init-db.')
    if args.max_polls is not None and (not args.watch or args.max_polls < 1):
        parser.error('--max-polls requiere --watch y un entero positivo.')
    args.keys = [key.strip() for key in args.keys.split(',') if key.strip()]
    repo = None
    error = ''
    try:
        repo = Repository(demo=args.demo, demo_path=ROOT / 'data/demo.db')
        repo.init()
    except Exception:
        if repo is not None:
            repo.engine.dispose()
        repo = None
        error = ('No se pudo abrir la base demo; revisa permisos de data/.' if args.demo else
                 'Configura .env, crea la base y comprueba el controlador ODBC.')
    try:
        if args.init_db:
            print('Base conectada y tablas disponibles.' if repo else error)
            return 0 if repo else 1
        if args.csv:
            try:
                rules = json.loads(Path(args.rules).read_text(encoding='utf-8-sig')) if args.rules else []
                if args.watch:
                    return monitor_cli(args, rules, repo)
                report = ejecutar(args.csv, rules, repo, args.keys, args.anomalies, args.sep, args.encoding)
                destination = exportar(report, args.output)
                print(json.dumps({'score': report['score'], 'cobertura': report['cobertura'],
                                  'guardado': report['guardado'], 'reporte': str(destination)}, ensure_ascii=False))
                if not report['guardado']:
                    print(report.get('error_bd', error))
                    return 2
                return 0
            except (OSError, ValueError, KeyError, TypeError) as exc:
                print(f'No se completó el análisis: {exc}')
                return 1
        if args.mvp:
            from src.dashboard.mvp import launch
        else:
            from src.dashboard.app import launch
        return launch(repo, args.demo, error)
    finally:
        if repo is not None:
            repo.engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
