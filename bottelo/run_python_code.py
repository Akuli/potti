import atexit
import os
import queue
import subprocess
import threading
from pathlib import Path


# Starting a runner is slow. Let's start many of them ahead of time, and
# output them as needed.
class RunnerSpawner:
    def __init__(self) -> None:
        self.queue: queue.Queue[subprocess.Popen] = queue.Queue(maxsize=1)
        self.stopping = False
        self.thread = threading.Thread(target=self.spawn_more, daemon=True)
        self.thread.start()

    def spawn_more(self) -> None:
        project_root = Path(__file__).parent.parent

        deno_cache = project_root / "deno" / "cache"
        deno_cache.mkdir(exist_ok=True)

        while not self.stopping:
            # --allow-read lets pyodide read Python library files.
            # This is safe, because pyodide has dummy file system anyway. See tests.
            process = subprocess.Popen(
                "ulimit -v 100000000; timeout 10 deno/deno run --allow-read run_pyodide.js",
                shell=True,  # ulimit is provided by shell
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=project_root,
                env=dict(os.environ) | {"DENO_DIR": str(deno_cache)},
            )

            if self.stopping:
                process.kill()
                process.wait()
            else:
                self.queue.put(process)  # will wait if queue is full (maxsize)

    def stop(self) -> None:
        if self.stopping:
            return

        self.stopping = True
        while True:
            try:
                process = self.queue.get(timeout=0.01)
            except queue.Empty:
                if self.thread.is_alive():
                    # Thread is spawning a new process now. It will soon put
                    # it to the queue and then stop.
                    continue
                else:
                    # We are done. All processes are stopped and no more will
                    # be created.
                    break

            process.kill()
            process.wait()

    def get_a_process(self) -> subprocess.Popen:
        return self.queue.get()


spawner = RunnerSpawner()
atexit.register(spawner.stop)


# Uses pyodide (python interpreter for WebAssembly) as a sandbox.
# This is great, because pyodide creates its own fake file system.
#
# To run webassembly, I stole some javascript code from pyodide's tests.
# I am running it with deno because they run it with deno.
def run_python_code(code: str) -> str:
    with spawner.get_a_process() as process:
        process.stdin.write(code)
        process.stdin.flush()
        process.stdin.close()
        return process.stdout.read().replace('\n', ' ').strip()
