import pandas as pd


def validar_columna(df, columna):
    if columna not in df.columns:
        raise ValueError(
            f"La columna '{columna}' no existe en el dataset."
        )


def calcular_porcentaje_cumplimiento(total_registros, total_errores):
    if total_registros == 0:
        return 100.0

    porcentaje = (
        (total_registros - total_errores)
        / total_registros
    ) * 100

    return round(porcentaje, 2)


def construir_resultado(df, regla, columna, mascara_error):
    total_errores = int(mascara_error.sum())

    return {
        "regla": regla,
        "columna": columna,
        "total_errores": total_errores,
        "porcentaje_cumplimiento":
            calcular_porcentaje_cumplimiento(
                len(df),
                total_errores
            ),
        "indices_error": df.index[mascara_error].tolist()
    }


def validar_obligatorio(df, columna):
    validar_columna(df, columna)

    mascara_error = df[columna].isna()

    return construir_resultado(
        df,
        "obligatorio",
        columna,
        mascara_error
    )


def validar_unicidad(df, columna):
    validar_columna(df, columna)

    mascara_error = (
        df[columna].notna()
        & df[columna].duplicated(keep=False)
    )

    return construir_resultado(
        df,
        "unicidad",
        columna,
        mascara_error
    )


def validar_rango(
    df,
    columna,
    minimo=None,
    maximo=None
):
    validar_columna(df, columna)

    serie = pd.to_numeric(
        df[columna],
        errors="coerce"
    )

    mascara_error = pd.Series(
        False,
        index=df.index
    )

    if minimo is not None:
        mascara_error |= serie < minimo

    if maximo is not None:
        mascara_error |= serie > maximo

    return construir_resultado(
        df,
        "rango",
        columna,
        mascara_error
    )


def validar_valores_permitidos(
    df,
    columna,
    valores_permitidos
):
    validar_columna(df, columna)

    mascara_error = (
        df[columna].notna()
        & ~df[columna].isin(valores_permitidos)
    )

    return construir_resultado(
        df,
        "valores_permitidos",
        columna,
        mascara_error
    )


def validar_menor_igual(
    df,
    columna_izquierda,
    columna_derecha
):
    validar_columna(df, columna_izquierda)
    validar_columna(df, columna_derecha)

    izquierda = pd.to_numeric(
        df[columna_izquierda],
        errors="coerce"
    )

    derecha = pd.to_numeric(
        df[columna_derecha],
        errors="coerce"
    )

    mascara_error = (
        izquierda.notna()
        & derecha.notna()
        & (izquierda > derecha)
    )

    nombre = (
        f"{columna_izquierda} <= "
        f"{columna_derecha}"
    )

    return construir_resultado(
        df,
        "consistencia",
        nombre,
        mascara_error
    )


def validar_fecha_anterior(
    df,
    columna_fecha_inicio,
    columna_fecha_fin
):
    validar_columna(df, columna_fecha_inicio)
    validar_columna(df, columna_fecha_fin)

    fecha_inicio = pd.to_datetime(
        df[columna_fecha_inicio],
        errors="coerce"
    )

    fecha_fin = pd.to_datetime(
        df[columna_fecha_fin],
        errors="coerce"
    )

    mascara_error = (
        fecha_inicio.notna()
        & fecha_fin.notna()
        & (fecha_inicio > fecha_fin)
    )

    nombre = (
        f"{columna_fecha_inicio} <= "
        f"{columna_fecha_fin}"
    )

    return construir_resultado(
        df,
        "consistencia_fecha",
        nombre,
        mascara_error
    )

def ejecutar_reglas(df, configuracion):
    resultados = []

    for regla in configuracion:

        tipo = regla["tipo"]

        if tipo == "obligatorio":

            resultado = validar_obligatorio(
                df,
                regla["columna"]
            )

        elif tipo == "unicidad":

            resultado = validar_unicidad(
                df,
                regla["columna"]
            )

        elif tipo == "rango":

            resultado = validar_rango(
                df,
                regla["columna"],
                regla.get("minimo"),
                regla.get("maximo")
            )

        elif tipo == "valores_permitidos":

            resultado = validar_valores_permitidos(
                df,
                regla["columna"],
                regla["valores"]
            )

        elif tipo == "menor_igual":

            resultado = validar_menor_igual(
                df,
                regla["columna_izquierda"],
                regla["columna_derecha"]
            )

        elif tipo == "fecha_anterior":

            resultado = validar_fecha_anterior(
                df,
                regla["columna_inicio"],
                regla["columna_fin"]
            )

        else:
            raise ValueError(
                f"Tipo de regla no soportado: {tipo}"
            )

        resultados.append(resultado)

    return resultados