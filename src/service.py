"""Orquestación del análisis y persistencia compartida por CLI, GUI y monitor."""
from pathlib import Path
from src.ingestion.data_loader import cargar_snapshot
from src.quality.engine import analizar


def guardar_reporte(report, repo=None):
    report['guardado'] = False
    if repo is not None:
        report['guardado'] = True
        try:
            repo.save(report)
        except Exception:
            report['guardado'] = False
            report['error_bd'] = 'No se guardó el histórico. Revisa conexión/permisos de la base y reintenta.'
    return report


def ejecutar(path, rules, repo=None, keys=None, anomalies=False, sep=None, encoding='utf-8-sig', expected_sha256=None):
    df, digest, _ = cargar_snapshot(path, sep, encoding)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError('El CSV cambió desde la vista previa. Vuelve a cargarlo antes de analizar.')
    report = analizar(df, rules, Path(path).name, keys, anomalies)
    report['sha256'] = digest
    report['ingestion'] = {'encoding': encoding, 'separador': sep or 'auto'}
    return guardar_reporte(report, repo)
