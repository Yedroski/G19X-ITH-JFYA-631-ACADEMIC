"""Compatibilidad de entrada y ciclo de vida del monitor en la interfaz unificada."""
import time

from PySide6.QtTest import QTest

from src.dashboard.app import Window
from src.dashboard.mvp import MvpWindow


def wait_for(app, condition, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
        if condition():
            return
    raise AssertionError('La interfaz no completó la operación a tiempo.')


def test_entrada_anterior_es_la_misma_interfaz():
    assert Window is MvpWindow


def test_monitoreo_gui_actualiza_detiene_y_reinicia(tmp_path, qt_app):
    path = tmp_path / 'vivo.csv'
    path.write_text('id,edad\n001,20\n', encoding='utf-8')
    win = Window()
    win.show()
    win.load_source(path, [{'id': 'r', 'type': 'range', 'column': 'edad', 'max': 100}])
    wait_for(qt_app, lambda: not win.busy)
    panel = win.monitor_panel
    panel.interval.setValue(.1)
    panel.stability.setValue(.1)
    win.tabs.setCurrentWidget(panel)
    try:
        win.start_monitor()
        wait_for(qt_app, lambda: panel.timeline.rowCount() == 1)
        assert not win.analyze_button.isEnabled() and not win.builder.isEnabled()
        assert not win.demo_button.isEnabled() and not win.export_button.isEnabled()
        assert win.tabs.currentWidget() == panel
        report_id = win.report['id']
        win.start_analysis()
        win.load_source(tmp_path / 'otro.csv')
        win.refresh_history()
        assert not win.busy and win.loaded['path'] == str(path.resolve())
        path.write_text('id,edad\n001,20\n002,150\n', encoding='utf-8')
        wait_for(qt_app, lambda: panel.timeline.rowCount() == 2)
        assert win.report['filas'] == 2 and win.report['alerta'] == 'REVISAR'
        assert win.report['id'] != report_id
        assert win.profile.rowCount() == 2
        last_report = win.report
        path.write_text('id,otra\n001,20\n', encoding='utf-8')
        wait_for(qt_app, lambda: 'error' in panel.status.text())
        assert win.report is last_report
        path.write_text('id,edad\n001,50\n', encoding='utf-8')
        wait_for(qt_app, lambda: panel.timeline.rowCount() == 3)
        win.stop_monitor()
        wait_for(qt_app, lambda: not win.monitoring)
        assert win.analyze_button.isEnabled() and win.builder.isEnabled()
        win.start_monitor()
        wait_for(qt_app, lambda: panel.timeline.rowCount() == 1)
        win.close()
        wait_for(qt_app, lambda: not win.isVisible())
        assert not win.monitor_worker.isRunning()
    finally:
        win.stop_monitor()
        if win.monitor_worker:
            win.monitor_worker.wait(10000)
        qt_app.processEvents()
        win.close()
        win.deleteLater()


def test_detencion_interrumpe_espera_larga(tmp_path, qt_app):
    from src.dashboard.monitor import MonitorWorker
    from src.monitoring.monitor import MonitorCSV
    worker = MonitorWorker(MonitorCSV(tmp_path / 'ausente.csv', interval=30))
    worker.start()
    QTest.qWait(50)
    worker.stop()
    assert worker.wait(1000)
    worker.deleteLater()
    qt_app.processEvents()
