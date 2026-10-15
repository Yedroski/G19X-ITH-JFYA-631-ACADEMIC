"""Vista Qt; el análisis ocurre fuera del hilo de interfaz."""
import json
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QFileDialog,
    QLineEdit, QComboBox, QCheckBox, QPlainTextEdit, QMessageBox, QProgressBar,
    QHeaderView, QAbstractItemView)
from src.service import ejecutar
from src.exporter import exportar

class Worker(QThread):
    success = Signal(object)
    failure = Signal(str)
    def __init__(self, kwargs):
        super().__init__(); self.kwargs = kwargs
    def run(self):
        try: self.success.emit(ejecutar(**self.kwargs))
        except (ValueError, KeyError, TypeError) as exc: self.failure.emit(str(exc))
        except Exception: self.failure.emit('No se pudo procesar el archivo. Revisa formato, reglas y permisos.')


def table(rows):
    t=QTableWidget(); fill(t,rows); return t


def fill(t, rows):
    t.clear(); t.setRowCount(len(rows)); t.setColumnCount(len(rows[0]) if rows else 0)
    if rows:
        t.setHorizontalHeaderLabels(list(rows[0]))
        for i,row in enumerate(rows):
            for j,v in enumerate(row.values()):
                t.setItem(i,j,QTableWidgetItem('N/D' if v is None else str(v)))
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)

class Window(QMainWindow):
    def __init__(self, repo=None, demo=False, db_error=''):
        super().__init__(); self.repo=repo; self.report=None; self.worker=None
        self.setWindowTitle('SistemaCalidadDatos · Calidad y monitoreo'); self.resize(1280,850)
        root=QWidget(); self.setCentralWidget(root); layout=QVBoxLayout(root)
        title=QLabel('CALIDAD DE DATOS  /  Laboratorio de análisis'); title.setObjectName('title');layout.addWidget(title)
        layout.addWidget(QLabel('CSV → Perfilado → Reglas → Métricas → Histórico'))
        self.status=QLabel(('Modo DEMO · SQLite local' if demo else 'SQL Server · Histórico conectado') if repo else 'Sin persistencia · '+db_error)
        layout.addWidget(self.status)
        bar=QHBoxLayout(); self.path=QLineEdit(); self.path.setPlaceholderText('Selecciona un archivo CSV')
        choose=QPushButton('Abrir CSV');choose.clicked.connect(self.choose)
        self.run=QPushButton('Analizar'); self.run.setObjectName('primary');self.run.clicked.connect(self.start)
        bar.addWidget(self.path,1);bar.addWidget(choose);bar.addWidget(self.run);layout.addLayout(bar)
        options=QHBoxLayout(); self.sep=QComboBox();self.sep.addItems(['Auto',',',';','Tab','|'])
        self.encoding=QComboBox();self.encoding.addItems(['utf-8-sig','cp1252','latin-1'])
        self.keys=QLineEdit();self.keys.setPlaceholderText('Claves duplicados: id, sucursal (vacío = fila completa)')
        self.anomalies=QCheckBox('Anomalías IQR'); options.addWidget(QLabel('Separador'));options.addWidget(self.sep)
        options.addWidget(self.encoding);options.addWidget(self.keys,1);options.addWidget(self.anomalies);layout.addLayout(options)
        self.progress=QProgressBar();self.progress.setRange(0,1);self.progress.setValue(0);layout.addWidget(self.progress)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        dashboard=QWidget();dl=QVBoxLayout(dashboard);self.score=QLabel('Selecciona un CSV para comenzar');self.score.setObjectName('score');dl.addWidget(self.score)
        self.summary=QLabel('Los resultados se calculan sobre el archivo completo.');dl.addWidget(self.summary)
        self.bars={}
        for name in ['completitud','validez','unicidad','consistencia']:
            line=QHBoxLayout();label=QLabel(name.capitalize());label.setMinimumWidth(130);line.addWidget(label)
            b=QProgressBar();b.setRange(0,10000);b.setFormat('N/D');line.addWidget(b);self.bars[name]=b;dl.addLayout(line)
        self.notice=QLabel('');self.notice.setWordWrap(True);dl.addWidget(self.notice);dl.addStretch()
        export=QPushButton('Exportar reporte JSON y tablas CSV');export.clicked.connect(self.export);dl.addWidget(export)
        self.tabs.addTab(dashboard,'Dashboard')
        self.profile=table([]);self.tabs.addTab(self.profile,'Perfilado')
        rule_page=QWidget();rl=QVBoxLayout(rule_page)
        rl.addWidget(QLabel('Reglas JSON editables · required / unique / range / regex / allowed / date / compare'))
        rb=QHBoxLayout();load=QPushButton('Cargar reglas');load.clicked.connect(self.load_rules)
        save=QPushButton('Guardar reglas');save.clicked.connect(self.save_rules)
        clear=QPushButton('Sin reglas');clear.clicked.connect(lambda:self.editor.setPlainText('[]'))
        for button in [load,save,clear]:rb.addWidget(button)
        rl.addLayout(rb);self.editor=QPlainTextEdit('[]');rl.addWidget(self.editor)
        self.tabs.addTab(rule_page,'Configurar reglas')
        self.rules_result=table([]);self.tabs.addTab(self.rules_result,'Resultado de reglas')
        issue_page=QWidget();il=QVBoxLayout(issue_page);self.filter=QLineEdit();self.filter.setPlaceholderText('Filtrar incidencias por tipo, columna o regla…')
        self.filter.textChanged.connect(self.filter_issues);il.addWidget(self.filter);self.issues=table([]);il.addWidget(self.issues)
        self.tabs.addTab(issue_page,'Incidencias y acciones')
        history_page=QWidget();hl=QVBoxLayout(history_page);refresh=QPushButton('Actualizar histórico');refresh.clicked.connect(self.refresh)
        hl.addWidget(refresh);hl.addWidget(QLabel('Doble clic para recuperar un análisis. Compara solo archivos y reglas equivalentes.'))
        self.history=table([]);self.history.cellDoubleClicked.connect(self.open_history);hl.addWidget(self.history)
        self.tabs.addTab(history_page,'Histórico');self.refresh()
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#f3f6fb; color:#192c45; font-size:13px; }
            QLabel#title { font-size:23px; font-weight:700; padding:12px 0; }
            QLabel#score { font-size:38px; font-weight:700; padding:24px 4px; color:#125a83; }
            QPushButton { background:#e1e9f3; padding:10px 16px; border:0; border-radius:5px; }
            QPushButton#primary { background:#126486; color:white; font-weight:700; }
            QPushButton:disabled { color:#8995a4; }
            QLineEdit,QComboBox,QPlainTextEdit { background:white; padding:8px; border:1px solid #ccd7e5; }
            QTableWidget { background:white; gridline-color:#e1e7ee; }
            QHeaderView::section { background:#e5edf7; padding:8px; border:0; }
            QTabBar::tab { padding:12px; } QTabBar::tab:selected { background:white; color:#126486; }
            QProgressBar { background:#dfe8f1; border:0; border-radius:4px; text-align:center; min-height:24px; }
            QProgressBar::chunk { background:#61b7b0; border-radius:4px; }
        """)
    def choose(self):
        p,_=QFileDialog.getOpenFileName(self,'Seleccionar CSV','data/input','CSV (*.csv)')
        if p:self.path.setText(p)
    def load_rules(self):
        p,_=QFileDialog.getOpenFileName(self,'Reglas','config','JSON (*.json)')
        if p:
            try:
                content=Path(p).read_text(encoding='utf-8');json.loads(content);self.editor.setPlainText(content)
            except Exception:QMessageBox.warning(self,'Reglas','No se pudo leer el JSON.')
    def save_rules(self):
        try: content=json.loads(self.editor.toPlainText())
        except ValueError: QMessageBox.warning(self,'Reglas','JSON inválido.');return
        p,_=QFileDialog.getSaveFileName(self,'Guardar reglas','config/reglas_personales.json','JSON (*.json)')
        if p:
            try:Path(p).write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError:QMessageBox.warning(self,'Reglas','No se pudo guardar el archivo.')
    def start(self):
        if self.worker and self.worker.isRunning():return
        try:rules=json.loads(self.editor.toPlainText())
        except ValueError:QMessageBox.warning(self,'Reglas','JSON inválido.');return
        sep=self.sep.currentText();sep=None if sep=='Auto' else '\t' if sep=='Tab' else sep
        self.run.setEnabled(False);self.progress.setRange(0,0)
        self.worker=Worker(dict(path=self.path.text(),rules=rules,repo=self.repo,
            keys=[v.strip() for v in self.keys.text().split(',') if v.strip()],
            anomalies=self.anomalies.isChecked(),sep=sep,encoding=self.encoding.currentText()))
        self.worker.success.connect(self.show_report);self.worker.failure.connect(self.failure)
        self.worker.finished.connect(self.done);self.worker.start()
    def done(self):
        self.progress.setRange(0,1);self.progress.setValue(1);self.run.setEnabled(True)
    def failure(self,message):QMessageBox.warning(self,'No se completó el análisis',message)
    def show_report(self,r):
        self.report=r;self.score.setText(f"{r['score']:.2f} / 100   ·   {r['alerta']}")
        self.summary.setText(f"{r['fuente']}   |   {r['filas']:,} registros   |   {r['columnas']} columnas   |   "
                             f"{r['faltantes']} celdas faltantes   |   {r['duplicados']} duplicados excedentes   |   {r['segundos']:.3f} s (motor)")
        for name,b in self.bars.items():
            v=r['metricas'][name];b.setValue(round(v*100) if v is not None else 0);b.setFormat(f'{v:.2f}%' if v is not None else 'N/D · sin evaluaciones')
        self.notice.setText(f"Cobertura del score: {r['cobertura']}%. Las dimensiones no evaluadas se excluyen y los pesos se renormalizan. "
                            f"Registros con hallazgos: {r.get('registros_con_errores', 'N/D')}; "
                            f"reglas incumplidas: {r.get('reglas_incumplidas', 'N/D')}; anomalías: {r.get('anomalias', 0)}. "
                            f"Incidencias: {sum(r['conteos'].values())}; muestra visible/exportable: {len(r['incidencias'])}. "
                            'Las anomalías son indicios y no afectan el score. '+
                            (r.get('error_bd','') or ('Histórico guardado.' if r.get('guardado') else 'Sin guardar en base de datos.')))
        fill(self.profile,r['perfil']);fill(self.rules_result,r['resultados_reglas']);self.filter_issues();self.tabs.setCurrentIndex(0);self.refresh()
    def filter_issues(self):
        if self.report:
            q=self.filter.text().casefold();fill(self.issues,[r for r in self.report['incidencias'] if q in str(r).casefold()])
    def refresh(self):
        if not self.repo:return
        try:fill(self.history,self.repo.history())
        except Exception:self.status.setText('Histórico no disponible. Revisa conexión y permisos de la base.')
    def open_history(self,row,col):
        try:self.show_report(self.repo.load(self.history.item(row,0).text()))
        except Exception:QMessageBox.warning(self,'Histórico','No se pudo recuperar el análisis.')
    def export(self):
        if not self.report:QMessageBox.information(self,'Exportar','Primero ejecuta un análisis.');return
        p=QFileDialog.getExistingDirectory(self,'Carpeta destino','reports')
        if p:
            try:
                dest=exportar(self.report,p);QMessageBox.information(self,'Exportado',str(dest))
            except Exception:QMessageBox.warning(self,'Exportar','No se pudo escribir el reporte.')
    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self,'Análisis en curso','Espera a que termine el análisis antes de cerrar.');event.ignore()
        else:event.accept()


def launch(repo=None,demo=False,db_error=''):
    app=QApplication.instance() or QApplication([]);window=Window(repo,demo,db_error);window.show();return app.exec()
