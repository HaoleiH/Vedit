"""
GIF tab — Convert video clip to animated GIF.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, get_output_path, show_snackbar

VIDEO_EXTENSIONS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv"]


def create_gif_tab(page: ft.Page) -> ft.Container:
    """Create the video-to-GIF tab UI."""

    input_path = ft.TextField(
        label="Input Video File",
        read_only=True,
        expand=True,
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    start_time = ft.TextField(
        label="Start Time (HH:MM:SS)",
        width=200,
        value="00:00:00",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    duration = ft.TextField(
        label="Duration (seconds)",
        width=160,
        value="5",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    fps = ft.Dropdown(
        label="FPS",
        width=120,
        options=[ft.dropdown.Option(str(f)) for f in [10, 15, 20, 24, 30]],
        value="15",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    width_field = ft.TextField(
        label="Width (px)",
        width=140,
        value="480",
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
        "Create GIF",
        icon=ft.Icons.GIF_ROUNDED,
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
            dialog_title="Select Video for GIF",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_gif(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        out_path = get_output_path(input_path.value, "output.gif")
        w = width_field.value
        f = fps.value

        # Two-pass GIF for better quality: generate palette then use it
        palette_path = get_output_path(input_path.value, "palette.png")

        # Pass 1: Generate palette
        cmd1 = [
            "ffmpeg",
            "-ss", start_time.value,
            "-t", duration.value,
            "-i", input_path.value,
            "-vf", f"fps={f},scale={w}:-1:flags=lanczos,palettegen",
            palette_path,
        ]

        # Pass 2: Create GIF using palette
        cmd2 = [
            "ffmpeg",
            "-ss", start_time.value,
            "-t", duration.value,
            "-i", input_path.value,
            "-i", palette_path,
            "-lavfi", f"fps={f},scale={w}:-1:flags=lanczos [x]; [x][1:v] paletteuse",
            out_path,
        ]

        progress_bar.visible = True
        progress_bar.value = None  # Indeterminate
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Pass 1/2: Generating palette..."
        page.update()

        def on_log(line):
            log_output.value = (log_output.value or "") + line + "\n"
            page.update()

        code1, _ = await run_ffmpeg(cmd1, on_log=on_log)

        if code1 != 0:
            run_btn.disabled = False
            progress_bar.value = 0
            progress_text.value = "❌ Error in palette generation"
            show_snackbar(page, "GIF creation failed at palette stage.", is_error=True)
            page.update()
            return

        progress_text.value = "Pass 2/2: Creating GIF..."
        page.update()

        code2, _ = await run_ffmpeg(cmd2, on_log=on_log)

        run_btn.disabled = False
        if code2 == 0:
            try:
                os.remove(palette_path)
            except OSError:
                pass
            gif_size = os.path.getsize(out_path) / (1024 * 1024)
            progress_bar.value = 1.0
            progress_text.value = f"✅ Done — {out_path} ({gif_size:.1f} MB)"
            show_snackbar(page, f"GIF created: {os.path.basename(out_path)}")
        else:
            progress_bar.value = 0
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "GIF creation failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_gif

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
                ft.Text("Video to GIF", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Convert a video clip to a high-quality animated GIF using two-pass palette generation.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row([start_time, duration, fps, width_field], spacing=16, wrap=True),
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
