// taken from pyodide's tests
// https://github.com/pyodide/pyodide/releases/tag/0.25.0

import pyodideModule from "npm:pyodide@0.25.0/pyodide.js";
const { loadPyodide, toPy } = pyodideModule;

const pyodide = await loadPyodide();

try {
  const result = await pyodide.runPythonAsync(Deno.args[0])
  // Show the Python return value / result, if not None
  if (result !== undefined) {
    console.log(result.toString());
  }
} catch(e) {
  // Don't show traceback, skip to "FooError: blah blah" part
  // (that part can span multiple lines)
  try {
    console.log(/\n[^ ][\S\s]*/.exec(e.toString())[0]);
  } catch(e2) {
    console.log(e.toString());
  }
}
