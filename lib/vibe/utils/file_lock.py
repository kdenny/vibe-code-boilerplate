"""File locking and atomic write utilities for multi-agent safety."""

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator


@contextmanager
def file_lock(path: Path) -> Generator[None, None, None]:
    """Acquire an exclusive lock on a file for safe read-modify-write.

    Uses fcntl.flock() with a sidecar .lock file so the actual data file
    is never held open longer than necessary.
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
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
