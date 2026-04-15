"""
Async FFmpeg subprocess runner with progress parsing and logging.
"""

import asyncio
import re
import shutil
import os
from typing import Callable, Optional

import flet as ft


def show_snackbar(page: "ft.Page", message: str, is_error: bool = False):
    """Show a snackbar notification using Flet 0.84+ API."""
    color = ft.Colors.ERROR if is_error else ft.Colors.PRIMARY
    sb = ft.SnackBar(ft.Text(message), bgcolor=color, open=True)
    page.overlay.append(sb)
    page.update()



async def check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system PATH."""
    return shutil.which("ffmpeg") is not None


async def probe_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of a media file in seconds using ffprobe.
    Returns None if duration cannot be determined.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        duration_str = stdout.decode().strip()
        if duration_str:
            return float(duration_str)
    except Exception:
        pass
    return None


def _parse_time_to_seconds(time_str: str) -> float:
    """Parse HH:MM:SS.ms or similar time string to seconds."""
    match = re.match(r"(\d+):(\d+):(\d+(?:\.\d+)?)", time_str)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


async def run_ffmpeg(
    cmd: list[str],
    on_progress: Optional[Callable[[float], None]] = None,
    on_log: Optional[Callable[[str], None]] = None,
    total_duration: Optional[float] = None,
) -> tuple[int, str]:
    """
    Run an ffmpeg command asynchronously.

    Args:
        cmd: The full ffmpeg command as a list of strings.
        on_progress: Callback with progress 0.0 - 1.0.
        on_log: Callback with each stderr line.
        total_duration: Total duration in seconds for progress calculation.

    Returns:
        Tuple of (return_code, stderr_output).
    """
    # Ensure -y flag is present for overwrite
    if "-y" not in cmd:
        cmd.insert(1, "-y")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stderr_lines = []
    buffer = ""

    while True:
        chunk = await process.stderr.read(256)
        if not chunk:
            break
        text = chunk.decode("utf-8", errors="replace")
        buffer += text

        while "\r" in buffer or "\n" in buffer:
            # Split on either \r or \n
            line, sep, buffer = re.split(r"([\r\n])", buffer, maxsplit=1)
            line = line.strip()
            if not line:
                continue

            stderr_lines.append(line)

            if on_log:
                on_log(line)

            # Parse progress from ffmpeg output
            if on_progress and total_duration and total_duration > 0:
                time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                if time_match:
                    current_time = _parse_time_to_seconds(time_match.group(1))
                    progress = min(current_time / total_duration, 1.0)
                    on_progress(progress)

    await process.wait()

    if on_progress:
        on_progress(1.0 if process.returncode == 0 else 0.0)

    return process.returncode, "\n".join(stderr_lines)


def get_output_path(input_path: str, suffix: str, output_dir: Optional[str] = None) -> str:
    """Generate an output file path based on input path and desired suffix/extension."""
    directory = output_dir or os.path.dirname(input_path)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(directory, f"{basename}_{suffix}")
