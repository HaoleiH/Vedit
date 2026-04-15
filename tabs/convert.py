"""
Convert tab — Format conversion between video/audio formats.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, probe_duration, get_output_path, show_snackbar


VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "ts"]
AUDIO_FORMATS = ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"]
ALL_FORMATS = VIDEO_FORMATS + AUDIO_FORMATS


def create_convert_tab(page: ft.Page) -> ft.Container:
    """Create the format conversion tab UI."""

    input_path = ft.TextField(
        label="Input File",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    output_format = ft.Dropdown(
        label="Output Format",
        width=180,
        options=[ft.dropdown.Option(f) for f in ALL_FORMATS],
        value="mp4",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    video_codec = ft.Dropdown(
        label="Video Codec",
        width=180,
        options=[
            ft.dropdown.Option("copy", "Copy (No Re-encode)"),
            ft.dropdown.Option("libx264", "H.264"),
            ft.dropdown.Option("libx265", "H.265 / HEVC"),
            ft.dropdown.Option("libvpx-vp9", "VP9"),
            ft.dropdown.Option("libaom-av1", "AV1"),
        ],
        value="copy",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    audio_codec = ft.Dropdown(
        label="Audio Codec",
        width=180,
        options=[
            ft.dropdown.Option("copy", "Copy (No Re-encode)"),
            ft.dropdown.Option("aac", "AAC"),
            ft.dropdown.Option("libmp3lame", "MP3"),
            ft.dropdown.Option("libvorbis", "Vorbis"),
            ft.dropdown.Option("flac", "FLAC"),
        ],
        value="copy",
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
        "Convert",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
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
            dialog_title="Select Input File",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_FORMATS + AUDIO_FORMATS + ["3gp", "mpeg", "mpg"],
        )
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_convert(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        fmt = output_format.value
        out_path = get_output_path(input_path.value, f"converted.{fmt}")

        cmd = ["ffmpeg", "-i", input_path.value]

        if video_codec.value != "copy":
            cmd += ["-c:v", video_codec.value]
        else:
            cmd += ["-c:v", "copy"]

        if audio_codec.value != "copy":
            cmd += ["-c:a", audio_codec.value]
        else:
            cmd += ["-c:a", "copy"]

        cmd.append(out_path)

        duration = await probe_duration(input_path.value)

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Starting..."
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
            show_snackbar(page, f"Conversion complete: {os.path.basename(out_path)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Conversion failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_convert

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
                ft.Text("Format Conversion", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Convert video or audio files between different formats.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row(
                    [output_format, video_codec, audio_codec],
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
