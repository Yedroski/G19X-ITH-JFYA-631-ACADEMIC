import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.data_loader import cargar_csv, cargar_snapshot
from src.profiling.profiler import estadisticas_numericas, perfil_columnas, perfil_general, perfilar
from src.quality.engine import analizar
from src.quality.rules import ejecutar_reglas, validar_fecha_anterior, validar_rango


def test_reglas_originales_sobre_dataset_conservado():
    df = cargar_csv('data/input/global_ai_jobs_2026.csv')
    rules = json.loads(Path('config/reglas_empleos.json').read_text(encoding='utf-8'))
    original = ejecutar_reglas(df, rules)
    integrated = analizar(df, rules)
    assert len(original) == 16
    assert [r['total_errores'] for r in original] == [r['fallos'] for r in integrated['resultados_reglas']]
    assert integrated['cobertura'] == 100
    assert rules[0]['tipo'] == 'obligatorio'


def test_api_original_y_errores_de_conversion():
    df = pd.DataFrame({'valor': ['10', 'texto', 'inf', None],
                       'inicio': ['2026-01-01', '2026-03-01', 'mal', None],
                       'fin': ['2026-02-01'] * 4})
    assert validar_rango(df, 'valor', 0)['indices_error'] == [1, 2]
    assert validar_fecha_anterior(df, 'inicio', 'fin')['indices_error'] == [1, 2]
    assert perfil_general(df)['filas'] == 4
    assert len(perfil_columnas(df)) == 3
    assert estadisticas_numericas(df).loc['valor', 'mean'] == 10


def test_perfil_descriptivo_y_tipo_predominante():
    df = pd.DataFrame({'valor': ['1', '2', '3', 'mal', None], 'fecha': ['2026-01-01'] * 5})
    p = perfilar(df)
    assert p[0]['tipo_inferido'] == 'numérico'
    assert p[0]['media'] == 2 and p[0]['mediana'] == 2
    assert p[0]['desviacion'] == 1 and p[0]['porcentaje_nulos'] == 20
    assert p[1]['tipo_inferido'] == 'fecha ISO'
    assert 'mal' in p[0]['ejemplos']


def test_filas_afectadas_sin_doble_conteo_y_con_indice_repetido():
    df = pd.DataFrame({'x': [None, None, '1']}, index=[0, 0, 0], dtype='string')
    r = analizar(df, [{'id': 'r', 'type': 'required', 'column': 'x'}], sample_limit=1)
    assert r['registros_con_errores'] == 2
    assert r['reglas_ejecutadas'] == r['reglas_incumplidas'] == 1
    assert r['porcentaje_registros_con_errores'] == pytest.approx(66.6667)


@pytest.mark.parametrize('rules', [{}, '', 0, [{'id': 'r', 'type': 'range', 'column': 'a', 'min': float('nan')}],
                                    [{'id': 'r', 'type': 'regex', 'column': 'a', 'pattern': '['}]])
def test_configuracion_invalida_no_pasa_como_sin_reglas(rules):
    with pytest.raises(ValueError):
        analizar(pd.DataFrame({'a': ['1']}), rules)


def test_hash_corresponde_a_los_bytes_analizados(tmp_path):
    path = tmp_path / 'snapshot.csv'
    content = b'id;valor\r\n001;20\r\n'
    path.write_bytes(content)
    df, digest, _ = cargar_snapshot(path)
    assert df.loc[0, 'id'] == '001'
    assert digest == hashlib.sha256(content).hexdigest()


def test_limite_registros(tmp_path, monkeypatch):
    import src.ingestion.data_loader as loader
    monkeypatch.setattr(loader, 'MAX_ROWS', 2)
    path = tmp_path / 'grande.csv'
    path.write_text('id\n1\n2\n3\n')
    with pytest.raises(ValueError, match='100 000'):
        cargar_csv(path)
