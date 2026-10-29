import json

import numpy as np
import pandas as pd
import pytest

from scripts.generar_demo_inteligente import dataset
from src.anomalies.isolation_forest import columnas_candidatas, detectar_isolation_forest
from src.database.repository import Repository
from src.exporter import exportar
from src.monitoring.monitor import MonitorCSV
from src.quality.engine import analizar
from src.service import ejecutar


def test_combinaciones_raras_que_iqr_no_detecta_y_score_intacto():
    df = dataset()
    before = df.copy(deep=True)
    base = analizar(df, anomalies=True)
    report = analizar(df, anomalies=True, intelligent=True)
    info = report['inteligencia']
    flagged = {r['registro'] for r in info['resultados']}
    assert {401, 402} <= flagged
    assert base['anomalias'] == 0
    assert info['columnas'] == ['unidades', 'importe']
    assert report['conteos']['anomalia_multivariada'] == len(flagged)
    assert report['registros_con_errores'] == len(flagged)
    assert report['score'] == base['score'] == 100
    assert report['metricas'] == base['metricas']
    assert info == analizar(df, intelligent=True)['inteligencia']
    assert all(r['decision'] < 0 for r in info['resultados'])
    pd.testing.assert_frame_equal(df, before)
    json.dumps(report, allow_nan=False)


def test_filas_incompletas_y_no_finitas_se_omiten_sin_desplazar_registros():
    df = dataset()
    df.loc[0, 'unidades'] = np.nan
    df.loc[1, 'importe'] = np.inf
    df.loc[2, 'importe'] = -np.inf
    mask, info = detectar_isolation_forest(df, ['unidades', 'importe'])
    assert info['filas_evaluadas'] == 399 and info['filas_omitidas'] == 3
    assert not mask.iloc[:3].any()
    assert {401, 402} <= {r['registro'] for r in info['resultados']}
    json.dumps(info, allow_nan=False)


@pytest.mark.parametrize('df', [pd.DataFrame({'x': range(30)}),
                               pd.DataFrame({'x': range(10), 'y': range(10)}),
                               pd.DataFrame({'x': [1]*30, 'y': [2]*30}),
                               pd.DataFrame({'x': [None]*30, 'y': ['texto']*30})])
def test_datos_insuficientes_explican_por_que_no_se_evalua(df):
    mask, info = detectar_isolation_forest(df)
    assert info['estado'] == 'no_evaluable' and info['motivo']
    assert not mask.any() and not info['resultados']


def test_seleccion_excluye_identificadores_constantes_texto_y_claves():
    df = dataset().assign(folio=range(402), constante=7, texto='A', codigo_cliente=range(402))
    selected, excluded = columnas_candidatas(df, exclude=['importe'])
    assert selected == ['unidades']
    assert {'id', 'folio', 'constante', 'texto', 'codigo_cliente', 'importe'} <= excluded.keys()


@pytest.mark.parametrize('value', [0, -1, .6, float('nan'), float('inf'), True, '0.1'])
def test_contaminacion_invalida(value):
    with pytest.raises(ValueError, match='fracción'):
        detectar_isolation_forest(dataset(), contamination=value)


@pytest.mark.parametrize('columns', [['ausente', 'importe'], ['importe', 'importe'], 'importe'])
def test_columnas_invalidas(columns):
    with pytest.raises(ValueError):
        detectar_isolation_forest(dataset(), columns)


def test_conteos_completos_con_detalle_limitado():
    df = dataset()
    full = analizar(df, intelligent=True)
    limited = analizar(df, intelligent=True, sample_limit=1)
    assert limited['anomalias'] == full['anomalias'] > 1
    assert limited['registros_con_errores'] == full['registros_con_errores']
    assert len(limited['incidencias']) == len(limited['inteligencia']['resultados']) == 1
    assert limited['muestra_limitada'] and limited['inteligencia']['detalle_limitado']


def test_servicio_exportacion_historico_y_monitor_conservan_evidencia(tmp_path):
    path = tmp_path / 'inteligente.csv'
    dataset().to_csv(path, index=False)
    before = path.read_bytes()
    repo = Repository(demo=True, demo_path=tmp_path / 'ia.db')
    repo.init()
    try:
        report = ejecutar(path, [], repo, intelligent=True)
        assert repo.load(report['id']) == report
        dest = exportar(report, tmp_path / 'out')
        assert json.loads((dest / 'reporte.json').read_text(encoding='utf-8')) == report
        assert len(pd.read_csv(dest / 'anomalias_inteligentes.csv')) == report['inteligencia']['anomalias']
        monitor = MonitorCSV(path, [], repo, intelligent=True, anomaly_columns=['unidades', 'importe'])
        monitor.poll(0)
        observed = monitor.poll(1)['reporte']
        assert observed['inteligencia']['resultados'] == report['inteligencia']['resultados']
        assert observed['guardado'] and observed['monitoreo']['experimental']
        assert path.read_bytes() == before
    finally:
        repo.engine.dispose()
