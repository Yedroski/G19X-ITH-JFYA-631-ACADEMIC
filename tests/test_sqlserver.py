"""Integración real opt-in: TEST_SQLSERVER=1 python -m pytest tests/test_sqlserver.py -v"""
import os
import pandas as pd
import pytest
from dotenv import load_dotenv
from src.quality.engine import analizar
from src.database.repository import Repository

@pytest.mark.skipif(os.getenv('TEST_SQLSERVER')!='1',reason='Requiere instancia real SQL Server')
def test_sqlserver_real():
    load_dotenv();repo=Repository();repo.init()
    r=analizar(pd.DataFrame({'id':['1','2']},dtype='string'),source='prueba_integracion')
    r['guardado']=True;repo.save(r)
    assert repo.load(r['id'])==r
