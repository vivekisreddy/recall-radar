"""Execute every notebook in notebooks/ in place so outputs are saved."""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NB = Path(__file__).resolve().parents[1] / "notebooks"
for path in sorted(NB.glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(NB)}}).execute()
    nbformat.write(nb, path)
    print("executed", path.name)
