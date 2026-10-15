"""Reglas declarativas y adaptadores de la API original en español."""
import math
import re

import pandas as pd

TYPES = {'required', 'unique', 'range', 'regex', 'allowed', 'date', 'compare'}
LEGACY_TYPES = {
    'obligatorio': 'required', 'unicidad': 'unique', 'rango': 'range',
    'valores_permitidos': 'allowed', 'menor_igual': 'compare',
    'fecha_anterior': 'compare',
}


def normalizar_reglas(rules):
    if rules is None:
        return []
    if not isinstance(rules, list):
        raise ValueError('Las reglas deben ser una lista JSON.')
    normalized = []
    for position, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            raise ValueError('Cada regla debe ser un objeto.')
        if 'tipo' not in rule:
            normalized.append(dict(rule))
            continue
        kind = rule['tipo']
        if kind not in LEGACY_TYPES:
            raise ValueError(f'Tipo de regla no soportado: {kind}')
        r = {'id': rule.get('id', f'original_{position}'), 'type': LEGACY_TYPES[kind],
             'column': rule.get('columna')}
        for old, new in [('minimo', 'min'), ('maximo', 'max'), ('valores', 'values')]:
            if old in rule and rule[old] is not None:
                r[new] = rule[old]
        if kind in {'menor_igual', 'fecha_anterior'}:
            date = kind == 'fecha_anterior'
            r.update(column=rule.get('columna_inicio' if date else 'columna_izquierda'),
                     other=rule.get('columna_fin' if date else 'columna_derecha'),
                     op='<=', dimension='consistencia')
            if date:
                r.update(value_type='date', format=rule.get('formato', '%Y-%m-%d'))
        if 'dimension' in rule:
            r['dimension'] = rule['dimension']
        normalized.append(r)
    return normalized


def validar_reglas(rules, columns):
    normalized = normalizar_reglas(rules)
    ids = set()
    for r in normalized:
        if not isinstance(r.get('id'), str) or not r['id'].strip() or r['id'] in ids:
            raise ValueError('Cada regla necesita un id textual único.')
        ids.add(r['id'])
        if not isinstance(r.get('type'), str) or r['type'] not in TYPES:
            raise ValueError(f"Regla {r['id']}: tipo no válido.")
        if not isinstance(r.get('column'), str) or r['column'] not in columns:
            raise ValueError(f"Regla {r['id']}: columna no válida.")
        if r.get('dimension', 'validez') not in ('validez', 'consistencia'):
            raise ValueError('La dimensión debe ser validez o consistencia.')
        if r['type'] == 'regex':
            if not isinstance(r.get('pattern'), str):
                raise ValueError('regex requiere un pattern textual.')
            try:
                re.compile(r['pattern'])
            except re.error as exc:
                raise ValueError(f"Regla {r['id']}: expresión regular inválida.") from exc
        if r['type'] == 'range':
            if 'min' not in r and 'max' not in r:
                raise ValueError('range requiere min o max.')
            for key in ('min', 'max'):
                value = r.get(key)
                if key in r and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise ValueError('Los límites deben ser números finitos.')
            if r.get('min', float('-inf')) > r.get('max', float('inf')):
                raise ValueError('min no puede ser mayor que max.')
        if r['type'] == 'allowed' and not isinstance(r.get('values'), list):
            raise ValueError('allowed requiere una lista values.')
        if r['type'] == 'date' and (not isinstance(r.get('format'), str) or not r['format']):
            raise ValueError('date requiere format, por ejemplo %Y-%m-%d.')
        if r['type'] == 'compare':
            if not isinstance(r.get('other'), str) or r['other'] not in columns or r.get('op') not in ('<=', '>=', '=='):
                raise ValueError('compare requiere other y op: <=, >= o ==.')
            if r.get('value_type', 'number') not in ('number', 'date'):
                raise ValueError('compare admite value_type number o date.')
            if r.get('value_type') == 'date' and (not isinstance(r.get('format'), str) or not r['format']):
                raise ValueError('La comparación de fechas requiere format.')
    return normalized


def evaluar(df, r):
    s = df[r['column']]
    kind = r['type']
    eligible = s.notna()
    if kind == 'required':
        eligible = pd.Series(True, index=df.index)
        good = s.notna()
    elif kind == 'unique':
        good = ~s.duplicated(keep=False)
    elif kind == 'range':
        n = pd.to_numeric(s, errors='coerce')
        good = n.notna() & ~n.isin([float('inf'), float('-inf')]) & n.between(r.get('min', float('-inf')), r.get('max', float('inf')))
    elif kind == 'regex':
        good = s.astype('string').str.fullmatch(r['pattern'], na=False)
    elif kind == 'allowed':
        good = s.astype('string').isin([str(v) for v in r['values']])
    elif kind == 'date':
        good = pd.to_datetime(s, format=r['format'], errors='coerce').notna()
    else:
        other = df[r['other']]
        eligible &= other.notna()
        if r.get('value_type') == 'date':
            a = pd.to_datetime(s, format=r['format'], errors='coerce')
            b = pd.to_datetime(other, format=r['format'], errors='coerce')
        else:
            a = pd.to_numeric(s, errors='coerce').replace([float('inf'), float('-inf')], float('nan'))
            b = pd.to_numeric(other, errors='coerce').replace([float('inf'), float('-inf')], float('nan'))
        good = {'<=': a.le, '>=': a.ge, '==': a.eq}[r['op']](b) & a.notna() & b.notna()
    failed = eligible & ~good.fillna(False)
    return eligible, failed


def validar_columna(df, columna):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe en el dataset.")


def calcular_porcentaje_cumplimiento(total_registros, total_errores):
    return round(100 * (1 - total_errores / total_registros), 2) if total_registros else 100.0


def construir_resultado(df, regla, columna, mascara_error):
    errors = int(mascara_error.sum())
    return {'regla': regla, 'columna': columna, 'total_errores': errors,
            'porcentaje_cumplimiento': calcular_porcentaje_cumplimiento(len(df), errors),
            'indices_error': df.index[mascara_error].tolist()}


def ejecutar_reglas(df, configuracion):
    """Conserva la forma del resultado original y acepta ambos formatos JSON."""
    rules = validar_reglas(configuracion, df.columns)
    data = df.replace(r'^\s*$', pd.NA, regex=True)
    results = []
    for original, rule in zip(configuracion or [], rules):
        _, failed = evaluar(data, rule)
        kind = original.get('tipo', rule['type'])
        name = rule['column']
        if kind in {'menor_igual', 'fecha_anterior'}:
            name = f"{rule['column']} <= {rule['other']}"
            kind = 'consistencia_fecha' if kind == 'fecha_anterior' else 'consistencia'
        results.append(construir_resultado(df, kind, name, failed))
    return results


def validar_obligatorio(df, columna):
    return ejecutar_reglas(df, [{'tipo': 'obligatorio', 'columna': columna}])[0]


def validar_unicidad(df, columna):
    return ejecutar_reglas(df, [{'tipo': 'unicidad', 'columna': columna}])[0]


def validar_rango(df, columna, minimo=None, maximo=None):
    return ejecutar_reglas(df, [{'tipo': 'rango', 'columna': columna, 'minimo': minimo, 'maximo': maximo}])[0]


def validar_valores_permitidos(df, columna, valores_permitidos):
    return ejecutar_reglas(df, [{'tipo': 'valores_permitidos', 'columna': columna, 'valores': valores_permitidos}])[0]


def validar_menor_igual(df, columna_izquierda, columna_derecha):
    return ejecutar_reglas(df, [{'tipo': 'menor_igual', 'columna_izquierda': columna_izquierda, 'columna_derecha': columna_derecha}])[0]


def validar_fecha_anterior(df, columna_fecha_inicio, columna_fecha_fin):
    return ejecutar_reglas(df, [{'tipo': 'fecha_anterior', 'columna_inicio': columna_fecha_inicio, 'columna_fin': columna_fecha_fin}])[0]
