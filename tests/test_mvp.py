import hashlib
import json
from pathlib import Path
from threading import Event
import time

import pandas as pd
from PySide6.QtTest import QTest
import pytest

import main
from src.dashboard.mvp import MvpWindow
from src.dashboard.rule_builder import RuleBuilder
from src.database.repository import Repository
from src.quality.engine import analizar
from src.service import ejecutar


def wait_for(app, condition, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
        if condition():
            return
    raise AssertionError('El MVP no completó la operación a tiempo.')


@pytest.fixture
def mvp(tmp_path, qt_app):
    repo = Repository(demo=True, demo_path=tmp_path / 'mvp.db')
    repo.init()
    window = MvpWindow(repo, demo=True)
    window.show()
    yield window
    if window.worker and window.worker.isRunning():
        assert window.worker.wait(10000)
    qt_app.processEvents()
    window.close()
    window.deleteLater()
    repo.engine.dispose()


def test_demo_un_clic_exporta_y_recupera_historial(mvp, qt_app, tmp_path):
    source = Path('data/input/demo_clientes.csv')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    assert not mvp.analyze_button.isEnabled()
    mvp.try_demo()
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None)
    report = mvp.report
    assert report['score'] == 97.3843
    assert report['cobertura'] == 100 and report['guardado']
    assert mvp.preview_table.rowCount() == 20
    assert len(mvp.builder.rules) == 7
    assert mvp.tabs.currentIndex() == 2
    assert mvp.actions.rowCount() > 0
    mvp.issue_filter.setText('email')
    assert 0 < mvp.issues.rowCount() < len(report['incidencias'])
    mvp.export_to(tmp_path / 'export')
    wait_for(qt_app, lambda: not mvp.busy and mvp.last_export is not None)
    assert json.loads((mvp.last_export / 'reporte.json').read_text(encoding='utf-8')) == report
    assert (mvp.last_export / 'perfil.csv').is_file()
    mvp.anomalies.setChecked(True)
    assert mvp.report is None and not mvp.export_button.isEnabled()
    mvp.tabs.setCurrentIndex(3)
    wait_for(qt_app, lambda: not mvp.busy and mvp.history.rowCount() == 1)
    mvp.open_history(0)
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None)
    assert mvp.report == report
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_demo_inteligente_muestra_modelo_y_las_dos_combinaciones(mvp, qt_app):
    mvp.intelligent_demo_button.click()
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None, timeout=20)
    report = mvp.report
    assert report['inteligencia']['estado'] == 'evaluado'
    assert mvp.selected_anomaly_columns() == ['unidades', 'importe']
    assert {401, 402} <= {r['registro'] for r in report['inteligencia']['resultados']}
    assert report['conteos'].get('anomalia', 0) == 0
    assert 'Isolation Forest' in mvp.intelligence_info.text()
    assert mvp.intelligence_table.rowCount() == report['inteligencia']['anomalias']
    mvp.intelligent.setChecked(False)
    assert mvp.report is None
    mvp.start_analysis()
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None)
    assert not mvp.report['inteligencia']['activo']
    assert mvp.report['score'] == report['score']


def test_historico_anterior_sin_inteligencia_sigue_visible(mvp):
    report = analizar(pd.DataFrame({'id': ['1', '2']}))
    report.pop('inteligencia')
    mvp.show_report(report)
    assert 'no incluida' in mvp.intelligence_info.text()
    assert mvp.cards['score'].text() == '100.00'


def test_csv_propio_reglas_visuales_y_metricas(mvp, qt_app, tmp_path):
    path = tmp_path / 'clientes.csv'
    path.write_text('id,edad,email\n001,20,a@example.com\n002,150,mal\n002,150,mal\n003,,\n', encoding='utf-8')
    mvp.load_source(path)
    wait_for(qt_app, lambda: not mvp.busy and mvp.loaded is not None)
    builder = mvp.builder
    builder.column.setCurrentText('edad')
    builder.kind.setCurrentIndex(builder.kind.findData('range'))
    builder.minimum.setText('18')
    builder.maximum.setText('100')
    builder.add_button.click()
    builder.column.setCurrentText('email')
    builder.kind.setCurrentIndex(builder.kind.findData('required'))
    builder.add_button.click()
    mvp.start_analysis()
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None)
    assert mvp.report['faltantes'] == 2
    assert mvp.report['duplicados'] == 1
    assert mvp.report['registros_con_errores'] == 3
    assert mvp.report['score'] == pytest.approx(71.4286)
    assert mvp.report['cobertura'] == 80
    assert 'Evaluación parcial' in mvp.coverage.text()
    assert mvp.preview_table.item(0, 0).text() == '001'


def test_fuente_cambiada_exige_recarga(mvp, qt_app, tmp_path):
    path = tmp_path / 'datos.csv'
    path.write_text('id\n001\n', encoding='utf-8')
    mvp.load_source(path)
    wait_for(qt_app, lambda: not mvp.busy)
    path.write_text('id\n001\n002\n', encoding='utf-8')
    mvp.start_analysis()
    wait_for(qt_app, lambda: not mvp.busy)
    assert mvp.report is None
    assert 'cambió' in mvp.message.text()
    assert mvp.repo.history() == []
    mvp.reload_source()
    wait_for(qt_app, lambda: not mvp.busy)
    mvp.start_analysis()
    wait_for(qt_app, lambda: not mvp.busy and mvp.report is not None)
    assert mvp.report['filas'] == 2 and mvp.report['cobertura'] == 50


def test_archivo_invalido_y_cambio_de_opciones_no_dejan_resultados_viejos(mvp, qt_app, tmp_path):
    path = tmp_path / 'datos.csv'
    path.write_text('id;edad\n001;20\n', encoding='utf-8')
    mvp.load_source(path)
    wait_for(qt_app, lambda: not mvp.busy)
    assert mvp.loaded['columns'] == ['id', 'edad']
    mvp.encoding.setCurrentText('cp1252')
    assert mvp.loaded is None and not mvp.analyze_button.isEnabled()
    mvp.reload_source()
    wait_for(qt_app, lambda: not mvp.busy)
    assert mvp.loaded is not None
    invalid = tmp_path / 'invalido.csv'
    invalid.write_text('id,edad\n001,20,extra\n', encoding='utf-8')
    mvp.load_source(invalid)
    wait_for(qt_app, lambda: not mvp.busy)
    assert mvp.loaded is None and mvp.report is None
    assert not mvp.analyze_button.isEnabled()
    assert not mvp.export_button.isEnabled()
    assert mvp.preview_table.rowCount() == 0


def test_formulario_produce_reglas_ejecutables_y_valida_antes_de_agregar(qt_app):
    widget = RuleBuilder()
    df = pd.DataFrame({'id': ['001', '001', '003'], 'edad': ['20', '150', None],
                       'email': ['a@example.com', 'mal', None], 'estado': ['pagado', 'otro', None],
                       'fecha': ['2026-01-01', 'mal', None], 'total': ['100', '10', None],
                       'descuento': ['10', '20', None], 'inicio': ['2026-01-01', '2026-03-01', None],
                       'fin': ['2026-02-01', '2026-02-01', None]}, dtype='string')
    widget.set_columns(df.columns)
    widget.minimum.setText('18')
    widget.maximum.setText('100')
    widget.values.setPlainText('pagado\npendiente')
    widget.compare_other.setCurrentText('total')
    widget.date_compare_other.setCurrentText('fin')
    widget.pattern.setText(r'\d{3}')
    for kind, column in [('required', 'email'), ('unique', 'id'), ('range', 'edad'),
                         ('allowed', 'estado'), ('email', 'email'), ('date', 'fecha'),
                         ('compare', 'descuento'), ('date_compare', 'inicio'), ('regex', 'id')]:
        widget.kind.setCurrentIndex(widget.kind.findData(kind))
        widget.column.setCurrentText(column)
        widget.add_rule()
    report = analizar(df, widget.rules)
    assert [r['fallos'] for r in report['resultados_reglas']] == [1, 2, 1, 1, 1, 1, 1, 1, 0]
    widget.kind.setCurrentIndex(widget.kind.findData('range'))
    widget.minimum.setText('no es número')
    widget.add_rule()
    assert len(widget.rules) == 9 and widget.error.text()
    widget.table.selectRow(0)
    widget.remove_selected()
    assert len(widget.rules) == 8
    saved = list(widget.rules)
    with pytest.raises(ValueError):
        widget.set_rules([{'id': 'mala', 'type': 'required', 'column': 'ausente'}])
    assert widget.rules == saved
    widget.deleteLater()


def test_cerrar_mvp_espera_operacion_activa(mvp, qt_app, monkeypatch, tmp_path):
    import src.dashboard.mvp as module
    original = module.preview
    release = Event()
    def delayed(**kwargs):
        release.wait(3)
        return original(**kwargs)
    monkeypatch.setattr(module, 'preview', delayed)
    path = tmp_path / 'datos.csv'
    path.write_text('id\n1\n', encoding='utf-8')
    mvp.load_source(path)
    try:
        mvp.close()
        assert mvp.closing and mvp.isVisible()
        release.set()
        wait_for(qt_app, lambda: not mvp.isVisible())
        assert not mvp.worker.isRunning()
    finally:
        release.set()


def test_servicio_rechaza_snapshot_cambiado_antes_de_guardar(tmp_path):
    path = tmp_path / 'datos.csv'
    path.write_text('id\n1\n')
    class NeverSave:
        def save(self, report):
            pytest.fail('No debe guardar un archivo distinto de la vista previa.')
    with pytest.raises(ValueError, match='cambió'):
        ejecutar(path, [], NeverSave(), expected_sha256='distinto')


@pytest.mark.parametrize('args', [['--demo'], ['--demo', '--mvp']])
def test_entrada_mvp_usa_vista_guiada(tmp_path, monkeypatch, args):
    import src.dashboard.mvp as module
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    received = []
    def launch(repo, demo, error):
        received.append((repo is not None, demo, error))
        return 0
    monkeypatch.setattr(module, 'launch', launch)
    assert main.main(args) == 0
    assert received == [(True, True, '')]


@pytest.mark.parametrize('args', [['--mvp', '--csv', 'a.csv'], ['--mvp', '--watch'], ['--mvp', '--init-db']])
def test_mvp_rechaza_modos_incompatibles(args):
    with pytest.raises(SystemExit) as error:
        main.main(args)
    assert error.value.code == 2
