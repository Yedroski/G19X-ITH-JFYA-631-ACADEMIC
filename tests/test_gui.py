import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from src.dashboard.app import Window
from src.database.repository import Repository


def test_flujo_gui(tmp_path):
    app=QApplication.instance() or QApplication([])
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
