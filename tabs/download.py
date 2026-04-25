"""
Download tab — Download video and audio using yt-dlp.
"""

import asyncio
import os
import re
import flet as ft

from utils.ffmpeg_runner import show_snackbar
from utils.exe_resolver import get_executable_path


async def run_ytdlp(
    cmd: list[str],
    on_progress=None,
    on_log=None,
) -> tuple[int, str]:
    """
    Run yt-dlp command asynchronously.
    """
    exe = get_executable_path(cmd[0]) or cmd[0]
    
    process = await asyncio.create_subprocess_exec(
        exe,
        *cmd[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    log_lines = []

    async def read_stream(stream, is_stderr=False):
        buffer = ""
        while True:
            chunk = await stream.read(256)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            buffer += text

            while "\r" in buffer or "\n" in buffer:
                line, sep, buffer = re.split(r"([\r\n])", buffer, maxsplit=1)
                line = line.strip()
                if not line:
                    continue

                log_lines.append(line)
                if on_log:
                    on_log(line)

                # Parse yt-dlp progress: [download]  15.0% of ...
                if on_progress and not is_stderr:
                    # Example: [download]  15.0% of 1.23GiB at 1.00MiB/s ETA 00:10
                    match = re.search(r"\[download\]\s+([\d\.]+)%", line)
                    if match:
                        try:
                            progress = float(match.group(1)) / 100.0
                            on_progress(progress)
                        except ValueError:
                            pass

    await asyncio.gather(
        read_stream(process.stdout),
        read_stream(process.stderr, is_stderr=True)
    )

    await process.wait()

    if on_progress:
        on_progress(1.0 if process.returncode == 0 else 0.0)

    return process.returncode, "\n".join(log_lines)


def create_download_tab(page: ft.Page) -> ft.Container:
    """Create the yt-dlp download tab UI."""

    url_input = ft.TextField(
        label="Video URL",
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
        hint_text="https://www.youtube.com/...",
    )
    
    output_dir_input = ft.TextField(
        label="Output Directory",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
        value=os.path.expanduser("~/Downloads"),
    )

    download_type = ft.Dropdown(
        label="Download Type",
        width=180,
        options=[
            ft.dropdown.Option("video_audio", "Video + Audio"),
            ft.dropdown.Option("video_only", "Video Only"),
            ft.dropdown.Option("audio_only", "Audio Only"),
        ],
        value="video_audio",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )

    video_format = ft.Dropdown(
        label="Video Format",
        width=150,
        options=[
            ft.dropdown.Option("best", "Best"),
            ft.dropdown.Option("mp4", "MP4"),
            ft.dropdown.Option("mkv", "MKV"),
            ft.dropdown.Option("webm", "WEBM"),
        ],
        value="best",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )

    audio_format = ft.Dropdown(
        label="Audio Format",
        width=150,
        options=[
            ft.dropdown.Option("best", "Best"),
            ft.dropdown.Option("mp3", "MP3"),
            ft.dropdown.Option("m4a", "M4A"),
            ft.dropdown.Option("flac", "FLAC"),
            ft.dropdown.Option("wav", "WAV"),
        ],
        value="best",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )

    quality = ft.Dropdown(
        label="Video Quality",
        width=150,
        options=[
            ft.dropdown.Option("best", "Best"),
            ft.dropdown.Option("2160", "4K (2160p)"),
            ft.dropdown.Option("1440", "2K (1440p)"),
            ft.dropdown.Option("1080", "1080p"),
            ft.dropdown.Option("720", "720p"),
            ft.dropdown.Option("480", "480p"),
        ],
        value="best",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )

    def on_type_change(e):
        t = download_type.value
        video_format.disabled = t == "audio_only"
        quality.disabled = t == "audio_only"
        audio_format.disabled = t == "video_only"
        page.update()

    download_type.on_change = on_type_change

    progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.Colors.PRIMARY)
    progress_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
    log_output = ft.TextField(
        label="yt-dlp Output",
        multiline=True,
        min_lines=8,
        max_lines=8,
        read_only=True,
        value="",
        text_size=11,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    run_btn = ft.Button(
        "Download",
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
            padding=ft.Padding.symmetric(horizontal=32, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def pick_folder(_):
        result = await file_picker.get_directory_path(
            dialog_title="Select Output Directory",
        )
        if result:
            output_dir_input.value = result
            page.update()

    async def run_download(_):
        if not url_input.value:
            show_snackbar(page, "Please enter a valid URL.", is_error=True)
            return

        cmd = ["yt-dlp"]
        
        ffmpeg_path = get_executable_path("ffmpeg")
        if ffmpeg_path:
            cmd.extend(["--ffmpeg-location", ffmpeg_path])
            
        out_tpl = os.path.join(output_dir_input.value, "%(title)s.%(ext)s")
        cmd.extend(["-o", out_tpl, "--newline"])
        
        dtype = download_type.value
        q = quality.value
        
        # Build format string
        if dtype == "audio_only":
            cmd.extend(["-x"])
            if audio_format.value != "best":
                cmd.extend(["--audio-format", audio_format.value])
        elif dtype == "video_only":
            fmt_str = f"bestvideo"
            if q != "best":
                fmt_str += f"[height<={q}]"
            cmd.extend(["-f", fmt_str])
            if video_format.value != "best":
                cmd.extend(["--remux-video", video_format.value])
        else:
            # Video + Audio
            v_fmt = "bestvideo"
            if q != "best":
                v_fmt += f"[height<={q}]"
                
            a_fmt = "bestaudio"
            # Using /best as fallback if video+audio formats aren't separated
            fmt_str = f"{v_fmt}+{a_fmt}/best[height<={q}]" if q != "best" else f"bestvideo+bestaudio/best"
            cmd.extend(["-f", fmt_str])
            
            if video_format.value != "best":
                cmd.extend(["--merge-output-format", video_format.value])

        cmd.append(url_input.value)

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Starting download..."
        page.update()

        def on_progress(p):
            progress_bar.value = p
            progress_text.value = f"{int(p * 100)}%"
            page.update()

        def on_log(line):
            # To avoid the log text getting too huge, maybe keep the last 50 lines.
            lines = log_output.value.splitlines()
            lines.append(line)
            if len(lines) > 50:
                lines = lines[-50:]
            log_output.value = "\n".join(lines)
            page.update()

        try:
            code, out = await run_ytdlp(cmd, on_progress, on_log)
        except FileNotFoundError:
            run_btn.disabled = False
            progress_text.value = "❌ Error — yt-dlp executable not found"
            show_snackbar(page, "yt-dlp is missing. Please download it and place it in the application folder or add it to PATH.", is_error=True)
            page.update()
            return
        except Exception as e:
            run_btn.disabled = False
            progress_text.value = f"❌ Error: {e}"
            show_snackbar(page, f"Error: {e}", is_error=True)
            page.update()
            return

        run_btn.disabled = False
        if code == 0:
            progress_text.value = "✅ Download Complete"
            show_snackbar(page, "Download complete!")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Download failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_download

    browse_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        tooltip="Browse",
        on_click=pick_folder,
        style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
    )

    # Initialize state
    on_type_change(None)

    return ft.Container(
        expand=True,
        padding=ft.Padding.all(24),
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Text("Download Media", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Download video and audio from various platforms using yt-dlp.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                url_input,
                ft.Row([output_dir_input, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row(
                    [download_type, quality, video_format, audio_format],
                    spacing=16,
                    wrap=True,
                ),
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
