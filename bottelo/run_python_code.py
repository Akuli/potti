import atexit
import os
import queue
import subprocess
import threading
import logging
from pathlib import Path


log = logging.getLogger(__name__)


# Starting a runner is slow. Let's start many of them ahead of time, and
# output them as needed.
class RunnerPool:
    def __init__(self) -> None:
        self.queue: queue.Queue[subprocess.Popen] = queue.Queue(maxsize=5)
        self.stopping = False
        self.thread = threading.Thread(target=self.spawn_more, daemon=True)
        self.thread.start()

    def spawn_more(self) -> None:
        project_root = Path(__file__).parent.parent

        deno_cache = project_root / "deno" / "cache"
        deno_cache.mkdir(exist_ok=True)

        while not self.stopping:
            process = subprocess.Popen(
                # --allow-read lets pyodide read Python library files.
                # This is safe, because pyodide has dummy file system anyway. See tests.
                #
                # TODO: memory limit
                [
                    "deno/deno",
                    "run",
                    "--allow-read",
                    "run_pyodide.js",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                cwd=project_root,
                env=dict(os.environ) | {"DENO_DIR": str(deno_cache)},
            )

            # Wait until this process has started and is ready to read input
            log.debug(f"new runner pid={process.pid} loading...")
            line = process.stdout.readline()
            assert line == "Loaded\n"
            log.debug(f"new runner pid={process.pid} is ready")

            if self.stopping:
                log.debug(f"new runner pid={process.pid} not needed, killing")
                process.kill()
                process.wait()
            else:
                self.queue.put(process)  # will wait more if queue is full (maxsize)

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

            log.debug(f"killing runner pid={process.pid}")
            process.kill()
            process.wait()

    def get_a_process(self) -> subprocess.Popen:
        return self.queue.get()


spawner = RunnerPool()
atexit.register(spawner.stop)


# Uses pyodide (python interpreter for WebAssembly) as a sandbox.
# This is great, because pyodide creates its own fake file system.
#
# To run webassembly, I stole some javascript code from pyodide's tests.
# I am running it with deno because they run it with deno.
def run_python_code(code: str) -> str:
    log.info(f"running {code!r}")
    with spawner.get_a_process() as process:
        log.debug(f"using runner pid={process.pid}")
        stdout, stderr = process.communicate(input=code, timeout=0.2)
        return stdout.replace('\n', ' ').strip()
