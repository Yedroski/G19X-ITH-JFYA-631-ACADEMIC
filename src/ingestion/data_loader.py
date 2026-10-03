import os
import pandas as pd


def cargar_csv(ruta_archivo):
    """
    Carga cualquier archivo CSV desde una ruta local.
    Devuelve un DataFrame de Pandas.
    """

    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta_archivo}"
        )

    if not os.path.isfile(ruta_archivo):
        raise ValueError(
            f"La ruta indicada no corresponde a un archivo: {ruta_archivo}"
        )

    if not ruta_archivo.lower().endswith(".csv"):
        raise ValueError(
            "El archivo seleccionado no tiene extensión .csv"
        )

    try:
        df = pd.read_csv(ruta_archivo)

        print("\nArchivo cargado correctamente.")
        print(f"Archivo: {os.path.basename(ruta_archivo)}")
        print(f"Registros: {len(df):,}")
        print(f"Columnas: {len(df.columns)}")

        return df

    except pd.errors.EmptyDataError:
        raise ValueError(
            "El archivo CSV está vacío."
        )

    except pd.errors.ParserError as error:
        raise ValueError(
            f"No se pudo interpretar correctamente el CSV: {error}"
        )

    except UnicodeDecodeError as error:
        raise ValueError(
            f"Problema de codificación del archivo: {error}"
        )