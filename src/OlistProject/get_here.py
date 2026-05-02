import os
from pathlib import Path

def get_here():
    """
    Find the project root directory by searching upwards for marker files.

    The function identifies the root by looking for the presence of 
    `_quarto.yml` or `pyproject.toml`. It handles both interactive 
    environments (Jupyter, Quarto) and standard Python scripts.

    Returns
    -------
    parent : pathlib.Path
        The path to the project root directory if a marker file is found. 
        Otherwise, returns the initial starting path (the directory of 
        the script or the current working directory).

    See Also
    --------
    os.getcwd : Return a string representing the current working directory.
    pathlib.Path.resolve : Make the path absolute, resolving any symlinks.

    Notes
    -----
    The search starts from the location of the current file (if `__file__` 
    is defined) or the current working directory. It then traverses 
    upwards through all parent directories until it encounters a 
    supported configuration file.

    Examples
    --------
    >>> root = get_here()
    >>> print(root.name)
    'my_project_name'
    """
    # Si estamos en Quarto/Jupyter, usamos el directorio actual
    # Si estamos en un script .py, usamos __file__
    try:
        start_path = Path(__file__).resolve()
    except NameError:
        start_path = Path(os.getcwd())
    
    # Buscamos hacia arriba hasta encontrar el archivo raíz del proyecto
    for parent in [start_path] + list(start_path.parents):
        if (parent / "_quarto.yml").exists() or (parent / "pyproject.toml").exists():
            return parent
    return start_path