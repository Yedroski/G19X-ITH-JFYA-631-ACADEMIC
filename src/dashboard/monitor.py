"""Presentación Qt del monitor experimental; procesamiento en un solo hilo."""
from threading import Event

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView, QHeaderView,
)

from src.monitoring.monitor import MonitorCSV


class MonitorWorker(QThread):
    update = Signal(object)

    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            for event in self.monitor.events(self.stop_event):
                self.update.emit(event)
        except Exception:
            self.update.emit(MonitorCSV.event('error', 'El monitor se detuvo por un error inesperado. Reinícialo para reintentar.'))


class MonitorPanel(QWidget):
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        description = QLabel('EXPERIMENTAL · Monitoreo de cambios en CSV\n'
                             'Selecciona el archivo en Datos y configura sus Reglas. Se analiza cada versión estable '
                             'del archivo completo. El dashboard se actualiza automáticamente. Detén el monitor para cambiar la configuración.')
        description.setWordWrap(True)
        layout.addWidget(description)
        options = QHBoxLayout()
        self.interval = QDoubleSpinBox()
        self.interval.setRange(.1, 3600)
        self.interval.setValue(2)
        self.interval.setSuffix(' s')
        self.stability = QDoubleSpinBox()
        self.stability.setRange(.1, 3600)
        self.stability.setValue(1)
        self.stability.setSuffix(' s')
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0, 100)
        self.threshold.setValue(90)
        for label, control in [('Consultar cada', self.interval), ('Estabilidad mínima', self.stability), ('Alertar bajo', self.threshold)]:
            options.addWidget(QLabel(label))
            options.addWidget(control)
        self.start_button = QPushButton('Iniciar monitoreo')
        self.start_button.clicked.connect(self.start_requested.emit)
        self.stop_button = QPushButton('Detener')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        options.addWidget(self.start_button)
        options.addWidget(self.stop_button)
        layout.addLayout(options)
        self.status = QLabel('Detenido · sin observaciones en esta sesión')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.latest = QLabel('Sin resultados. Las alertas son locales; no se envían notificaciones externas.')
        self.latest.setWordWrap(True)
        layout.addWidget(self.latest)
        self.timeline = QTableWidget(0, 7)
        self.timeline.setHorizontalHeaderLabels(['Fecha UTC', 'Score', 'Cobertura %', 'Registros', 'Con hallazgos', 'Alerta', 'Guardado'])
        self.timeline.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.timeline.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.timeline.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.timeline)
        layout.addWidget(QLabel('Se muestran las últimas 100 versiones de la sesión. Histórico conserva las ejecuciones guardadas.'))

    def set_running(self, running):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        for control in (self.interval, self.stability, self.threshold):
            control.setEnabled(not running)

    def clear_session(self):
        self.timeline.setRowCount(0)
        self.latest.setText('Esperando la primera versión estable del CSV.')

    def show_event(self, event):
        self.status.setText(f"{event['fecha']} · {event['estado']} · {event['mensaje']}")
        self.status.setStyleSheet('color:#a32020;' if event['estado'] == 'error' else '')
        report = event.get('reporte')
        if report is None:
            return
        values = [report['fecha'], f"{report['score']:.2f}", report['cobertura'], report['filas'],
                  report['registros_con_errores'], report['alerta'], 'Sí' if report['guardado'] else 'No']
        self.timeline.insertRow(0)
        for column, value in enumerate(values):
            self.timeline.setItem(0, column, QTableWidgetItem(str(value)))
        if self.timeline.rowCount() > 100:
            self.timeline.removeRow(100)
        self.latest.setText(f"Último análisis: {report['fecha']} · {event['mensaje']}. " + report.get('error_bd', ''))
        self.latest.setStyleSheet('color:#a32020; font-weight:bold;' if report['alerta'] == 'REVISAR' else '')
