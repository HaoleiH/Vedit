"""
Resize tab — Change video resolution.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, probe_duration, get_output_path, show_snackbar


RESOLUTION_PRESETS = {
    "4K (3840×2160)": "3840:2160",
    "1440p (2560×1440)": "2560:1440",
    "1080p (1920×1080)": "1920:1080",
    "720p (1280×720)": "1280:720",
    "480p (854×480)": "854:480",
    "360p (640×360)": "640:360",
    "Custom": "custom",
}

VIDEO_EXTENSIONS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv"]


def create_resize_tab(page: ft.Page) -> ft.Container:
    """Create the resize tab UI."""

    input_path = ft.TextField(
        label="Input Video File",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    resolution = ft.Dropdown(
        label="Resolution",
        width=240,
        options=[ft.dropdown.Option(k) for k in RESOLUTION_PRESETS],
        value="1080p (1920×1080)",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    custom_width = ft.TextField(
        label="Width",
        width=120,
        value="1280",
        visible=False,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    custom_height = ft.TextField(
        label="Height",
        width=120,
        value="720",
        visible=False,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    keep_aspect = ft.Checkbox(label="Maintain aspect ratio (auto-adjust height)", value=True)

    def on_resolution_change(e):
        is_custom = resolution.value == "Custom"
        custom_width.visible = is_custom
        custom_height.visible = is_custom
        page.update()

    resolution.on_change = on_resolution_change

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
        "Resize",
        icon=ft.Icons.ASPECT_RATIO_ROUNDED,
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
            dialog_title="Select Video to Resize",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_resize(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        if resolution.value == "Custom":
            w = custom_width.value
            h = custom_height.value
        else:
            res = RESOLUTION_PRESETS[resolution.value]
            w, h = res.split(":")

        if keep_aspect.value:
            scale_filter = f"scale={w}:-2"
        else:
            scale_filter = f"scale={w}:{h}"

        out_path = get_output_path(input_path.value, f"resized_{w}p.mp4")

        cmd = [
            "ffmpeg", "-i", input_path.value,
            "-vf", scale_filter,
            "-c:v", "libx264",
            "-crf", "23",
            "-c:a", "copy",
            out_path,
        ]

        duration = await probe_duration(input_path.value)

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Resizing..."
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
            show_snackbar(page, f"Resized: {os.path.basename(out_path)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Resize failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_resize

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
                ft.Text("Resize Video", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Scale video to a different resolution with preset or custom dimensions.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row([resolution, custom_width, custom_height], spacing=16),
                keep_aspect,
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
