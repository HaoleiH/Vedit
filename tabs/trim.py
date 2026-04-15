"""
Trim tab — Cut a segment from a video/audio file.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, get_output_path, show_snackbar


def create_trim_tab(page: ft.Page) -> ft.Container:
    """Create the trim tab UI."""

    input_path = ft.TextField(
        label="Input File",
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
    end_time = ft.TextField(
        label="End Time (HH:MM:SS)",
        width=200,
        value="00:00:30",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )
    re_encode = ft.Checkbox(label="Re-encode (slower, precise cuts)", value=False)

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
        "Trim",
        icon=ft.Icons.CONTENT_CUT_ROUNDED,
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
        result = await file_picker.pick_files(dialog_title="Select File to Trim")
        if result:
            input_path.value = result[0].path
            page.update()

    async def run_trim(_):
        if not input_path.value:
            show_snackbar(page, "Please select an input file.", is_error=True)
            return

        ext = os.path.splitext(input_path.value)[1]
        out_path = get_output_path(input_path.value, f"trimmed{ext}")

        cmd = [
            "ffmpeg",
            "-ss", start_time.value,
            "-to", end_time.value,
            "-i", input_path.value,
        ]

        if re_encode.value:
            cmd += ["-c:v", "libx264", "-c:a", "aac"]
        else:
            cmd += ["-c", "copy"]

        cmd.append(out_path)

        progress_bar.visible = True
        progress_bar.value = None  # Indeterminate
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Trimming..."
        page.update()

        def on_log(line):
            log_output.value = (log_output.value or "") + line + "\n"
            page.update()

        code, _ = await run_ffmpeg(cmd, on_log=on_log)

        run_btn.disabled = False
        progress_bar.value = 1.0 if code == 0 else 0.0
        if code == 0:
            progress_text.value = f"✅ Done — {out_path}"
            show_snackbar(page, f"Trimmed: {os.path.basename(out_path)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Trim failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_trim

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
                ft.Text("Trim / Cut", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Cut a segment from a video or audio file by specifying start and end times.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([input_path, browse_btn], alignment=ft.MainAxisAlignment.START),
                ft.Row([start_time, end_time], spacing=16),
                re_encode,
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
