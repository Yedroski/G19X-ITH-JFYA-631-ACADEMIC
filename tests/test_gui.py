import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import time
from pathlib import Path
from PySide6.QtTest import QTest
from src.dashboard.app import Window
from src.database.repository import Repository


def test_flujo_gui(tmp_path, qt_app):
    app=qt_app
    repo=Repository(demo=True,demo_path=tmp_path/'gui.db');repo.init()
    win=Window(repo,demo=True);win.show()
    win.path.setText(str(Path('data/input/demo_clientes.csv').resolve()))
    win.editor.setPlainText(Path('config/reglas_demo.json').read_text(encoding='utf-8'))
    win.start()
    for _ in range(600):
        app.processEvents();QTest.qWait(10)
        if win.worker.isFinished() and win.report:break
    assert win.report and win.report['filas']==1000
    assert win.report['guardado'];assert win.profile.rowCount()==7
    assert win.rules_result.rowCount()==7;assert win.history.rowCount()==1
    win.filter.setText('regex');assert win.issues.rowCount()>0
    win.open_history(0,0);assert win.report['filas']==1000
    win.grab().save(str(tmp_path/'interfaz.png'))
    win.close()
    win.deleteLater()
    repo.engine.dispose()


def wait_for(app, condition, timeout=6):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
        if condition():
            return
    raise AssertionError('La interfaz no completó la operación a tiempo.')


def test_monitoreo_gui_actualiza_detiene_y_reinicia(tmp_path, qt_app):
    app = qt_app
    path = tmp_path / 'vivo.csv'
    path.write_text('id,edad\n001,20\n', encoding='utf-8')
    win = Window()
    win.show()
    win.path.setText(str(path))
    win.editor.setPlainText(json.dumps([{'id': 'r', 'type': 'range', 'column': 'edad', 'max': 100}]))
    panel = win.monitor_panel
    panel.interval.setValue(.1)
    panel.stability.setValue(.1)
    win.tabs.setCurrentWidget(panel)
    try:
        win.start_monitor()
        wait_for(app, lambda: panel.timeline.rowCount() == 1)
        assert not win.run.isEnabled() and not win.editor.isEnabled()
        assert win.tabs.currentWidget() == panel
        path.write_text('id,edad\n001,20\n002,150\n', encoding='utf-8')
        wait_for(app, lambda: panel.timeline.rowCount() == 2)
        assert win.report['filas'] == 2 and win.report['alerta'] == 'REVISAR'
        assert win.profile.rowCount() == 2
        win.stop_monitor()
        wait_for(app, lambda: panel.start_button.isEnabled())
        assert win.run.isEnabled() and win.editor.isEnabled()
        win.start_monitor()
        wait_for(app, lambda: panel.timeline.rowCount() == 1)
        win.close()
        wait_for(app, lambda: not win.isVisible())
        assert not win.monitor_worker.isRunning()
    finally:
        win.stop_monitor()
        if win.monitor_worker:
            win.monitor_worker.wait(6000)
        app.processEvents()
        win.close()
        win.deleteLater()


def test_detencion_interrumpe_espera_larga(tmp_path, qt_app):
    from src.dashboard.monitor import MonitorWorker
    from src.monitoring.monitor import MonitorCSV
    app = qt_app
    worker = MonitorWorker(MonitorCSV(tmp_path / 'ausente.csv', interval=30))
    worker.start()
    QTest.qWait(50)
    worker.stop()
    assert worker.wait(1000)
    worker.deleteLater()
    app.processEvents()
