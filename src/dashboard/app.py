"""Alias de importación para la única interfaz de escritorio vigente."""
from src.dashboard.mvp import MvpWindow as Window, launch
from src.dashboard.widgets import fill, table

__all__ = ['Window', 'launch', 'fill', 'table']
