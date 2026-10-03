from src.ingestion.data_loader import cargar_csv
from src.profiling.perfilador import (
    perfil_general,
    perfil_columnas,
    estadisticas_numericas
)


def main():
    try:
        ruta_archivo = "data/input/global_ai_jobs_2026.csv"

        df = cargar_csv(ruta_archivo)

        perfil_general(df)

        print("\n========== PERFIL POR COLUMNA ==========")
        perfil = perfil_columnas(df)
        print(perfil.to_string(index=False))

        print("\n========== ESTADÍSTICAS NUMÉRICAS ==========")
        estadisticas = estadisticas_numericas(df)

        if estadisticas.empty:
            print("No se encontraron columnas numéricas.")
        else:
            print(estadisticas)

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()