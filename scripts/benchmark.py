"""Medición local reproducible del flujo carga + motor + persistencia demo."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generar_demo import generar
from src.database.repository import Repository
from src.service import ejecutar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeticiones', type=int, default=3)
    parser.add_argument('--salida', type=Path, default=ROOT / 'reports/benchmark.json')
    args = parser.parse_args()
    if args.repeticiones < 1:
        parser.error('repeticiones debe ser positivo.')
    workspace = ROOT / 'reports' / f'benchmark-{uuid.uuid4().hex}'
    workspace.mkdir(parents=True)
    rules = json.loads((ROOT / 'config/reglas_demo.json').read_text(encoding='utf-8'))
    repo = Repository(demo=True, demo_path=workspace / 'benchmark.db')
    repo.init()
    result = {'fecha_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
              'sistema': platform.system(), 'maquina': platform.machine(),
              'alcance': 'Carga, analisis IQR y guardado SQLite; excluye generacion, inicio Python y exportacion.',
              'casos': []}
    try:
        for n in (10_000, 100_000):
            path = workspace / f'demo_{n}.csv'
            generar(path, n)
            durations = []
            motor = []
            for _ in range(args.repeticiones):
                start = time.perf_counter()
                report = ejecutar(path, rules, repo, anomalies=True)
                durations.append(round(time.perf_counter() - start, 4))
                motor.append(report['segundos'])
                if not report['guardado']:
                    raise RuntimeError(report['error_bd'])
            result['casos'].append({'filas': n, 'columnas': report['columnas'],
                                   'segundos_totales': durations, 'mediana_segundos': statistics.median(durations),
                                   'segundos_motor': motor, 'score': report['score'],
                                   'cobertura': report['cobertura'], 'muestra': len(report['incidencias'])})
    finally:
        repo.engine.dispose()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
