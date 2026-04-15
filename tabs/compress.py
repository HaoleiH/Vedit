"""
Compress tab — Reduce video file size with quality presets.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, probe_duration, get_output_path, show_snackbar


PRESETS = {
    "High Quality (CRF 18)": 18,
    "Medium Quality (CRF 23)": 23,
    "Low Quality (CRF 28)": 28,
    "Very Low (CRF 35)": 35,
}

SPEED_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
VIDEO_EXTENSIONS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv"]


def create_compress_tab(page: ft.Page) -> ft.Container:
    """Create the compression tab UI."""

    input_path = ft.TextField(
        label="Input Video File",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    quality_preset = ft.Dropdown(
        label="Quality Preset",
        width=260,
        options=[ft.dropdown.Option(k) for k in PRESETS],
        value="Medium Quality (CRF 23)",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    speed_preset = ft.Dropdown(
        label="Encoding Speed",
        width=200,
        options=[ft.dropdown.Option(s) for s in SPEED_PRESETS],
        value="medium",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    codec = ft.Dropdown(
        label="Codec",
        width=180,
        options=[
            ft.dropdown.Option("libx264", "H.264"),
            ft.dropdown.Option("libx265", "H.265 / HEVC"),
        ],
        value="libx264",
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
        "Compress",
        icon=ft.Icons.COMPRESS_ROUNDED,
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
            dialog_title="Select Video to Compress",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_compress(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        crf = PRESETS[quality_preset.value]
        out_path = get_output_path(input_path.value, "compressed.mp4")

        cmd = [
            "ffmpeg", "-i", input_path.value,
            "-c:v", codec.value,
            "-crf", str(crf),
            "-preset", speed_preset.value,
            "-c:a", "aac",
            "-b:a", "128k",
            out_path,
        ]

        duration = await probe_duration(input_path.value)

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Compressing..."
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
            in_size = os.path.getsize(input_path.value) / (1024 * 1024)
            out_size = os.path.getsize(out_path) / (1024 * 1024)
            ratio = (1 - out_size / in_size) * 100 if in_size > 0 else 0
            progress_text.value = f"✅ Done — {in_size:.1f} MB → {out_size:.1f} MB ({ratio:.0f}% smaller)"
            show_snackbar(page, f"Compressed: {os.path.basename(out_path)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Compression failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_compress

    browse_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        tooltip="Browse",
        on_click=pick_file,
        style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
    )

    return ft.Container(
        expand=True,
        padding=ft.padding.all(24),
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Text("Compress Video", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Reduce video file size using H.264/H.265 encoding with adjustable quality.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row([quality_preset, speed_preset, codec], spacing=16, wrap=True),
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
