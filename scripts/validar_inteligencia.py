"""Evidencia reproducible y limitada al ejemplo sintético; no valida producción."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.data_loader import cargar_snapshot
from src.quality.engine import analizar


def validar():
    path = ROOT / 'data/input/demo_inteligente.csv'
    df, digest, _ = cargar_snapshot(path)
    started = time.perf_counter()
    report = analizar(df, anomalies=True, intelligent=True)
    duration = time.perf_counter() - started
    info = report['inteligencia']
    predicted = {row['registro'] for row in info['resultados']}
    seeded = {401, 402}
    result = {'dataset': path.name, 'sha256': digest, 'filas': len(df),
              'sembrados': sorted(seeded), 'sembrados_detectados': sorted(seeded & predicted),
              'otros_senalados': len(predicted - seeded), 'total_senalados': info['anomalias'],
              'hallazgos_iqr': report['conteos'].get('anomalia', 0),
              'score': report['score'], 'cobertura': report['cobertura'],
              'segundos_motor_incluye_importacion': round(duration, 4),
              'columnas': info['columnas'], 'parametros': info['parametros'],
              'version_sklearn': info['version_sklearn'],
              'fuente_sin_cambios': hashlib.sha256(path.read_bytes()).hexdigest() == digest,
              'limite': 'Caso sintético conocido. Otros señalados son falsos positivos respecto de las etiquetas sembradas; no demuestra exactitud productiva.'}
    assert seeded <= predicted, 'No se detectaron las dos combinaciones sembradas.'
    assert result['hallazgos_iqr'] == 0
    assert result['fuente_sin_cambios'] and report['score'] == 100
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', default='reports/validacion_inteligencia.json')
    args = parser.parse_args()
    result = validar()
    output = Path(args.salida)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
