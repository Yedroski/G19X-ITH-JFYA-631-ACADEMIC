"""Publica snapshots sintéticos de forma atómica para demostrar el monitor."""
import argparse
import csv
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, default=Path('data/input/stream_demo.csv'))
    parser.add_argument('--eventos', type=int, default=12)
    parser.add_argument('--intervalo', type=float, default=3)
    args = parser.parse_args()
    if args.eventos < 1 or not .1 <= args.intervalo <= 3600:
        parser.error('Usa al menos un evento y un intervalo entre 0.1 y 3600 segundos.')
    if args.salida.suffix.lower() != '.csv' or args.salida.exists():
        parser.error('Elige una ruta .csv nueva para no sobrescribir datos existentes.')
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        for i in range(args.eventos):
            bad = i % 3 == 2
            rows.append({'id': f'{i:06}', 'email': 'mal' if bad else f'persona{i}@example.com',
                         'edad': 150 if bad else 25, 'estado': 'desconocido' if bad else 'pagado',
                         'fecha': '2026-02-30' if bad else '2026-10-15',
                         'total': 100, 'descuento': 150 if bad else 10})
            temporary = args.salida.with_suffix('.csv.tmp')
            with temporary.open('w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            temporary.replace(args.salida)
            print(f'Publicado: {len(rows)} registros en {args.salida}', flush=True)
            if i + 1 < args.eventos:
                time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print('Simulador detenido.')


if __name__ == '__main__':
    main()
