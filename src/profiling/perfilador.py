import pandas as pd


def perfil_general(df):
    """
    Genera un perfil general del DataFrame.
    """

    total_filas = len(df)
    total_columnas = len(df.columns)
    duplicados = df.duplicated().sum()

    print("\n========== PERFIL GENERAL ==========")
    print(f"Filas: {total_filas:,}")
    print(f"Columnas: {total_columnas}")
    print(f"Registros duplicados: {duplicados:,}")

    return {
        "filas": total_filas,
        "columnas": total_columnas,
        "duplicados": duplicados
    }


def perfil_columnas(df):
    """
    Genera métricas básicas para cada columna.
    """

    resultados = []

    for columna in df.columns:
        total = len(df)
        nulos = df[columna].isna().sum()
        porcentaje_nulos = (nulos / total * 100) if total > 0 else 0
        unicos = df[columna].nunique(dropna=True)

        resultado = {
            "columna": columna,
            "tipo": str(df[columna].dtype),
            "nulos": int(nulos),
            "porcentaje_nulos": round(porcentaje_nulos, 2),
            "valores_unicos": int(unicos)
        }

        resultados.append(resultado)

    return pd.DataFrame(resultados)

def estadisticas_numericas(df):
    """
    Genera estadísticas descriptivas para columnas numéricas.
    """

    columnas_numericas = df.select_dtypes(
        include="number"
    )

    if columnas_numericas.empty:
        return pd.DataFrame()

    return columnas_numericas.describe().transpose()
"""Alias del módulo de perfilado usado por el proyecto de Visual Studio."""
from src.profiling.profiler import (
    estadisticas_numericas, perfil_columnas, perfil_general, perfilar,
)

__all__ = ['estadisticas_numericas', 'perfil_columnas', 'perfil_general', 'perfilar']
