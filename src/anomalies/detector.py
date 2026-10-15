import pandas as pd

def detectar_iqr(df):
    """Exploratorio: no cambia el score y no prueba que un dato sea incorrecto."""
    found = []
    for col in df:
        n = pd.to_numeric(df[col], errors='coerce'); valid = n.dropna()
        if len(valid) < 8 or len(valid) != int(df[col].notna().sum()):
            continue
        q1, q3 = valid.quantile([.25, .75]); iqr = q3 - q1
        if iqr <= 0:
            continue
        mask = (n < q1-1.5*iqr) | (n > q3+1.5*iqr)
        if mask.any():
            found.append((str(col), mask, float(q1-1.5*iqr), float(q3+1.5*iqr)))
    return found
