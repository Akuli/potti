// taken from pyodide's tests
// https://github.com/pyodide/pyodide/releases/tag/0.25.0

import pyodideModule from "npm:pyodide@0.25.0/pyodide.js";
const { loadPyodide } = pyodideModule;

const pyodide = await loadPyodide();
try {
  const result = await pyodide.runPythonAsync(Deno.args[0])
  console.log(result.toString());
} catch(e) {
  console.log(e);
}
