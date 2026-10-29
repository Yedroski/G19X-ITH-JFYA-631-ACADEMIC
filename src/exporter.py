import csv
import json
from pathlib import Path

def exportar(report, folder):
    dest = Path(folder)/report['id']; dest.mkdir(parents=True, exist_ok=True)
    (dest/'reporte.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    for key in ('perfil', 'resultados_reglas', 'incidencias'):
        rows = report[key]
        with (dest/f'{key}.csv').open('w', encoding='utf-8-sig', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader()
                # Evita interpretar fórmulas al abrir CSV exportado en Excel.
                writer.writerows({k: "'"+v if isinstance(v,str) and v.startswith(('=', '+', '-', '@')) else v
                                  for k,v in row.items()} for row in rows)
    intelligence = report.get('inteligencia', {})
    if intelligence.get('activo'):
        with (dest/'anomalias_inteligentes.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['registro', 'puntuacion_anomalia', 'decision', 'valores'])
            writer.writeheader()
            for row in intelligence.get('resultados', []):
                writer.writerow({**row, 'valores': json.dumps(row['valores'], ensure_ascii=False, allow_nan=False)})
    return dest
