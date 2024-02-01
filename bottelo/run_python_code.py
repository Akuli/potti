import subprocess
from pathlib import Path


# Uses pyodide (python interpreter for WebAssembly) as a sandbox.
# This is great, because pyodide creates its own fake file system.
#
# To run webassembly, I stole some javascript code from pyodide's tests.
# I am running it with deno because they run it with deno.
def run_python_code(code: str) -> str:
    output = subprocess.check_output(
        [
            "downloaded-deps/deno",
            "run",
            "--allow-read",  # let it read library files (pyodide has dummy file system)
            "run_pyodide.js",
            code,
        ],
        stderr=subprocess.STDOUT,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    return output
