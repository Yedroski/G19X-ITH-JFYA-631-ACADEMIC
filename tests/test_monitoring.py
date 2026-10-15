import os
from threading import Event

import pytest

from src.database.repository import Repository
from src.monitoring.monitor import MonitorCSV

RULES = [{'id': 'edad', 'type': 'range', 'column': 'edad', 'min': 0, 'max': 100}]


def csv_path(tmp_path):
    path = tmp_path / 'vivo.csv'
    path.write_text('id,edad\n001,20\n', encoding='utf-8')
    return path


def settle(monitor, now):
    assert monitor.poll(now)['estado'] == 'esperando'
    return monitor.poll(now + 1)


def test_detecta_versiones_alerta_y_persiste_una_vez(tmp_path):
    path = csv_path(tmp_path)
    repo = Repository(demo=True, demo_path=tmp_path / 'monitor.db')
    repo.init()
    monitor = MonitorCSV(path, RULES, repo)
    first = settle(monitor, 0)['reporte']
    assert first['score'] == 100 and first['guardado']
    assert monitor.poll(2)['estado'] == 'sin_cambios'
    path.write_text('id,edad\n001,20\n002,150\n', encoding='utf-8')
    second = settle(monitor, 3)['reporte']
    assert second['filas'] == 2 and second['alerta'] == 'REVISAR'
    assert second['sha256'] != first['sha256']
    assert repo.load(second['id']) == second
    assert len(repo.history()) == 2
    assert monitor.poll(5)['estado'] == 'sin_cambios'
    assert len(repo.history()) == 2
    repo.engine.dispose()


def test_cambio_solo_de_fecha_no_duplica_contenido(tmp_path):
    path = csv_path(tmp_path)
    monitor = MonitorCSV(path, RULES)
    settle(monitor, 0)
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert settle(monitor, 2)['estado'] == 'sin_cambios'
    assert len(monitor.recent) == 1


def test_espera_y_reintenta_archivo_incompleto(tmp_path):
    path = csv_path(tmp_path)
    monitor = MonitorCSV(path, RULES)
    first = settle(monitor, 0)['reporte']
    path.write_text('id,edad\n001,20\n002', encoding='utf-8')
    assert settle(monitor, 2)['estado'] == 'error'
    assert monitor.last_report == first
    path.write_text('id,edad\n001,20\n002,99\n', encoding='utf-8')
    assert settle(monitor, 4)['reporte']['filas'] == 2


def test_ausencia_y_recreacion_de_fuente(tmp_path):
    path = tmp_path / 'pendiente.csv'
    monitor = MonitorCSV(path, RULES)
    assert monitor.poll(0)['estado'] == 'error'
    path.write_text('id,edad\n1,20\n', encoding='utf-8')
    assert settle(monitor, 1)['estado'] == 'analizado'
    path.unlink()
    assert monitor.poll(3)['estado'] == 'error'
    path.write_text('id,edad\n1,300\n', encoding='utf-8')
    assert settle(monitor, 4)['reporte']['alerta'] == 'REVISAR'


def test_esquema_incompatible_no_sobrescribe_ultimo_resultado(tmp_path):
    path = csv_path(tmp_path)
    monitor = MonitorCSV(path, RULES)
    first = settle(monitor, 0)['reporte']
    path.write_text('id,otra\n1,20\n', encoding='utf-8')
    event = settle(monitor, 2)
    assert event['estado'] == 'error'
    assert monitor.last_report == first


def test_cambio_durante_analisis_no_guarda_reporte_obsoleto(tmp_path, monkeypatch):
    import src.monitoring.monitor as module
    path = csv_path(tmp_path)
    original = module.analizar
    saved = []
    class Repo:
        def save(self, report):
            saved.append(report)
    def changing(*args, **kwargs):
        report = original(*args, **kwargs)
        path.write_text('id,edad\n001,20\n002,30\n', encoding='utf-8')
        return report
    monkeypatch.setattr(module, 'analizar', changing)
    monitor = MonitorCSV(path, RULES, Repo())
    assert settle(monitor, 0)['estado'] == 'esperando'
    assert not saved and monitor.last_report is None
    monkeypatch.setattr(module, 'analizar', original)
    assert settle(monitor, 2)['reporte']['filas'] == 2
    assert len(saved) == 1


def test_bloqueo_temporal_reintenta(tmp_path, monkeypatch):
    import src.monitoring.monitor as module
    path = csv_path(tmp_path)
    monitor = MonitorCSV(path, RULES)
    original = module.cargar_snapshot
    def locked(*args):
        raise PermissionError('archivo bloqueado')
    monkeypatch.setattr(module, 'cargar_snapshot', locked)
    assert settle(monitor, 0)['estado'] == 'error'
    monkeypatch.setattr(module, 'cargar_snapshot', original)
    assert settle(monitor, 2)['estado'] == 'analizado'


def test_fallo_bd_entrega_reporte_y_conserva_diagnostico(tmp_path):
    class Broken:
        def save(self, report):
            raise RuntimeError('desconectada')
    monitor = MonitorCSV(csv_path(tmp_path), RULES, Broken())
    event = settle(monitor, 0)
    assert event['reporte']['guardado'] is False
    assert 'error_bd' in event['reporte']
    assert monitor.poll(2)['estado'] == 'sin_cambios'


def test_configuracion_se_copia_y_umbral_es_configurable(tmp_path):
    rules = [dict(RULES[0])]
    path = csv_path(tmp_path)
    path.write_text('id,edad\n1,150\n', encoding='utf-8')
    monitor = MonitorCSV(path, rules, threshold=50)
    rules[0]['max'] = 1000
    report = settle(monitor, 0)['reporte']
    assert report['resultados_reglas'][0]['fallos'] == 1
    assert report['alerta'] == 'ACEPTABLE'
    assert report['monitoreo']['umbral_alerta'] == 50


@pytest.mark.parametrize('kwargs', [{'interval': 0}, {'interval': float('nan')}, {'threshold': 101},
                                    {'threshold': float('inf')}, {'stable_seconds': -1}, {'interval': True}])
def test_opciones_invalidas(tmp_path, kwargs):
    with pytest.raises(ValueError):
        MonitorCSV(tmp_path / 'x.csv', **kwargs)


def test_detencion_y_sondeos_acotados(tmp_path):
    monitor = MonitorCSV(csv_path(tmp_path), RULES, interval=.1)
    stop = Event()
    assert len(list(monitor.events(stop, max_polls=1))) == 1
    stop.set()
    assert list(monitor.events(stop)) == []
    with pytest.raises(ValueError):
        list(monitor.events(stop, max_polls=0))


def test_historial_de_sesion_tiene_limite(tmp_path):
    path = csv_path(tmp_path)
    monitor = MonitorCSV(path, RULES)
    for i in range(102):
        path.write_text(f'id,edad\n{i},20\n', encoding='utf-8')
        # Asegura identidad distinta incluso en filesystems con timestamp grueso.
        stamp = 1_800_000_000_000_000_000 + i * 1_000_000_000
        os.utime(path, ns=(stamp, stamp))
        assert settle(monitor, i * 2)['estado'] == 'analizado'
    assert len(monitor.recent) == 100
