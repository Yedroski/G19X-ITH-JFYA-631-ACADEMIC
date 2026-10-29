"""MVP de escritorio: datos → reglas visuales → resultados verificables."""
from copy import deepcopy
import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QProgressBar, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.dashboard.widgets import fill, table
from src.anomalies.isolation_forest import columnas_candidatas
from src.dashboard.monitor import MonitorPanel, MonitorWorker
from src.dashboard.rule_builder import RULE_NAMES, RuleBuilder
from src.exporter import exportar
from src.ingestion.data_loader import cargar_snapshot
from src.monitoring.monitor import MonitorCSV
from src.remediation.recommender import SUGGESTIONS
from src.service import ejecutar

ROOT = Path(__file__).resolve().parents[2]
ISSUE_NAMES = {**RULE_NAMES, 'faltante': 'Dato faltante', 'duplicado': 'Registro duplicado',
               'anomalia': 'Anomalía IQR', 'anomalia_multivariada': 'Anomalía multivariada (IA)'}


def preview(path, sep=None, encoding='utf-8-sig'):
    df, digest, _ = cargar_snapshot(path, sep, encoding)
    sample = df.head(20).astype(object)
    candidates, excluded = columnas_candidatas(df)
    return {'path': str(Path(path).resolve()), 'columns': list(df.columns), 'count': len(df),
            'rows': sample.where(sample.notna(), None).to_dict('records'),
            'sha256': digest, 'sep': sep, 'encoding': encoding,
            'anomaly_candidates': candidates, 'anomaly_excluded': excluded}


class MvpTask(QThread):
    success = Signal(object)
    failure = Signal(str)

    def __init__(self, function, kwargs, parent=None):
        super().__init__(parent)
        self.function = function
        self.kwargs = kwargs

    def run(self):
        try:
            self.success.emit(self.function(**self.kwargs))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.failure.emit(str(exc))
        except Exception:
            self.failure.emit('No se pudo completar la operación. Revisa el archivo, las reglas y la conexión al histórico.')


def text_label(text='', name=None):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    if name:
        label.setObjectName(name)
    return label


class MvpWindow(QMainWindow):
    def __init__(self, repo=None, demo=False, db_error='', project_root=ROOT):
        super().__init__()
        self.repo = repo
        self.project_root = Path(project_root)
        self.loaded = None
        self.report = None
        self.worker = None
        self.monitor_worker = None
        self.monitoring = False
        self.busy = False
        self.closing = False
        self.last_export = None
        self._callback = None
        self._pending_rules = []
        self._auto_analyze = False
        self.setWindowTitle('Sistema Inteligente de Calidad de Datos')
        self.resize(1240, 850)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 18, 24, 18)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(text_label('CALIDAD DE DATOS', 'title'))
        heading.addWidget(text_label('Carga un archivo, define reglas y encuentra los problemas.'))
        header.addLayout(heading, 1)
        self.demo_button = QPushButton('Probar con datos de ejemplo')
        self.demo_button.clicked.connect(self.try_demo)
        header.addWidget(self.demo_button)
        self.intelligent_demo_button = QPushButton('Probar detección inteligente')
        self.intelligent_demo_button.clicked.connect(self.try_intelligent_demo)
        header.addWidget(self.intelligent_demo_button)
        layout.addLayout(header)
        persistence = ('Histórico local de demostración' if demo else 'Histórico conectado a SQL Server') if repo else 'Histórico no disponible. Puedes analizar y exportar resultados. ' + db_error
        layout.addWidget(text_label(persistence, 'muted'))
        self.message = text_label('Comienza con tu CSV o prueba el ejemplo incluido.', 'message')
        layout.addWidget(self.message)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(5)
        layout.addWidget(self.progress)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self._build_data()
        self._build_rules()
        self._build_results()
        self._build_history()
        self.monitor_panel = MonitorPanel()
        self.monitor_panel.start_requested.connect(self.start_monitor)
        self.monitor_panel.stop_requested.connect(self.stop_monitor)
        self.tabs.addTab(self.monitor_panel, 'Tiempo real · Experimental')
        self.builder.changed.connect(self.configuration_changed)
        self.sep.currentIndexChanged.connect(self.input_options_changed)
        self.encoding.currentIndexChanged.connect(self.input_options_changed)
        self.keys.currentIndexChanged.connect(self.configuration_changed)
        self.anomalies.toggled.connect(self.configuration_changed)
        self.intelligent.toggled.connect(self.intelligence_changed)
        self.anomaly_columns.itemChanged.connect(self.configuration_changed)
        self.contamination.valueChanged.connect(self.configuration_changed)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.setStyleSheet('''
            QMainWindow, QWidget { background:#f2f5f8; color:#20334a; font-family:"Segoe UI"; font-size:13px; }
            QLabel#title { font-size:27px; font-weight:700; padding-bottom:5px; }
            QLabel#muted { color:#5c6f82; }
            QLabel#message { padding:9px 0; }
            QLabel#error { color:#a52727; }
            QLabel#value { font-size:27px; font-weight:700; }
            QFrame#card { background:white; border:1px solid #dae3ec; border-radius:8px; }
            QFrame#card QLabel { background:transparent; }
            QPushButton { background:#e1e9f1; padding:10px 16px; border:0; border-radius:5px; }
            QPushButton#primary { background:#146984; color:white; font-weight:700; }
            QPushButton:disabled, QPushButton#primary:disabled { background:#e8edf2; color:#8492a1; }
            QLineEdit, QComboBox, QPlainTextEdit { background:white; padding:7px; border:1px solid #cbd7e3; }
            QTableWidget { background:white; gridline-color:#e4ebf2; }
            QHeaderView::section { background:#e7eef5; padding:8px; border:0; }
            QTabBar::tab { padding:12px 18px; }
            QTabBar::tab:selected { background:white; color:#146984; }
            QProgressBar { background:#dce6ef; border:0; text-align:center; min-height:5px; }
            QProgressBar::chunk { background:#35a499; }
        ''')
        self.update_controls()

    def _build_data(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(text_label('1. Elige el archivo que quieres evaluar.'))
        self.data_controls = QWidget()
        controls = QVBoxLayout(self.data_controls)
        path_row = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setReadOnly(True)
        self.path.setPlaceholderText('Archivo CSV · hasta 100 000 registros y 100 MB')
        self.choose_button = QPushButton('Elegir CSV')
        self.choose_button.clicked.connect(self.choose_file)
        self.reload_button = QPushButton('Volver a cargar')
        self.reload_button.clicked.connect(self.reload_source)
        path_row.addWidget(self.path, 1)
        path_row.addWidget(self.choose_button)
        path_row.addWidget(self.reload_button)
        controls.addLayout(path_row)
        options = QHBoxLayout()
        self.sep = QComboBox()
        for label, value in [('Automático', None), ('Coma (,)', ','), ('Punto y coma (;)', ';'), ('Tabulación', '\t'), ('Barra (|)', '|')]:
            self.sep.addItem(label, value)
        self.encoding = QComboBox()
        self.encoding.addItems(['utf-8-sig', 'cp1252', 'latin-1'])
        options.addWidget(text_label('Separador'))
        options.addWidget(self.sep)
        options.addWidget(text_label('Codificación'))
        options.addWidget(self.encoding)
        options.addStretch()
        controls.addLayout(options)
        layout.addWidget(self.data_controls)
        self.preview_info = text_label('La vista previa aparecerá aquí. Se analizará el archivo completo.')
        layout.addWidget(self.preview_info)
        self.preview_table = table([])
        layout.addWidget(self.preview_table, 1)
        self.next_button = QPushButton('Continuar a las reglas')
        self.next_button.setObjectName('primary')
        self.next_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(page, '1  Datos')

    def _build_rules(self):
        self.rules_page = QWidget()
        layout = QVBoxLayout(self.rules_page)
        self.builder = RuleBuilder()
        self.builder.load_requested.connect(self.import_rules)
        self.builder.save_requested.connect(self.save_rules)
        layout.addWidget(self.builder, 1)
        options = QHBoxLayout()
        self.keys = QComboBox()
        self.keys.addItem('Fila completa', None)
        options.addWidget(text_label('Detectar duplicados por'))
        options.addWidget(self.keys, 1)
        self.anomalies = QCheckBox('Anomalías IQR')
        options.addWidget(self.anomalies)
        layout.addLayout(options)
        self.intelligent = QCheckBox('Detección inteligente · Isolation Forest')
        self.intelligent.setChecked(True)
        layout.addWidget(self.intelligent)
        self.intelligence_options = QWidget()
        ml_layout = QHBoxLayout(self.intelligence_options)
        ml_layout.setContentsMargins(0, 0, 0, 0)
        ml_layout.addWidget(text_label('Columnas numéricas\n(mínimo dos)'))
        self.anomaly_columns = QListWidget()
        self.anomaly_columns.setMaximumHeight(85)
        ml_layout.addWidget(self.anomaly_columns, 1)
        ml_layout.addWidget(text_label('Proporción estimada\nde atípicos'))
        self.contamination = QDoubleSpinBox()
        self.contamination.setRange(.1, 50)
        self.contamination.setValue(5)
        self.contamination.setSuffix(' %')
        self.contamination.setToolTip('Determina el umbral del modelo; puede marcar valores legítimos. No es una probabilidad de error.')
        ml_layout.addWidget(self.contamination)
        layout.addWidget(self.intelligence_options)
        layout.addWidget(text_label('Aprende combinaciones de valores del archivo. Requiere 20 filas completas; los hallazgos no cambian el Quality Score.'))
        self.analyze_button = QPushButton('Analizar y ver resultados')
        self.analyze_button.setObjectName('primary')
        self.analyze_button.clicked.connect(self.start_analysis)
        layout.addWidget(self.analyze_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(self.rules_page, '2  Reglas')

    def _build_results(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.result_info = text_label('Ejecuta un análisis para consultar sus resultados.')
        layout.addWidget(self.result_info)
        results = QTabWidget()
        layout.addWidget(results, 1)
        summary = QWidget()
        summary_layout = QVBoxLayout(summary)
        cards = QHBoxLayout()
        self.cards = {}
        for key, title in [('score', 'Quality Score / 100'), ('filas', 'Registros'), ('faltantes', 'Celdas faltantes'),
                           ('duplicados', 'Duplicados'), ('registros_con_errores', 'Registros con hallazgos')]:
            card = QFrame()
            card.setObjectName('card')
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(text_label(title))
            value = text_label('—', 'value')
            card_layout.addWidget(value)
            self.cards[key] = value
            cards.addWidget(card, 1)
        summary_layout.addLayout(cards)
        self.coverage = text_label('Las dimensiones evaluadas y su cobertura aparecerán después del análisis.')
        summary_layout.addWidget(self.coverage)
        self.dimensions = {}
        for name in ['completitud', 'validez', 'unicidad', 'consistencia']:
            row = QHBoxLayout()
            label = text_label(name.capitalize())
            label.setMinimumWidth(120)
            row.addWidget(label)
            progress = QProgressBar()
            progress.setRange(0, 10000)
            progress.setValue(0)
            progress.setMinimumHeight(25)
            progress.setFormat('Sin evaluar')
            row.addWidget(progress)
            self.dimensions[name] = progress
            summary_layout.addLayout(row)
        summary_layout.addWidget(text_label('Problemas principales y acciones sugeridas'))
        self.actions = table([])
        summary_layout.addWidget(self.actions, 1)
        results.addTab(summary, 'Resumen')
        self.profile = table([])
        results.addTab(self.profile, 'Perfil de columnas')
        self.rule_results = table([])
        results.addTab(self.rule_results, 'Evaluación de reglas')
        issue_page = QWidget()
        issue_layout = QVBoxLayout(issue_page)
        self.issue_filter = QLineEdit()
        self.issue_filter.setPlaceholderText('Buscar por columna, problema o recomendación')
        self.issue_filter.textChanged.connect(self.filter_issues)
        issue_layout.addWidget(self.issue_filter)
        self.issue_info = text_label('')
        issue_layout.addWidget(self.issue_info)
        self.issues = table([])
        issue_layout.addWidget(self.issues)
        results.addTab(issue_page, 'Incidencias')
        intelligence_page = QWidget()
        intelligence_layout = QVBoxLayout(intelligence_page)
        self.intelligence_info = text_label('Ejecuta la detección inteligente para ver el modelo y sus hallazgos.')
        intelligence_layout.addWidget(self.intelligence_info)
        self.intelligence_table = table([])
        intelligence_layout.addWidget(self.intelligence_table, 1)
        results.addTab(intelligence_page, 'Detección inteligente')
        self.result_tabs = results
        self.export_button = QPushButton('Exportar reporte y tablas')
        self.export_button.clicked.connect(self.choose_export)
        layout.addWidget(self.export_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(page, '3  Resultados')

    def _build_history(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(text_label('Recupera una ejecución con doble clic. Se muestran las últimas 500; cada reporte conserva sus reglas y métricas.'))
        self.refresh_button = QPushButton('Actualizar histórico')
        self.refresh_button.clicked.connect(self.refresh_history)
        layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.history = table([])
        self.history.cellDoubleClicked.connect(self.open_history)
        layout.addWidget(self.history)
        self.tabs.addTab(page, 'Histórico')

    def notify(self, message, error=False):
        self.message.setText(message)
        self.message.setStyleSheet('color:#a52727;' if error else 'color:#20334a;')

    def update_controls(self):
        available = not (self.busy or self.monitoring or self.closing)
        self.data_controls.setEnabled(available)
        self.demo_button.setEnabled(available)
        self.intelligent_demo_button.setEnabled(available)
        self.reload_button.setEnabled(bool(self.path.text()) and available)
        self.rules_page.setEnabled(self.loaded is not None and available)
        self.next_button.setEnabled(self.loaded is not None and available)
        self.export_button.setEnabled(self.report is not None and available)
        self.refresh_button.setEnabled(self.repo is not None and available)
        self.monitor_panel.start_button.setEnabled(self.loaded is not None and available)
        for control in (self.monitor_panel.interval, self.monitor_panel.stability, self.monitor_panel.threshold):
            control.setEnabled(available)

    def run_task(self, function, kwargs, callback, message):
        if self.busy or self.monitoring or self.closing:
            return False
        if self.worker:
            self.worker.deleteLater()
        self.busy = True
        self._callback = callback
        self.notify(message)
        self.progress.setRange(0, 0)
        self.update_controls()
        self.worker = MvpTask(function, kwargs, self)
        self.worker.success.connect(self.task_success)
        self.worker.failure.connect(self.task_failure)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()
        return True

    def task_success(self, result):
        try:
            self._callback(result)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            self.task_failure(str(exc))

    def task_failure(self, message):
        self._auto_analyze = False
        self.notify(message, error=True)

    def task_finished(self):
        self.busy = False
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.update_controls()
        if self.closing:
            self.close()
        elif self._auto_analyze:
            self._auto_analyze = False
            self.start_analysis()

    def clear_report(self):
        self.report = None
        self.last_export = None
        for label in self.cards.values():
            label.setText('—')
        for bar in self.dimensions.values():
            bar.setValue(0)
            bar.setFormat('Sin evaluar')
        for widget in [self.profile, self.rule_results, self.actions, self.issues, self.intelligence_table]:
            fill(widget, [])
        self.result_info.setText('Ejecuta un análisis para consultar sus resultados.')
        self.coverage.setText('Las dimensiones evaluadas y su cobertura aparecerán después del análisis.')
        self.issue_info.clear()
        self.intelligence_info.setText('Ejecuta la detección inteligente para ver el modelo y sus hallazgos.')
        self.export_button.setEnabled(False)

    def configuration_changed(self):
        had_report = self.report is not None
        self.clear_report()
        if had_report:
            self.notify('La configuración cambió. Ejecuta un nuevo análisis para actualizar los resultados.')

    def intelligence_changed(self):
        self.intelligence_options.setEnabled(self.intelligent.isChecked())
        self.configuration_changed()

    def selected_anomaly_columns(self):
        return [self.anomaly_columns.item(i).text() for i in range(self.anomaly_columns.count())
                if self.anomaly_columns.item(i).checkState() == Qt.CheckState.Checked]

    def input_options_changed(self):
        self.loaded = None
        self.clear_report()
        fill(self.preview_table, [])
        self.preview_info.setText('Vuelve a cargar el archivo con las opciones seleccionadas.')
        self.update_controls()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccionar archivo CSV', str(self.project_root / 'data/input'), 'CSV (*.csv)')
        if path:
            self.load_source(path)

    def reload_source(self):
        if self.path.text():
            self.load_source(self.path.text(), preset_rules=deepcopy(self.builder.rules))

    def load_source(self, path, preset_rules=None, auto_analyze=False):
        if self.busy or self.monitoring or self.closing:
            return
        self.loaded = None
        self.clear_report()
        self.path.setText(str(path))
        fill(self.preview_table, [])
        self.preview_info.setText('Leyendo y validando el CSV…')
        self.builder.set_columns([])
        self._pending_rules = deepcopy(preset_rules or [])
        self._auto_analyze = auto_analyze
        self.tabs.setCurrentIndex(0)
        self.run_task(preview, {'path': path, 'sep': self.sep.currentData(), 'encoding': self.encoding.currentText()},
                      self.source_loaded, 'Validando el archivo y preparando la vista previa…')

    def source_loaded(self, data):
        self.loaded = data
        self.path.setText(data['path'])
        fill(self.preview_table, data['rows'])
        self.preview_info.setText(f"{data['count']:,} registros · {len(data['columns'])} columnas · primeras {len(data['rows'])} filas. El análisis utiliza todos los registros.")
        self.builder.set_columns(data['columns'])
        self.anomaly_columns.blockSignals(True)
        self.anomaly_columns.clear()
        for column in data['anomaly_candidates']:
            item = QListWidgetItem(column)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.anomaly_columns.addItem(item)
        self.anomaly_columns.blockSignals(False)
        self.keys.blockSignals(True)
        self.keys.clear()
        self.keys.addItem('Fila completa', None)
        for column in data['columns']:
            self.keys.addItem(column, column)
        self.keys.blockSignals(False)
        self.builder.set_rules(self._pending_rules)
        self.notify('Archivo listo. Continúa a las reglas o ejecuta el ejemplo preparado.')

    def try_demo(self):
        if self.busy or self.monitoring or self.closing:
            return
        try:
            rules = json.loads((self.project_root / 'config/reglas_demo.json').read_text(encoding='utf-8-sig'))
        except (ValueError, OSError) as exc:
            self.notify(f'No se pudo cargar el ejemplo: {exc}', error=True)
            return
        for control in [self.sep, self.encoding]:
            control.blockSignals(True)
            control.setCurrentIndex(0)
            control.blockSignals(False)
        self.anomalies.setChecked(False)
        self.load_source(self.project_root / 'data/input/demo_clientes.csv', rules, auto_analyze=True)

    def try_intelligent_demo(self):
        if self.busy or self.monitoring or self.closing:
            return
        for control in [self.sep, self.encoding]:
            control.blockSignals(True)
            control.setCurrentIndex(0)
            control.blockSignals(False)
        self.intelligent.setChecked(True)
        self.anomalies.setChecked(True)
        self.contamination.setValue(5)
        self.load_source(self.project_root / 'data/input/demo_inteligente.csv', auto_analyze=True)

    def import_rules(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Cargar reglas', str(self.project_root / 'config'), 'JSON (*.json)')
        if path:
            try:
                self.builder.set_rules(json.loads(Path(path).read_text(encoding='utf-8-sig')))
                self.notify('Reglas cargadas. Revisa sus condiciones antes de analizar.')
            except (ValueError, TypeError, KeyError, OSError) as exc:
                self.notify(f'No se cargaron las reglas: {exc}', error=True)

    def save_rules(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar reglas', str(self.project_root / 'config/reglas_mvp.json'), 'JSON (*.json)')
        if path:
            try:
                Path(path).write_text(json.dumps(self.builder.rules, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                self.notify('Configuración guardada.')
            except OSError as exc:
                self.notify(f'No se pudo guardar: {exc}', error=True)

    def start_analysis(self):
        if self.busy or self.monitoring or self.closing or self.loaded is None:
            return
        data = self.loaded
        key = self.keys.currentData()
        self.clear_report()
        self.run_task(ejecutar, {'path': data['path'], 'rules': deepcopy(self.builder.rules), 'repo': self.repo,
                                'keys': [key] if key is not None else [], 'anomalies': self.anomalies.isChecked(),
                                'intelligent': self.intelligent.isChecked(),
                                'anomaly_columns': self.selected_anomaly_columns(), 'contamination': self.contamination.value() / 100,
                                'sep': data['sep'], 'encoding': data['encoding'], 'expected_sha256': data['sha256']},
                      self.show_report, 'Analizando calidad y guardando resultados…')

    def show_report(self, report, navigate=True):
        self.report = report
        self.last_export = None
        for key, label in self.cards.items():
            value = report.get(key)
            label.setText('N/D' if value is None else f'{value:.2f}' if key == 'score' else f'{value:,}')
        saved = 'Guardado en histórico.' if report.get('guardado') else 'Sin guardar en histórico; puedes exportar el reporte.'
        self.result_info.setText(f"{report['fuente']} · {report['fecha']} · {report['segundos']:.3f} s de análisis. {saved}")
        verdict = 'Evaluación parcial' if report['cobertura'] < 100 else report['alerta'].capitalize()
        self.coverage.setText(f"{verdict} · Cobertura del score: {report['cobertura']}%. "
                              'Las dimensiones sin evaluaciones no se incluyen en el score. Las anomalías son indicios y no cambian la puntuación.')
        for name, bar in self.dimensions.items():
            value = report['metricas'][name]
            bar.setValue(round(value * 100) if value is not None else 0)
            bar.setFormat(f'{value:.2f}%' if value is not None else 'N/D · sin evaluaciones')
        findings = sorted(((kind, count) for kind, count in report['conteos'].items() if count), key=lambda item: item[1], reverse=True)
        fill(self.actions, [{'Problema': ISSUE_NAMES.get(kind, kind), 'Hallazgos': count,
                             'Acción sugerida': SUGGESTIONS[kind]} for kind, count in findings[:5]])
        fill(self.profile, report['perfil'])
        fill(self.rule_results, [{'Regla': r['id'], 'Columna': r['columna'], 'Validación': RULE_NAMES.get(r['tipo'], r['tipo']),
                                 'Evaluados': r['evaluados'], 'Fallos': r['fallos'], 'Omitidos': r['omitidos']}
                                for r in report['resultados_reglas']])
        self.filter_issues()
        self.show_intelligence(report.get('inteligencia', {}))
        if navigate:
            self.tabs.setCurrentIndex(2)
        self.notify(report.get('error_bd') or f'Análisis completo. {saved}', error=bool(report.get('error_bd')))
        self.update_controls()

    def show_intelligence(self, info):
        fill(self.intelligence_table, [])
        if not info.get('activo'):
            self.intelligence_info.setText('Detección inteligente desactivada o no incluida en este reporte histórico.')
            return
        if info['estado'] != 'evaluado':
            self.intelligence_info.setText('No evaluado · ' + info['motivo'])
            return
        params = info['parametros']
        limit = ' El detalle muestra solo una parte; el conteo es completo.' if info['detalle_limitado'] else ''
        self.intelligence_info.setText(
            f"Isolation Forest · {info['anomalias']} registros atípicos de {info['filas_evaluadas']} evaluados; "
            f"{info['filas_omitidas']} omitidos. Columnas: {', '.join(info['columnas'])}.\n"
            f"Proporción estimada: {params['contamination']:.1%} · árboles: {params['n_estimators']} · "
            f"semilla: {params['random_state']} · scikit-learn {info['version_sklearn']}.\n"
            'Mayor puntuación = más atípico; decisión menor que cero = señalado. No es probabilidad de error. '
            'Se aprende de cada lote y se requiere revisión humana.' + limit)
        fill(self.intelligence_table, [
            {'Registro': row['registro'], 'Puntuación de anomalía': round(row['puntuacion_anomalia'], 6),
             'Decisión': round(row['decision'], 6),
             'Valores observados': ', '.join(f'{c}: {v:g}' for c, v in row['valores'].items())}
            for row in info['resultados']])

    def filter_issues(self):
        if self.report is None:
            return
        query = self.issue_filter.text().casefold()
        rows = [{'Registro': item['registro'], 'Problema': ISSUE_NAMES.get(item['tipo'], item['tipo']),
                 'Columna': item['columna'], 'Regla': item['regla'], 'Detalle': item['detalle'],
                 'Recomendación': item['recomendacion']} for item in self.report['incidencias']]
        visible = [row for row in rows if query in str(row).casefold()]
        fill(self.issues, visible)
        limitation = 'El detalle está limitado a 2 000 incidencias; los conteos son completos.' if self.report['muestra_limitada'] else 'Se incluye todo el detalle de esta ejecución.'
        self.issue_info.setText(f'{len(visible)} visibles de {len(rows)} incidencias disponibles. {limitation}')

    def choose_export(self):
        folder = QFileDialog.getExistingDirectory(self, 'Carpeta para el reporte', str(self.project_root / 'reports'))
        if folder:
            self.export_to(folder)

    def export_to(self, folder):
        if self.report is not None:
            self.run_task(exportar, {'report': self.report, 'folder': folder}, self.exported, 'Exportando reporte y tablas…')

    def exported(self, destination):
        self.last_export = destination
        self.notify(f'Reporte JSON y tablas CSV guardados en {destination}')

    def tab_changed(self, index):
        if index == 3 and not self.busy and not self.monitoring and self.repo is not None:
            self.refresh_history()

    def refresh_history(self):
        if self.repo is not None:
            self.run_task(self.repo.history, {}, self.history_loaded, 'Consultando histórico…')

    def history_loaded(self, rows):
        fill(self.history, [{'Id': r['id'], 'Fecha UTC': r['fecha'], 'Archivo': r['nombre'],
                             'Registros': r['filas'], 'Score': r['score']} for r in rows])
        if rows:
            self.history.setColumnHidden(0, True)
        self.notify(f'{len(rows)} ejecuciones disponibles. Haz doble clic para consultar un reporte.')

    def open_history(self, row, column=0):
        item = self.history.item(row, 0)
        if item is not None and self.repo is not None:
            self.run_task(self.repo.load, {'run_id': item.text()}, self.show_report, 'Recuperando reporte…')

    def closeEvent(self, event):
        if self.monitoring:
            self.closing = True
            self.stop_monitor()
            event.ignore()
        elif self.busy:
            self.closing = True
            self.notify('Finalizando la operación en curso antes de cerrar…')
            event.ignore()
        else:
            event.accept()

    def start_monitor(self):
        if self.busy or self.monitoring or self.closing or self.loaded is None:
            return
        data = self.loaded
        key = self.keys.currentData()
        try:
            monitor = MonitorCSV(data['path'], deepcopy(self.builder.rules), self.repo,
                                 keys=[key] if key is not None else [], anomalies=self.anomalies.isChecked(),
                                 intelligent=self.intelligent.isChecked(), anomaly_columns=self.selected_anomaly_columns(),
                                 contamination=self.contamination.value() / 100,
                                 sep=data['sep'], encoding=data['encoding'],
                                 interval=self.monitor_panel.interval.value(),
                                 stable_seconds=self.monitor_panel.stability.value(),
                                 threshold=self.monitor_panel.threshold.value())
        except (ValueError, TypeError, KeyError) as exc:
            self.notify(str(exc), error=True)
            return
        self.monitoring = True
        self.monitor_panel.clear_session()
        self.monitor_panel.set_running(True)
        self.update_controls()
        if self.monitor_worker:
            self.monitor_worker.deleteLater()
        self.monitor_worker = MonitorWorker(monitor, self)
        self.monitor_worker.update.connect(self.monitor_update)
        self.monitor_worker.finished.connect(self.monitor_done)
        self.monitor_worker.start()
        self.notify('Monitoreo activo. Cada versión estable actualizará los resultados.')

    def stop_monitor(self):
        if self.monitoring:
            self.monitor_worker.stop()
            self.monitor_panel.stop_button.setEnabled(False)
            self.monitor_panel.status.setText('Deteniendo; esperando que finalice el análisis en curso…')

    def monitor_update(self, event):
        self.monitor_panel.show_event(event)
        if event.get('reporte') is not None:
            self.show_report(event['reporte'], navigate=False)

    def monitor_done(self):
        self.monitoring = False
        self.monitor_panel.set_running(False)
        self.monitor_panel.status.setText('Detenido · ' + self.monitor_panel.status.text())
        self.update_controls()
        self.notify('Monitoreo detenido. Si el CSV cambió, vuelve a cargarlo antes de un análisis manual.')
        if self.closing:
            self.close()


def launch(repo=None, demo=False, db_error=''):
    app = QApplication.instance() or QApplication([])
    window = MvpWindow(repo, demo, db_error)
    window.show()
    return app.exec()
