"""File locking and atomic write utilities for multi-agent safety."""

import fcntl
import json
import os
import sys
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

# Maximum seconds to wait for a lock before giving up and proceeding unlocked.
LOCK_TIMEOUT_SECONDS = 10
LOCK_RETRY_INTERVAL = 0.05


@contextmanager
def file_lock(path: Path, timeout: float = LOCK_TIMEOUT_SECONDS) -> Generator[None, None, None]:
    """Acquire an exclusive lock on a file for safe read-modify-write.

    Uses fcntl.flock() with a sidecar .lock file so the actual data file
    is never held open longer than necessary.

    If the lock cannot be acquired within *timeout* seconds, proceeds
    without the lock and writes a warning to stderr.  This ensures agent
    processes are never blocked indefinitely — the worst case degrades to
    the same behavior as running without locking at all.
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    acquired = False
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                if time.monotonic() >= deadline:
                    print(
                        f"Warning: could not acquire lock on {path} after "
                        f"{timeout}s, proceeding without lock",
                        file=sys.stderr,
                    )
                    break
                time.sleep(LOCK_RETRY_INTERVAL)
        yield
    finally:
        if acquired:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically using temp file + rename.

    Writes to a temporary file in the same directory, then uses
    ``os.replace()`` (which is atomic on the same filesystem) to move
    it into place.  This prevents partial writes from corrupting the
    file if the process is interrupted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, str(path))
    except BaseException:
        os.unlink(tmp_path)
        raise
