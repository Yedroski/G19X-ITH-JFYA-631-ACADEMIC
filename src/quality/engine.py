from datetime import datetime, timezone
import hashlib
import json
import time
import uuid
import pandas as pd
from src.profiling.profiler import perfilar
from src.quality.rules import validar_reglas, evaluar
from src.anomalies.detector import detectar_iqr
from src.remediation.recommender import SUGGESTIONS

WEIGHTS = {'completitud': .30, 'validez': .30, 'unicidad': .20, 'consistencia': .20}


def analizar(df, rules=None, source='memoria', keys=None, anomalies=False, sample_limit=2000):
    start = time.perf_counter(); keys = keys or []
    if df.empty or not len(df.columns):
        raise ValueError('No hay datos para analizar.')
    df = df.reset_index(drop=True).replace(r'^\s*$', pd.NA, regex=True)
    rules = validar_reglas(rules, df.columns)
    if any(k not in df.columns for k in keys):
        raise ValueError('Hay claves de duplicados que no existen en el CSV.')
    issues = []; summaries = []; totals = {}; n = len(df)
    affected = pd.Series(False, index=df.index)
    def add(kind, column, mask, rid='', detail=''):
        affected.loc[mask.fillna(False)] = True
        count = int(mask.sum()); totals[kind] = totals.get(kind, 0) + count
        # Muestras por hallazgo, acotadas globalmente. Conteos siempre completos.
        for idx in mask[mask].index[:max(0, sample_limit-len(issues))]:
            issues.append({'registro': int(df.index.get_loc(idx))+1, 'tipo': kind,
                           'columna': column, 'regla': rid, 'detalle': detail,
                           'recomendacion': SUGGESTIONS[kind]})
    missing = int(df.isna().sum().sum())
    for col in df:
        add('faltante', str(col), df[col].isna())
    dup = df.duplicated(subset=keys or None, keep='first')
    add('duplicado', ', '.join(keys) or '(fila completa)', dup)
    dims = {'validez': [0, 0], 'consistencia': [0, 0]}
    for rule in rules:
        eligible, failed = evaluar(df, rule); tested = int(eligible.sum()); errors = int(failed.sum())
        dimension = rule.get('dimension', 'validez')
        dims[dimension][0] += tested; dims[dimension][1] += errors
        summaries.append({'id': rule['id'], 'tipo': rule['type'], 'columna': rule['column'],
                          'dimension': dimension, 'evaluados': tested, 'fallos': errors,
                          'omitidos': n-tested})
        add(rule['type'], rule['column'], failed, rule['id'])
    if anomalies:
        for col, mask, low, high in detectar_iqr(df):
            add('anomalia', col, mask, detail=f'IQR: fuera de [{low:.3f}, {high:.3f}]')
    metrics = {'completitud': 100*(1-missing/df.size), 'unicidad': 100*(1-int(dup.sum())/n)}
    for dim, (tested, errors) in dims.items():
        metrics[dim] = 100*(1-errors/tested) if tested else None
    coverage = sum(WEIGHTS[k] for k,v in metrics.items() if v is not None)
    score = sum(WEIGHTS[k]*v for k,v in metrics.items() if v is not None)/coverage
    rules_json = json.dumps(rules, sort_keys=True, ensure_ascii=False)
    return {'id': str(uuid.uuid4()), 'fecha': datetime.now(timezone.utc).isoformat(),
            'fuente': str(source), 'filas': n, 'columnas': len(df.columns),
            'faltantes': missing, 'duplicados': int(dup.sum()),
            'registros_con_errores': int(affected.sum()),
            'porcentaje_registros_con_errores': round(100 * affected.mean(), 4),
            'reglas_ejecutadas': len(summaries),
            'reglas_incumplidas': sum(s['fallos'] > 0 for s in summaries),
            'anomalias': totals.get('anomalia', 0),
            'metricas': {k: round(v,4) if v is not None else None for k,v in metrics.items()},
            'score': round(score,4), 'cobertura': round(coverage*100),
            'alerta': 'REVISAR' if score < 90 else 'ACEPTABLE',
            'perfil': perfilar(df), 'reglas': rules, 'resultados_reglas': summaries,
            'hash_reglas': hashlib.sha256(rules_json.encode()).hexdigest(),
            'claves': keys, 'anomalias_activas': anomalies, 'conteos': totals,
            'incidencias': issues, 'muestra_limitada': sum(totals.values()) > len(issues),
            'segundos': round(time.perf_counter()-start,4)}
