"""Perfilado descriptivo sin modificar los valores originales."""
import math

import pandas as pd


def _finite(value):
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else None


def perfilar(df):
    result = []
    for col in df:
        s = df[col]
        nonnull = s.dropna().astype('string')
        num = pd.to_numeric(nonnull, errors='coerce')
        finite = num.replace([float('inf'), float('-inf')], float('nan')).dropna()
        numeric_count = int(num.notna().sum())
        date_count = int(pd.to_datetime(nonnull, format='%Y-%m-%d', errors='coerce').notna().sum())
        bool_count = int(nonnull.str.lower().isin(['true', 'false', 'sí', 'si', 'no']).sum())
        kind, count = max([('numérico', numeric_count), ('fecha ISO', date_count), ('booleano', bool_count)], key=lambda item: item[1])
        if not len(nonnull) or count <= len(nonnull) / 2:
            kind = 'texto' if len(nonnull) else 'sin datos'
        numeric = kind == 'numérico' and not finite.empty
        result.append({
            'columna': str(col), 'tipo_inferido': kind, 'filas': len(s),
            'faltantes': int(s.isna().sum()),
            'porcentaje_nulos': round(100 * s.isna().mean(), 2) if len(s) else 0,
            'completitud': round(100 * s.notna().mean(), 2) if len(s) else 0,
            'distintos': int(s.nunique()), 'valores_numericos': len(finite),
            'mínimo': _finite(finite.min()) if numeric else None,
            'máximo': _finite(finite.max()) if numeric else None,
            'media': _finite(finite.mean()) if numeric else None,
            'desviacion': _finite(finite.std()) if numeric else None,
            'q25': _finite(finite.quantile(.25)) if numeric else None,
            'mediana': _finite(finite.median()) if numeric else None,
            'q75': _finite(finite.quantile(.75)) if numeric else None,
            'ejemplos': ' | '.join(str(v)[:80] for v in nonnull.unique()[:5]),
            'frecuentes': ' | '.join(f'{str(v)[:80]}: {n}' for v, n in nonnull.value_counts().head(5).items()),
        })
    return result


def perfil_general(df):
    return {'filas': len(df), 'columnas': len(df.columns), 'duplicados': int(df.duplicated().sum())}


def perfil_columnas(df):
    return pd.DataFrame([{'columna': p['columna'], 'tipo': p['tipo_inferido'],
                          'nulos': p['faltantes'], 'porcentaje_nulos': p['porcentaje_nulos'],
                          'valores_unicos': p['distintos']} for p in perfilar(df)])


def estadisticas_numericas(df):
    numeric = df.apply(pd.to_numeric, errors='coerce').replace([float('inf'), float('-inf')], float('nan')).dropna(axis=1, how='all')
    return numeric.describe().transpose() if not numeric.empty else pd.DataFrame()
