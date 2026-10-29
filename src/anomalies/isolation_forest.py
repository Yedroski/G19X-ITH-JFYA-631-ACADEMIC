"""Detección multivariada no supervisada; nunca modifica datos ni Quality Score."""
import math
import re

import numpy as np
import pandas as pd

MIN_ROWS = 20
DEFAULT_CONTAMINATION = .05


def columnas_candidatas(df, exclude=()):
    """Selección conservadora y explicable; el usuario puede elegir columnas."""
    included, excluded = [], {}
    for column in df:
        name = str(column)
        values = df[column].dropna().astype('string').str.strip()
        numbers = pd.to_numeric(values, errors='coerce')
        if column in exclude or re.search(r'(^|_)(id|codigo|código|folio|cp|zip)($|_)', name.casefold()):
            reason = 'Identificador o clave; no se usa como magnitud.'
        elif values.str.match(r'^0\d+$').any():
            reason = 'Posible identificador con ceros iniciales.'
        elif values.empty or numbers.isna().any():
            reason = 'Contiene texto no numérico o no tiene datos.'
        elif not np.isfinite(numbers.to_numpy(dtype=float)).all():
            reason = 'Contiene valores no finitos.'
        elif numbers.nunique() < 2:
            reason = 'Columna constante.'
        else:
            included.append(name)
            continue
        excluded[name] = reason
    return included, excluded


def detectar_isolation_forest(df, columns=None, contamination=DEFAULT_CONTAMINATION,
                              exclude=(), sample_limit=2000):
    """Ajusta y evalúa cada snapshot. Devuelve máscara completa y evidencia acotada.

    Solo filas completas y finitas; sin imputación. La decisión negativa identifica
    un atípico relativo a este lote, no una probabilidad ni un error confirmado.
    """
    if isinstance(contamination, bool) or not isinstance(contamination, (int, float)) or not math.isfinite(contamination) or not 0 < contamination <= .5:
        raise ValueError('La fracción estimada de anomalías debe ser mayor que 0 y hasta 0.5.')
    if isinstance(sample_limit, bool) or not isinstance(sample_limit, int) or sample_limit < 0:
        raise ValueError('El límite de detalles debe ser un entero no negativo.')
    candidates, excluded = columnas_candidatas(df, exclude)
    if columns is not None:
        if isinstance(columns, str) or len(set(columns)) != len(columns):
            raise ValueError('Selecciona columnas distintas para Isolation Forest.')
        if any(column not in df.columns for column in columns):
            raise ValueError('Hay columnas de Isolation Forest que no existen en el CSV.')
        selected = list(columns)
        excluded = {str(c): 'No seleccionada por el usuario.' for c in df if c not in selected}
    else:
        selected = candidates
    parameters = {'n_estimators': 200, 'max_samples': min(256, len(df)),
                  'contamination': float(contamination), 'random_state': 42, 'n_jobs': 1}
    result = {'activo': True, 'metodo': 'IsolationForest', 'estado': 'no_evaluable',
              'motivo': '', 'columnas': selected, 'columnas_excluidas': excluded,
              'seleccion': 'manual' if columns is not None else 'automatica',
              'filas_evaluadas': 0, 'filas_omitidas': len(df), 'minimo_filas': MIN_ROWS,
              'parametros': parameters, 'version_sklearn': None,
              'umbral_score_samples': None, 'anomalias': 0, 'resultados': [],
              'detalle_limitado': False,
              'preprocesamiento': 'Filas completas finitas; escala por máximo absoluto de cada columna; sin imputación.'}
    mask = pd.Series(False, index=df.index)
    if len(selected) < 2:
        result['motivo'] = 'Se necesitan al menos dos columnas numéricas variables.'
        return mask, result
    numeric = df[selected].apply(pd.to_numeric, errors='coerce').astype(float)
    complete = np.isfinite(numeric.to_numpy()).all(axis=1)
    positions = np.flatnonzero(complete)
    valid = numeric.iloc[positions]
    if len(valid) < MIN_ROWS:
        result['motivo'] = f'Se necesitan al menos {MIN_ROWS} filas completas y finitas; hay {len(valid)}.'
        return mask, result
    if (valid.nunique() < 2).any():
        result['motivo'] = 'Hay columnas constantes entre las filas completas; cambia la selección.'
        return mask, result
    from sklearn import __version__
    from sklearn.ensemble import IsolationForest

    # Evita overflow al convertir internamente a float32, sin alterar la fuente.
    scales = valid.abs().max()
    matrix = (valid / scales).to_numpy(dtype=np.float32)
    parameters['max_samples'] = min(256, len(valid))
    model = IsolationForest(**parameters).fit(matrix)
    scores = model.score_samples(matrix)
    decision = scores - model.offset_
    flagged = np.flatnonzero(decision < 0)
    mask.iloc[positions[flagged]] = True
    ranked = flagged[np.argsort(decision[flagged], kind='stable')]
    result.update(estado='evaluado', motivo='Atípicos relativos al lote; requieren revisión humana.',
                  filas_evaluadas=len(valid), filas_omitidas=len(df) - len(valid),
                  version_sklearn=__version__, umbral_score_samples=float(model.offset_),
                  escalas={str(c): float(scales[c]) for c in selected},
                  anomalias=len(flagged), detalle_limitado=len(flagged) > sample_limit)
    result['resultados'] = [
        {'registro': int(positions[i]) + 1, 'puntuacion_anomalia': float(-scores[i]),
         'decision': float(decision[i]),
         'valores': {str(c): float(valid.iloc[i][c]) for c in selected}}
        for i in ranked[:sample_limit]
    ]
    return mask, result
