"""CSV genérico y snapshots coherentes de archivos locales."""
import csv
import hashlib
import io
from pathlib import Path

import pandas as pd

MAX_BYTES = 100 * 1024 * 1024
MAX_ROWS = 100_000


class ArchivoEnCambio(ValueError):
    """La fuente cambió durante la lectura; el monitor debe reintentar."""


def firma_archivo(path):
    stat = Path(path).stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def cargar_snapshot(ruta_archivo, separador=None, encoding='utf-8-sig'):
    path = Path(ruta_archivo)
    if not path.is_file():
        raise ValueError(f'No existe el archivo: {path}')
    if path.suffix.lower() != '.csv':
        raise ValueError('El prototipo admite archivos .csv.')
    before = firma_archivo(path)
    if before[2] > MAX_BYTES:
        raise ValueError('El límite del prototipo es 100 MB por archivo.')
    with path.open('rb') as file:
        content = file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError('El límite del prototipo es 100 MB por archivo.')
    if before != firma_archivo(path):
        raise ArchivoEnCambio('El archivo está cambiando; se reintentará cuando esté estable.')
    try:
        text = content.decode(encoding)
        if not text.strip():
            raise ValueError('El archivo está vacío.')
        if not separador:
            try:
                separador = csv.Sniffer().sniff(text[:65536], delimiters=',;\t|').delimiter
            except csv.Error:
                separador = ','
        if len(separador) != 1:
            raise ValueError('El separador debe ser un carácter.')
        reader = csv.reader(io.StringIO(text, newline=''), delimiter=separador, strict=True)
        headers = next(reader)
        if not headers or any(not h.strip() for h in headers) or len(set(headers)) != len(headers):
            raise ValueError('Los encabezados deben ser únicos y no vacíos.')
        count = 0
        for number, row in enumerate(reader, start=2):
            if row:
                count += 1
                if len(row) != len(headers):
                    raise ValueError(f'Registro CSV {number}: se esperaban {len(headers)} campos, llegaron {len(row)}.')
                if count > MAX_ROWS:
                    raise ValueError('El límite del prototipo es 100 000 registros por archivo.')
        df = pd.read_csv(io.StringIO(text), sep=separador, dtype='string',
                         keep_default_na=False, on_bad_lines='error')
        if df.empty:
            raise ValueError('El CSV no contiene registros.')
        # Solo vacío/espacios son faltantes; NA y NULL permanecen literales.
        df = df.replace(r'^\s*$', pd.NA, regex=True)
        return df, hashlib.sha256(content).hexdigest(), before
    except UnicodeDecodeError as exc:
        raise ValueError('Codificación incorrecta. Prueba cp1252 en las opciones.') from exc
    except LookupError as exc:
        raise ValueError('Codificación no soportada.') from exc
    except (pd.errors.ParserError, csv.Error) as exc:
        raise ValueError('CSV mal formado. Revisa separador y número de campos.') from exc


def cargar_csv(ruta_archivo, separador=None, encoding='utf-8-sig'):
    return cargar_snapshot(ruta_archivo, separador, encoding)[0]
