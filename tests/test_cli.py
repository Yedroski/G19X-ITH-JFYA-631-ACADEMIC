import json

import pytest

import main


def test_cli_batch_y_monitor(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    path = tmp_path / 'datos.csv'
    path.write_text('id,edad\n001,20\n002,150\n', encoding='utf-8')
    rules = tmp_path / 'reglas.json'
    rules.write_text(json.dumps([{'id': 'edad', 'type': 'range', 'column': 'edad', 'max': 100}]), encoding='utf-8')
    base = ['--demo', '--csv', str(path), '--rules', str(rules), '--output', str(tmp_path / 'out')]
    assert main.main(base) == 0
    assert main.main(base + ['--watch', '--interval', '.1', '--stability', '.1', '--max-polls', '6']) == 0
    output = capsys.readouterr().out
    assert 'analizado' in output and 'sin_cambios' in output
    reports = list((tmp_path / 'out').glob('*/reporte.json'))
    assert len(reports) == 2
    assert any(json.loads(p.read_text(encoding='utf-8')).get('monitoreo') for p in reports)


def test_cli_monitor_sin_persistencia(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    def broken(**kwargs):
        raise RuntimeError('BD desconectada')
    monkeypatch.setattr(main, 'Repository', broken)
    path = tmp_path / 'datos.csv'
    path.write_text('id\n1\n')
    assert main.main(['--demo', '--csv', str(path), '--watch', '--interval', '.1',
                      '--stability', '.1', '--max-polls', '4', '--output', str(tmp_path / 'out')]) == 2


@pytest.mark.parametrize('args', [['--watch'], ['--max-polls', '2'],
                                  ['--watch', '--csv', 'a.csv', '--max-polls', '0']])
def test_cli_rechaza_combinaciones_invalidas(args):
    with pytest.raises(SystemExit) as error:
        main.main(args)
    assert error.value.code == 2


def test_cli_no_confunde_sin_analisis_con_exito(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    assert main.main(['--demo', '--csv', str(tmp_path / 'ausente.csv'), '--watch', '--max-polls', '1']) == 1
