"""Dos grupos sintéticos y dos combinaciones raras dentro de los rangos IQR."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def dataset():
    rng = np.random.default_rng(42)
    # Patrones ficticios de consumo: NO son datos ni reglas de negocio reales.
    units = np.concatenate([rng.normal(30, 2, 200), rng.normal(70, 2, 200), [30, 70]])
    amounts = np.concatenate([rng.normal(60, 3, 200), rng.normal(140, 3, 200), [140, 60]])
    return pd.DataFrame({'id': [f'{i:04d}' for i in range(1, 403)],
                         'unidades': units.round(4), 'importe': amounts.round(4)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', default='data/input/demo_inteligente.csv')
    args = parser.parse_args()
    path = Path(args.salida)
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset().to_csv(path, index=False, encoding='utf-8')
    print(f'{path}: 402 filas; combinaciones anómalas sembradas en los registros 401 y 402.')
