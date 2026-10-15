"""Datos sintéticos deterministas; no representan personas reales."""
import argparse
import csv
from pathlib import Path

def generar(path, n=1000):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        writer = csv.writer(f); writer.writerow(['id','email','edad','estado','fecha','total','descuento'])
        previous = None
        for i in range(n):
            row = [f'{i:06d}',f'persona{i}@example.com',20+i%50,'pagado','2026-10-01',100+i%500,10]
            if i%17==0: row[1]=''
            elif i%19==0: row[1]='correo-invalido'
            if i%23==0: row[2]=150
            if i%29==0: row[3]='desconocido'
            if i%31==0: row[4]='2026-02-30'
            if i%37==0: row[6]=9999
            if i%41==0: row[5]=100000
            if i%43==0 and previous: row=previous.copy()
            writer.writerow(row); previous=row
if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--filas',type=int,default=1000)
    p.add_argument('--salida',default='data/input/demo_clientes.csv');a=p.parse_args()
    generar(a.salida,a.filas)
