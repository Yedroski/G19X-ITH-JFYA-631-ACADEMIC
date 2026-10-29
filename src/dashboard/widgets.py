"""Tablas compartidas de la interfaz de escritorio."""
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem


def table(rows):
    widget = QTableWidget()
    fill(widget, rows)
    return widget


def fill(widget, rows):
    widget.clear()
    widget.setRowCount(len(rows))
    widget.setColumnCount(len(rows[0]) if rows else 0)
    if rows:
        widget.setHorizontalHeaderLabels(list(rows[0]))
        for i, row in enumerate(rows):
            for j, value in enumerate(row.values()):
                widget.setItem(i, j, QTableWidgetItem('N/D' if value is None else str(value)))
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
