import kagglehub
import os


def descargar_dataset():
    try:
        path = kagglehub.dataset_download(
            "datascikhan/e-commerce-sales-and-customer-analytics"
        )

        print("Dataset descargado correctamente.")
        print(f"Ruta: {path}")

        return path

    except Exception as error:
        print(f"Error al descargar el dataset: {error}")
        return None


def listar_archivos(ruta):
    if ruta is None:
        return

    print("\nArchivos encontrados:")

    for archivo in os.listdir(ruta):
        print(f"- {archivo}")