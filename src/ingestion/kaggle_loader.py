"""Descarga opcional; no se necesita Internet para la demo."""
def descargar_dataset(nombre='datascikhan/e-commerce-sales-and-customer-analytics'):
    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError('Instala la dependencia opcional: pip install kagglehub') from exc
    return kagglehub.dataset_download(nombre)


def listar_archivos(ruta):
    """Compatibilidad con la utilidad original, sin descargar al importar."""
    from pathlib import Path
    if ruta is not None:
        for archivo in sorted(Path(ruta).iterdir()):
            print(f'- {archivo.name}')
