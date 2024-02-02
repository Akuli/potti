import sys
import fcntl
import atexit
import os
import queue
import subprocess
import threading
import logging
import time
import resource
import select
from pathlib import Path
from typing import IO


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(h)


def set_memory_limit() -> None:
    # https://gist.github.com/s3rvac/f97d6cbdfdb15c0a32e7e941f7f4a3fa
    max_mem = 200_000_000
    resource.setrlimit(resource.RLIMIT_DATA, (max_mem, max_mem))


def kill_process(process: subprocess.Popen[bytes]) -> None:
    log.debug(f"killing runner pid={process.pid}")
    process.kill()
    process.wait()  # don't leave a zombie process around


# This will wait max 0.1sec for data to become available.
def read_available_data(file: IO[bytes]) -> bytes:
    if select.select([file], [], [], 0.1)[0]:
        return file.read1()  # type: ignore
    else:
        return b""


# Starting a runner is slow. Let's start many of them ahead of time, and
# output them as needed.
class RunnerPool:
    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.queue: queue.Queue[subprocess.Popen[bytes]] = queue.Queue(maxsize=3)
        self.stopping = False
        self.thread = threading.Thread(target=self.spawn_more_until_stopped, daemon=True)
        self.thread.start()

    def spawn_one_new_runner(self) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(
            # --allow-read lets pyodide read Python library files.
            # This is safe, because pyodide has dummy file system anyway. See tests.
            ["deno/deno", "run", "--allow-read", "run_pyodide.js"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.project_root,
            env=dict(os.environ) | {"DENO_DIR": "deno/cache"},
            preexec_fn=set_memory_limit,
        )

        try:
            # Wait until this process has started and is ready to read input.
            #
            # We can't use text=True when starting the process because it breaks this.
            # Basically, one chunk that we happen to read at once could be in the
            # middle of a utf-8 character. Unlikely to happen, but would be extremely
            # hard to debug, so I don't want that.
            line = b""
            waited_damn_long_enough = time.monotonic() + 30
            while b"\n" not in line and not self.stopping:
                if time.monotonic() > waited_damn_long_enough:
                    raise ValueError("runner process didn't print anything in 30sec")

                assert process.stdout is not None  # needed to satisfy mypy
                line += read_available_data(process.stdout)

            # Ignore printed value when stopping. Process will soon be killed.
            if line != b"Loaded\n" and not self.stopping:
                raise ValueError(f"first thing runner process printed was {line!r}")

        except Exception as e:
            kill_process(process)
            raise e

        return process

    def spawn_more_until_stopped(self) -> None:
        project_root = Path(__file__).parent.parent

        deno_cache = project_root / "deno" / "cache"
        deno_cache.mkdir(exist_ok=True)

        while not self.stopping:
            start = time.monotonic()
            try:
                process = self.spawn_one_new_runner()
            except (ValueError, OSError):
                log.exception("loading runner failed")

                # Don't spam logs and such with failures, sleep until 2 seconds has passed
                now = time.monotonic()
                duration = now - start
                if duration < 2:
                    time.sleep(2 - duration)

            else:
                self.queue.put(process)  # will wait more if queue is full (maxsize)
                log.debug(f"{self.queue.qsize()} runners ready")

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

            kill_process(process)

    def get_a_process(self) -> subprocess.Popen[bytes]:
        while True:
            process = self.queue.get()

            if process.poll() is not None:
                # it dead
                log.error(f"runner process pid={process.pid} has died")
                continue

            # lgtm
            return process


pool = RunnerPool()
atexit.register(pool.stop)


def set_non_blocking(file: IO[bytes]) -> None:
    old_flags = fcntl.fcntl(file.fileno(), fcntl.F_GETFD)
    new_flags = old_flags | os.O_NONBLOCK
    fcntl.fcntl(file, fcntl.F_SETFD, new_flags)


MAX_RUN_TIME = 0.5


# Uses pyodide (python interpreter for WebAssembly) as a sandbox.
# This is great, because pyodide creates its own fake file system.
#
# To run webassembly, I stole some javascript code from pyodide's tests.
# I am running it with deno because they run it with deno.
def run_python_code(code: str) -> str:
    log.info(f"running {code!r}")
    process = pool.get_a_process()
    log.debug(f"got runner pid={process.pid}")

    try:
        # We can't use the communicate() method.
        #
        # I was wondering why communicate() got stuck when running python code
        # "while True: pass". Then I noticed that subprocess source code says:
        #
        #       # XXX Rewrite these to use non-blocking I/O on the file
        #       # objects; they are no longer using C stdio!
        #
        # Apparently this means that the timeout argument is broken in some cases.

        assert process.stdin is not None
        assert process.stdout is not None

        process.stdin.write(code.encode("utf-8"))
        process.stdin.flush()
        process.stdin.close()  # send EOF on stdin

        end = time.monotonic() + MAX_RUN_TIME
        set_non_blocking(process.stdout)
        output = b""

        while len(output) < 1000 and process.poll() is None:
            if time.monotonic() > end:
                return "timed out"
            output += read_available_data(process.stdout)

        return output.decode("utf-8", errors="replace").replace('\n', ' ').strip()

    finally:
        kill_process(process)


# for quick and dirty testing
#
#   $ python3 -m potti.run_python_code 'print(1)'
if __name__ == "__main__":
    [code] = sys.argv[1:]
    print(repr(run_python_code(code)))
