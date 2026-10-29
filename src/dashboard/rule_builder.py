"""Configuración visual de reglas; la validación pertenece al motor común."""
from copy import deepcopy
import uuid

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from src.dashboard.widgets import fill, table
from src.quality.rules import validar_reglas

RULE_NAMES = {
    'required': 'Campo obligatorio', 'unique': 'Valor único', 'range': 'Rango numérico',
    'allowed': 'Valores permitidos', 'regex': 'Formato de texto',
    'date': 'Fecha válida', 'compare': 'Comparación entre columnas',
}


def describe_rule(rule):
    kind = rule['type']
    if kind == 'range':
        return f"Desde {rule.get('min', 'sin límite')} hasta {rule.get('max', 'sin límite')}"
    if kind == 'allowed':
        return ', '.join(map(str, rule['values']))
    if kind == 'regex':
        return rule['pattern']
    if kind == 'date':
        return rule['format']
    if kind == 'compare':
        suffix = f" (fechas: {rule['format']})" if rule.get('value_type') == 'date' else ''
        return f"{rule['column']} {rule['op']} {rule['other']}{suffix}"
    return 'Debe tener un valor' if kind == 'required' else 'No debe repetirse'


class RuleBuilder(QWidget):
    changed = Signal()
    load_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        self.columns = []
        layout = QVBoxLayout(self)
        intro = QLabel('Define qué significa un dato correcto para tu archivo. Puedes agregar reglas o cargar una configuración existente.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        self.column = QComboBox()
        self.kind = QComboBox()
        for label, code in [
            ('Campo obligatorio', 'required'), ('Valor único', 'unique'),
            ('Rango numérico', 'range'), ('Valores permitidos', 'allowed'),
            ('Correo electrónico', 'email'), ('Fecha válida', 'date'),
            ('Comparar números', 'compare'), ('Comparar fechas', 'date_compare'),
            ('Formato de texto (expresión regular)', 'regex'),
        ]:
            self.kind.addItem(label, code)
        form.addRow('Columna', self.column)
        form.addRow('Validación', self.kind)
        layout.addLayout(form)
        self.parameters = QStackedWidget()
        self.pages = {}
        for code in ['required', 'unique', 'range', 'allowed', 'email', 'date', 'compare', 'date_compare', 'regex']:
            page = QWidget()
            page_form = QFormLayout(page)
            self.pages[code] = self.parameters.addWidget(page)
            if code in {'required', 'unique', 'email'}:
                text = {'required': 'Marca los registros donde el campo esté vacío.',
                        'unique': 'Marca todos los valores no vacíos que se repitan.',
                        'email': 'Comprueba la estructura del correo. No verifica si la dirección existe.'}[code]
                label = QLabel(text)
                label.setWordWrap(True)
                page_form.addRow(label)
            elif code == 'range':
                self.minimum = QLineEdit()
                self.maximum = QLineEdit()
                self.minimum.setPlaceholderText('Ejemplo: 18; vacío = sin límite')
                self.maximum.setPlaceholderText('Ejemplo: 100; vacío = sin límite')
                page_form.addRow('Mínimo', self.minimum)
                page_form.addRow('Máximo', self.maximum)
            elif code == 'allowed':
                self.values = QPlainTextEdit()
                self.values.setPlaceholderText('Un valor por línea, por ejemplo:\npagado\npendiente\ncancelado')
                self.values.setMaximumHeight(90)
                page_form.addRow('Valores aceptados', self.values)
            elif code == 'date':
                self.date_format = self.format_control()
                page_form.addRow('Formato de fecha', self.date_format)
            elif code in {'compare', 'date_compare'}:
                other = QComboBox()
                operator = QComboBox()
                operator.addItems(['<=', '>=', '=='])
                setattr(self, code + '_other', other)
                setattr(self, code + '_op', operator)
                page_form.addRow('Relación', operator)
                page_form.addRow('Con la columna', other)
                if code == 'date_compare':
                    self.compare_format = self.format_control()
                    page_form.addRow('Formato de ambas fechas', self.compare_format)
            else:
                self.pattern = QLineEdit()
                self.pattern.setPlaceholderText('Ejemplo: [A-Z]{3}[0-9]{4}')
                page_form.addRow('Expresión regular', self.pattern)
        layout.addWidget(self.parameters)
        self.kind.currentIndexChanged.connect(self.change_kind)
        actions = QHBoxLayout()
        self.add_button = QPushButton('Agregar regla')
        self.add_button.clicked.connect(self.add_rule)
        self.remove_button = QPushButton('Quitar seleccionadas')
        self.remove_button.clicked.connect(self.remove_selected)
        self.load_button = QPushButton('Cargar reglas')
        self.load_button.clicked.connect(self.load_requested.emit)
        self.save_button = QPushButton('Guardar reglas')
        self.save_button.clicked.connect(self.save_requested.emit)
        for button in [self.add_button, self.remove_button, self.load_button, self.save_button]:
            actions.addWidget(button)
        layout.addLayout(actions)
        self.error = QLabel('')
        self.error.setObjectName('error')
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        self.summary = QLabel('')
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = table([])
        layout.addWidget(self.table, 1)
        self.render()

    @staticmethod
    def format_control():
        control = QComboBox()
        control.setEditable(True)
        control.addItems(['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'])
        return control

    def change_kind(self):
        self.parameters.setCurrentIndex(self.pages[self.kind.currentData()])
        self.error.clear()

    def set_columns(self, columns):
        self.columns = list(columns)
        for combo in [self.column, self.compare_other, self.date_compare_other]:
            combo.clear()
            combo.addItems(self.columns)
        self.rules = []
        self.render()
        self.changed.emit()

    def set_rules(self, rules):
        # Validar antes de reemplazar una configuración que ya funciona.
        normalized = validar_reglas(rules, self.columns)
        self.rules = deepcopy(normalized)
        self.error.clear()
        self.render()
        self.changed.emit()

    def build_rule(self):
        kind = self.kind.currentData()
        rule = {'id': 'MVP_' + uuid.uuid4().hex[:10], 'column': self.column.currentText(), 'type': kind}
        if kind == 'range':
            for field, name in [(self.minimum, 'min'), (self.maximum, 'max')]:
                if field.text().strip():
                    try:
                        rule[name] = float(field.text().strip())
                    except ValueError as exc:
                        raise ValueError('Escribe límites numéricos; usa punto para los decimales.') from exc
        elif kind == 'allowed':
            rule['values'] = [value.strip() for value in self.values.toPlainText().splitlines() if value.strip()]
            if not rule['values']:
                raise ValueError('Agrega al menos un valor permitido.')
        elif kind == 'email':
            rule.update(type='regex', pattern=r'[^\s@]+@[^\s@]+\.[^\s@]+')
        elif kind == 'regex':
            rule['pattern'] = self.pattern.text()
            if not rule['pattern']:
                raise ValueError('Escribe la expresión regular que debe cumplir el campo.')
        elif kind == 'date':
            rule['format'] = self.date_format.currentText().strip()
        elif kind in {'compare', 'date_compare'}:
            rule.update(type='compare', other=getattr(self, kind + '_other').currentText(),
                        op=getattr(self, kind + '_op').currentText(), dimension='consistencia')
            if kind == 'date_compare':
                rule.update(value_type='date', format=self.compare_format.currentText().strip())
        return validar_reglas([rule], self.columns)[0]

    def add_rule(self):
        try:
            self.rules.append(self.build_rule())
        except (ValueError, TypeError, KeyError) as exc:
            self.error.setText(str(exc))
            return
        self.error.clear()
        self.render()
        self.changed.emit()

    def remove_selected(self):
        selected = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not selected:
            self.error.setText('Selecciona una regla en la tabla para quitarla.')
            return
        for index in selected:
            del self.rules[index]
        self.error.clear()
        self.render()
        self.changed.emit()

    def render(self):
        fill(self.table, [{'Columna': rule['column'], 'Validación': RULE_NAMES[rule['type']],
                           'Condición': describe_rule(rule)} for rule in self.rules])
        self.summary.setText(f'{len(self.rules)} reglas configuradas.' if self.rules else
                             'Sin reglas se evalúan completitud y unicidad; la cobertura del score será del 50%.')
