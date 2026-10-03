from src.ingestion.data_loader import cargar_csv
from src.quality.rules import ejecutar_reglas


def main():
    try:
        ruta_archivo = "data/input/global_ai_jobs_2026.csv"

        df = cargar_csv(ruta_archivo)

        reglas = [
            {
                "tipo": "obligatorio",
                "columna": "Job_ID"
            },
            {
                "tipo": "unicidad",
                "columna": "Job_ID"
            },
            {
                "tipo": "obligatorio",
                "columna": "Job_Title"
            },
            {
                "tipo": "rango",
                "columna": "Years_of_Experience",
                "minimo": 0,
                "maximo": 50
            },
            {
                "tipo": "rango",
                "columna": "Salary_USD",
                "minimo": 0
            },
            {
                "tipo": "rango",
                "columna": "Remote_Work_%",
                "minimo": 0,
                "maximo": 100
            },
            {
                "tipo": "rango",
                "columna": "Hiring_Difficulty_1_10",
                "minimo": 1,
                "maximo": 10
            },
            {
                "tipo": "rango",
                "columna": "Job_Satisfaction_1_10",
                "minimo": 1,
                "maximo": 10
            },
            {
                "tipo": "rango",
                "columna": "Work_Life_Balance_1_10",
                "minimo": 1,
                "maximo": 10
            },
            {
                "tipo": "valores_permitidos",
                "columna": "Job_Type",
                "valores": [
                    "Full-time",
                    "Contract",
                    "Freelance",
                    "Part-time"
                ]
            },
            {
                "tipo": "valores_permitidos",
                "columna": "Equity_Offered",
                "valores": [
                    "Yes",
                    "No"
                ]
            },
            {
                "tipo": "valores_permitidos",
                "columna": "Work_From_Home_Available",
                "valores": [
                    "Yes",
                    "No"
                ]
            }
        ]

        resultados = ejecutar_reglas(df, reglas)

        print("\n========== RESULTADOS DE CALIDAD ==========")

        for resultado in resultados:
            print(
                f"\nRegla: {resultado['regla']}"
                f"\nColumna: {resultado['columna']}"
                f"\nErrores: {resultado.get('total_errores', '-')}"
            )

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()