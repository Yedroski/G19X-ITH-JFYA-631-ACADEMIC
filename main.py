from src.ingestion.data_loader import cargar_csv
from src.quality.rules import ejecutar_reglas


def main():

    try:

        ruta_archivo = (
            "data/input/global_ai_jobs_2026.csv"
        )

        df = cargar_csv(ruta_archivo)

        reglas = [

            # =====================
            # COMPLETITUD
            # =====================

            {
                "tipo": "obligatorio",
                "columna": "Job_ID"
            },

            {
                "tipo": "obligatorio",
                "columna": "Job_Title"
            },

            {
                "tipo": "obligatorio",
                "columna": "Salary_USD"
            },

            # =====================
            # UNICIDAD
            # =====================

            {
                "tipo": "unicidad",
                "columna": "Job_ID"
            },

            # =====================
            # VALIDEZ
            # =====================

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
                    "Part-time",
                    "Contract",
                    "Freelance"
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
                "columna":
                    "Work_From_Home_Available",
                "valores": [
                    "Yes",
                    "No"
                ]
            },

            # =====================
            # CONSISTENCIA
            # =====================

            {
                "tipo": "menor_igual",
                "columna_izquierda":
                    "Salary_Min",
                "columna_derecha":
                    "Salary_USD"
            },

            {
                "tipo": "menor_igual",
                "columna_izquierda":
                    "Salary_USD",
                "columna_derecha":
                    "Salary_Max"
            },

            {
                "tipo": "fecha_anterior",
                "columna_inicio":
                    "Posted_Date",
                "columna_fin":
                    "Application_Deadline"
            }
        ]

        resultados = ejecutar_reglas(
            df,
            reglas
        )

        print(
            "\n========== RESULTADOS "
            "DE CALIDAD =========="
        )

        for resultado in resultados:

            print(
                f"\nRegla: "
                f"{resultado['regla']}"
            )

            print(
                f"Columna: "
                f"{resultado['columna']}"
            )

            print(
                f"Errores: "
                f"{resultado['total_errores']}"
            )

            print(
                f"Cumplimiento: "
                f"{resultado['porcentaje_cumplimiento']}%"
            )

    except Exception as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()