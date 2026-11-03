import subprocess
import os
import signal
import time
from pathlib import Path
from typing import Callable, Any
from scene_signal.render.ports.cancellation import CancellationToken
from scene_signal.render.domain.errors import RenderError

class FFmpegRunner:
    @staticmethod
    def run(
        args: list[str],
        timeout: float = 120.0,
        cancel_token: CancellationToken | None = None,
        cwd: Path | None = None,
        line_callback: Callable[[str], None] | None = None,
        stderr_tail_bytes: int = 1024,
    ) -> tuple[int, float, str]:
        start_time = time.time()
        
        # Ensure -nostdin is present
        if "-nostdin" not in args:
            args = [args[0], "-nostdin"] + args[1:]

        preexec = os.setsid if hasattr(os, "setsid") else None

        try:
            proc = subprocess.Popen(
                args,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                preexec_fn=preexec,
            )
        except Exception as e:
            raise RenderError(
                code="FFMPEG_FAILED",
                message=f"Failed to start subprocess {args[0]}: {e}",
                retryable=False,
                phase="render",
            ) from e

        stdout_lines = []
        stderr_lines = []

        try:
            # Simple monitoring loop with timeout and cancellation
            while proc.poll() is None:
                if cancel_token and cancel_token.is_cancelled:
                    FFmpegRunner._kill_proc(proc)
                    raise RenderError("RENDER_CANCELLED", "Render job cancelled", retryable=False, phase="render")

                if time.time() - start_time > timeout:
                    FFmpegRunner._kill_proc(proc)
                    raise RenderError("RENDER_TIMEOUT", f"Subprocess timed out after {timeout} seconds", retryable=True, phase="render")

                time.sleep(0.1)

            stdout, stderr = proc.communicate(timeout=5.0)
            elapsed = time.time() - start_time
            retcode = proc.returncode

            if retcode != 0:
                stderr_tail = stderr[-stderr_tail_bytes:] if stderr else ""
                raise RenderError(
                    code="FFMPEG_FAILED",
                    message=f"Subprocess failed with exit code {retcode}: {stderr_tail}",
                    retryable=False,
                    phase="render",
                    details={"returncode": retcode, "stderr": stderr_tail},
                )

            return retcode, elapsed, stderr[-stderr_tail_bytes:] if stderr else ""

        except RenderError:
            raise
        except Exception as e:
            FFmpegRunner._kill_proc(proc)
            raise RenderError(
                code="FFMPEG_FAILED",
                message=f"Subprocess execution error: {e}",
                retryable=False,
                phase="render",
            ) from e

    @staticmethod
    def _kill_proc(proc: subprocess.Popen) -> None:
        try:
            if hasattr(os, "killpg") and proc.pid:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
            else:
                proc.kill()
            proc.wait(timeout=2.0)
        except Exception:
            pass
