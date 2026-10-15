import json
import pandas as pd
import pytest
from src.ingestion.data_loader import cargar_csv
from src.quality.engine import analizar
from src.database.repository import Repository
from src.service import ejecutar
from src.exporter import exportar

def frame(data):return pd.DataFrame(data,dtype='string').replace(r'^\s*$',pd.NA,regex=True)

def test_csv_preserva_ids_y_na(tmp_path):
    p=tmp_path/'x.csv';p.write_text('id;valor\n001;NA\n002;   \n',encoding='utf-8')
    d=cargar_csv(p);assert d.loc[0,'id']=='001';assert d.loc[0,'valor']=='NA';assert pd.isna(d.loc[1,'valor'])

@pytest.mark.parametrize('content',['','a,a\n1,2','a,\n1,2','a,b\n'])
def test_csv_invalido(tmp_path,content):
    p=tmp_path/'x.csv';p.write_text(content)
    with pytest.raises(ValueError):cargar_csv(p)

def test_metricas_con_oraculo_manual():
    df=frame({'id':['1','2','2','3'],'edad':['20','150','150',None],'total':['10']*4,'descuento':['5','20','20','0']})
    rules=[{'id':'edad','type':'range','column':'edad','min':18,'max':100},
           {'id':'rel','type':'compare','column':'descuento','other':'total','op':'<=','dimension':'consistencia'}]
    r=analizar(df,rules)
    assert r['faltantes']==1 and r['duplicados']==1
    assert r['metricas']['completitud']==93.75
    assert r['metricas']['validez']==pytest.approx(100/3,abs=.0001)
    assert r['metricas']['unicidad']==75
    assert r['metricas']['consistencia']==50
    assert r['score']==63.125 and r['cobertura']==100

def test_sin_reglas_no_inventa_dimensiones():
    r=analizar(frame({'a':['1','2']}))
    assert r['metricas']['validez'] is None and r['metricas']['consistencia'] is None
    assert r['score']==100 and r['cobertura']==50

def test_reglas_y_nulos():
    df=frame({'id':['01','01',None],'email':['a@b.co','mal',None], 'fecha':['2026-02-28','2026-02-30',None], 'estado':['si','no',None]})
    rules=[{'id':'u','type':'unique','column':'id'}, {'id':'r','type':'required','column':'email'},
           {'id':'e','type':'regex','column':'email','pattern':r'[^@]+@[^@]+\.[^@]+'},
           {'id':'d','type':'date','column':'fecha','format':'%Y-%m-%d'},
           {'id':'a','type':'allowed','column':'estado','values':['si']}]
    r=analizar(df,rules);assert [x['fallos'] for x in r['resultados_reglas']]==[2,1,1,1,1]
    assert [x['omitidos'] for x in r['resultados_reglas']]==[1,0,1,1,1]

@pytest.mark.parametrize('rule',[
 {'id':'x','type':'range','column':'absent','min':1},
 {'id':'x','type':'range','column':'a','min':5,'max':1},
 {'id':'x','type':'compare','column':'a','other':'b','op':'<='},
 {'id':'x','type':'eval','column':'a'}])
def test_rechaza_reglas(rule):
    with pytest.raises(ValueError):analizar(frame({'a':['1']}),[rule])

def test_muestra_acotada_conteo_completo():
    r=analizar(frame({'a':[None]*100}),sample_limit=5)
    assert r['faltantes']==100 and len(r['incidencias'])==5 and r['muestra_limitada']

def test_anomalias_no_cambian_score():
    df=frame({'valor':list(map(str,[10,11,12,13,14,15,16,17,18,9999]))})
    a=analizar(df);b=analizar(df,anomalies=True)
    assert a['score']==b['score'];assert b['conteos']['anomalia']==1

def test_persistencia_y_exportacion(tmp_path):
    p=tmp_path/'x.csv';p.write_text('id,edad\n001,20\n002,150\n')
    repo=Repository(demo=True,demo_path=tmp_path/'test.db');repo.init()
    r=ejecutar(p,[{'id':'r','type':'range','column':'edad','max':100}],repo)
    assert r['guardado'];assert len(repo.history())==1;assert repo.load(r['id'])==r
    dest=exportar(r,tmp_path/'out');assert json.loads((dest/'reporte.json').read_text(encoding='utf-8'))==r
    assert (dest/'incidencias.csv').exists()

def test_fallo_bd_no_pierde_reporte(tmp_path):
    p=tmp_path/'x.csv';p.write_text('id\n1\n')
    class Broken:
        def save(self,r):raise RuntimeError('fallo simulado')
    r=ejecutar(p,[],Broken());assert not r['guardado'];assert r['filas']==1;assert 'error_bd' in r

def test_transaccion_rollback(tmp_path):
    from sqlalchemy import select,func
    from src.database.repository import ejecuciones,fuentes
    repo=Repository(demo=True,demo_path=tmp_path/'t.db');repo.init()
    r=analizar(frame({'a':['1']}));r['score']=float('nan')
    with pytest.raises(ValueError):repo.save(r)
    with repo.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(fuentes)).scalar()==0
        assert c.execute(select(func.count()).select_from(ejecuciones)).scalar()==0

@pytest.mark.parametrize('content',['a,b\n1,2,3\n','a,b\n1\n'])
def test_rechaza_ancho_csv_incorrecto(tmp_path,content):
    p=tmp_path/'x.csv';p.write_text(content)
    with pytest.raises(ValueError):cargar_csv(p)

def test_export_numeros_no_finitos(tmp_path):
    r=analizar(frame({'valor':['inf','-inf','1']}))
    dest=exportar(r,tmp_path);assert (dest/'reporte.json').is_file()

def test_clave_negocio_duplicada():
    df=frame({'id':['1','1'],'dato':['a','b']})
    assert analizar(df)['duplicados']==0
    assert analizar(df,keys=['id'])['duplicados']==1
