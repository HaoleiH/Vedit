"""
Extract Audio tab — Extract audio track from video files.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, probe_duration, get_output_path, show_snackbar


AUDIO_FORMATS = ["mp3", "wav", "flac", "aac", "ogg", "m4a"]
BITRATE_OPTIONS = ["64k", "128k", "192k", "256k", "320k"]
VIDEO_EXTENSIONS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "ts", "3gp"]


def create_extract_audio_tab(page: ft.Page) -> ft.Container:
    """Create the audio extraction tab UI."""

    input_path = ft.TextField(
        label="Input Video File",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    audio_format = ft.Dropdown(
        label="Audio Format",
        width=180,
        options=[ft.dropdown.Option(f) for f in AUDIO_FORMATS],
        value="mp3",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    bitrate = ft.Dropdown(
        label="Bitrate",
        width=180,
        options=[ft.dropdown.Option(b) for b in BITRATE_OPTIONS],
        value="192k",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.Colors.PRIMARY)
    progress_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
    log_output = ft.TextField(
        label="FFmpeg Output",
        multiline=True,
        min_lines=6,
        max_lines=6,
        read_only=True,
        value="",
        text_size=11,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    run_btn = ft.ElevatedButton(
        "Extract Audio",
        icon=ft.Icons.MUSIC_NOTE_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def pick_file(_):
        result = await file_picker.pick_files(
            dialog_title="Select Video File",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_extract(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        fmt = audio_format.value
        out_path = get_output_path(input_path.value, f"audio.{fmt}")

        codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "flac": "flac",
            "aac": "aac",
            "ogg": "libvorbis",
            "m4a": "aac",
        }
        codec = codec_map.get(fmt, "copy")

        cmd = [
            "ffmpeg", "-i", input_path.value,
            "-vn",
            "-c:a", codec,
            "-b:a", bitrate.value,
            out_path,
        ]

        duration = await probe_duration(input_path.value)

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Extracting audio..."
        page.update()

        def on_progress(p):
            progress_bar.value = p
            progress_text.value = f"{int(p * 100)}%"
            page.update()

        def on_log(line):
            log_output.value = (log_output.value or "") + line + "\n"
            page.update()

        code, _ = await run_ffmpeg(cmd, on_progress, on_log, duration)

        run_btn.disabled = False
        if code == 0:
            progress_text.value = f"✅ Done — {out_path}"
            show_snackbar(page, f"Audio extracted: {os.path.basename(out_path)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Extraction failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_extract

    browse_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        tooltip="Browse",
        on_click=pick_file,
        style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
    )

    return ft.Container(
        padding=ft.padding.all(24),
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Text("Extract Audio", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Extract the audio track from a video file into a standalone audio file.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row([audio_format, bitrate], spacing=16),
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
