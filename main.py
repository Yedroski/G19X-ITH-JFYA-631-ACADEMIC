from src.ingestion.data_loader import cargar_csv


def main():
    try:
        ruta_archivo = "data/input/global_ai_jobs_2026.csv"

        df = cargar_csv(ruta_archivo)

        print("\nPrimeros registros:")
        print(df.head())

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()