import re
import pandas as pd


def validar_obligatorio(df, columna):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")

    mascara_error = df[columna].isna()

    return {
        "regla": "obligatorio",
        "columna": columna,
        "total_errores": int(mascara_error.sum()),
        "indices_error": df.index[mascara_error].tolist()
    }


def validar_unicidad(df, columna):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")

    mascara_error = df[columna].duplicated(keep=False)

    return {
        "regla": "unicidad",
        "columna": columna,
        "total_errores": int(mascara_error.sum()),
        "indices_error": df.index[mascara_error].tolist()
    }


def validar_rango(df, columna, minimo=None, maximo=None):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")

    serie = pd.to_numeric(df[columna], errors="coerce")

    mascara_error = pd.Series(False, index=df.index)

    if minimo is not None:
        mascara_error |= serie < minimo

    if maximo is not None:
        mascara_error |= serie > maximo

    return {
        "regla": "rango",
        "columna": columna,
        "total_errores": int(mascara_error.sum()),
        "indices_error": df.index[mascara_error].tolist()
    }


def validar_valores_permitidos(df, columna, valores_permitidos):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")

    mascara_error = (
        df[columna].notna()
        & ~df[columna].isin(valores_permitidos)
    )

    return {
        "regla": "valores_permitidos",
        "columna": columna,
        "total_errores": int(mascara_error.sum()),
        "indices_error": df.index[mascara_error].tolist()
    }


def validar_email(df, columna):
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe.")

    patron = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    mascara_error = (
        df[columna].notna()
        & ~df[columna].astype(str).str.match(patron)
    )

    return {
        "regla": "formato_email",
        "columna": columna,
        "total_errores": int(mascara_error.sum()),
        "indices_error": df.index[mascara_error].tolist()
    }

def ejecutar_reglas(df, configuracion):
    resultados = []

    for regla in configuracion:

        tipo = regla["tipo"]
        columna = regla["columna"]

        if tipo == "obligatorio":
            resultado = validar_obligatorio(df, columna)

        elif tipo == "unicidad":
            resultado = validar_unicidad(df, columna)

        elif tipo == "rango":
            resultado = validar_rango(
                df,
                columna,
                regla.get("minimo"),
                regla.get("maximo")
            )

        elif tipo == "valores_permitidos":
            resultado = validar_valores_permitidos(
                df,
                columna,
                regla["valores"]
            )

        elif tipo == "email":
            resultado = validar_email(df, columna)

        else:
            resultado = {
                "regla": tipo,
                "columna": columna,
                "error": "Tipo de regla no soportado"
            }

        resultados.append(resultado)

    return resultados