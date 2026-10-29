"""Monitor secuencial, independiente de Qt y sin modificar la fuente."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import math
from pathlib import Path
import time

from src.ingestion.data_loader import ArchivoEnCambio, cargar_snapshot, firma_archivo
from src.quality.engine import analizar
from src.quality.rules import normalizar_reglas
from src.service import guardar_reporte


class MonitorCSV:
    def __init__(self, path, rules=None, repo=None, keys=None, anomalies=False,
                 sep=None, encoding='utf-8-sig', interval=2.0, stable_seconds=1.0,
                 threshold=90.0, intelligent=False, anomaly_columns=None, contamination=.05):
        for name, value, low, high in [('interval', interval, .1, 3600),
                                       ('stable_seconds', stable_seconds, .1, 3600),
                                       ('threshold', threshold, 0, 100)]:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{name} debe estar entre {low} y {high}.')
        self.path = Path(path).resolve()
        if self.path.suffix.lower() != '.csv':
            raise ValueError('El monitor experimental requiere un archivo .csv.')
        self.rules = deepcopy(normalizar_reglas(rules))
        self.repo = repo
        self.keys = list(keys or [])
        self.anomalies = anomalies
        self.intelligent = intelligent
        self.anomaly_columns = list(anomaly_columns) if anomaly_columns is not None else None
        self.contamination = contamination
        self.sep = sep
        self.encoding = encoding
        self.interval = interval
        self.stable_seconds = stable_seconds
        self.threshold = threshold
        self._candidate = None
        self._candidate_since = 0.0
        self._last_signature = None
        self._last_digest = None
        self.last_report = None
        self.recent = deque(maxlen=100)

    @staticmethod
    def event(state, message, report=None):
        return {'estado': state, 'mensaje': message,
                'fecha': datetime.now(timezone.utc).isoformat(), 'reporte': report}

    def poll(self, now=None):
        """Una observación. Espera estabilidad y analiza solo versiones nuevas.

        `now` permite probar los tiempos sin pausas reales. Debe ser monótono.
        Los errores de entrada son recuperables; no invalidan el último reporte.
        """
        now = time.monotonic() if now is None else now
        try:
            signature = firma_archivo(self.path)
            if signature != self._candidate:
                self._candidate = signature
                self._candidate_since = now
                return self.event('esperando', 'Cambio detectado; esperando que el CSV se estabilice.')
            if now - self._candidate_since < self.stable_seconds:
                return self.event('esperando', 'Esperando estabilidad del archivo.')
            if signature == self._last_signature:
                return self.event('sin_cambios', 'Activo; esperando nuevos datos.')
            df, digest, snapshot_signature = cargar_snapshot(self.path, self.sep, self.encoding)
            if snapshot_signature != signature:
                raise ArchivoEnCambio('El archivo cambió antes de la lectura; se reintentará.')
            if digest == self._last_digest:
                self._last_signature = signature
                return self.event('sin_cambios', 'El contenido no cambió; no se repite el análisis.')
            report = analizar(df, self.rules, self.path.name, self.keys, self.anomalies,
                              intelligent=self.intelligent, anomaly_columns=self.anomaly_columns,
                              contamination=self.contamination)
            if firma_archivo(self.path) != signature:
                raise ArchivoEnCambio('El archivo cambió durante el análisis; se reintentará.')
            report['sha256'] = digest
            report['ingestion'] = {'encoding': self.encoding, 'separador': self.sep or 'auto'}
            report['monitoreo'] = {'experimental': True, 'modo': 'sondeo_csv',
                                   'intervalo_segundos': self.interval,
                                   'estabilidad_segundos': self.stable_seconds,
                                   'umbral_alerta': self.threshold}
            report['alerta'] = 'REVISAR' if report['score'] < self.threshold else 'ACEPTABLE'
            guardar_reporte(report, self.repo)
            self._last_signature = signature
            self._last_digest = digest
            self.last_report = report
            self.recent.append({'fecha': report['fecha'], 'score': report['score'],
                                'filas': report['filas'], 'alerta': report['alerta']})
            message = f"{report['alerta']} · {report['score']:.2f}/100 · cobertura {report['cobertura']}%"
            if not report['guardado']:
                message += ' · sin guardar en histórico'
            return self.event('analizado', message, report)
        except ArchivoEnCambio as exc:
            self._candidate = None
            return self.event('esperando', str(exc))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # Exigir estabilidad de nuevo después de desapariciones/bloqueos.
            self._candidate = None
            return self.event('error', f'No se pudo analizar el CSV: {exc}')

    def events(self, stop, max_polls=None):
        """Sondeos sin solapamiento; Event.wait permite detener la espera."""
        if max_polls is not None and (isinstance(max_polls, bool) or not isinstance(max_polls, int) or max_polls < 1):
            raise ValueError('max_polls debe ser un entero positivo.')
        count = 0
        while not stop.is_set() and (max_polls is None or count < max_polls):
            yield self.poll()
            count += 1
            if max_polls is not None and count >= max_polls:
                break
            if stop.wait(self.interval):
                break
