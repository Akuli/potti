// based on pyodide's tests
// https://github.com/pyodide/pyodide/blob/3e6d17147b60423b729f1b4920032e11185dfc42/src/test-deno/smoke-test.ts

import pyodideModule from "npm:pyodide@0.25.0/pyodide.js";
const { loadPyodide, toPy } = pyodideModule;


const pyodide = await loadPyodide();  // This is really really slow.

// Read python code after loading pyodide to work around loading slowness.
// This way, we can prepare a runners when idle, and have it sit here until it's needed.
const pythonCode = await Deno.readTextFile("/dev/stdin");

try {
  const result = await pyodide.runPythonAsync(pythonCode);
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
