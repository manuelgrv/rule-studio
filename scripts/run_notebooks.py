"""Execute notebooks with the project's Python, without installing a global kernel."""
import json
import sys
import tempfile
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="rule-manager-kernel-") as tmp:
    directory=Path(tmp)/"rule-manager-local"
    directory.mkdir()
    (directory/"kernel.json").write_text(json.dumps({
        "argv":[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],
        "display_name":"Rule Manager local","language":"python"}))
    specs=KernelSpecManager(kernel_dirs=[tmp])
    for path in sorted((ROOT/"notebooks").glob("*.ipynb")):
        notebook=nbformat.read(path,as_version=4)
        notebook.metadata.kernelspec={"name":"rule-manager-local","display_name":"Rule Manager local","language":"python"}
        km=KernelManager(kernel_name="rule-manager-local",kernel_spec_manager=specs)
        client=NotebookClient(notebook,km=km,timeout=600,resources={"metadata":{"path":str(ROOT)}})
        print("Ejecutando",path.name,flush=True)
        try:
            client.execute()
        finally:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
                km.cleanup_resources()
        notebook.metadata.kernelspec={"name":"python3","display_name":"Python (proyecto rule-manager)","language":"python"}
        nbformat.write(notebook,path)
        print("OK",path.name,flush=True)
