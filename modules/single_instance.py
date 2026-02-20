"""Single-instance guard.

Goal: a tiny, dependency-free way to prevent two copies of the app
from running at the same time.

Implementation: OS file locking (non-blocking). Keeping the file handle
open keeps the lock held until process exit/crash.
"""

from __future__ import annotations

import atexit
import os
import tempfile
from typing import Optional


class SingleInstance:
    def __init__(self, app_id: str, lock_dir: Optional[str] = None) -> None:
        self.app_id = app_id
        self.lock_dir = lock_dir or tempfile.gettempdir()
        self.lock_path = os.path.join(self.lock_dir, f"{self.app_id}.lock")
        self._fh = None
        self.acquired = False

    def acquire(self) -> bool:
        if self.acquired:
            return True

        try:
            # Open (or create) lock file.
            self._fh = open(self.lock_path, "a+b")
        except OSError:
            self._fh = None
            self.acquired = False
            return False

        try:
            if os.name == "nt":
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            self.acquired = True

            # Best-effort: write PID for debugging.
            try:
                self._fh.seek(0)
                self._fh.truncate()
                self._fh.write(str(os.getpid()).encode("utf-8", errors="ignore"))
                self._fh.flush()
            except Exception:
                pass

            atexit.register(self.release)
            return True
        except Exception:
            # Another instance likely holds the lock.
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None
            self.acquired = False
            return False

    def release(self) -> None:
        if not self._fh:
            self.acquired = False
            return

        try:
            if os.name == "nt":
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        finally:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None
            self.acquired = False
