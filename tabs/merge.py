"""
Merge tab — Concatenate multiple video files into one.
"""

import os
import flet as ft

from utils.ffmpeg_runner import run_ffmpeg, probe_duration, show_snackbar

VIDEO_EXTENSIONS = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "ts"]


def create_merge_tab(page: ft.Page) -> ft.Container:
    """Create the merge videos tab UI."""

    file_list_data: list[str] = []

    file_list_view = ft.ListView(
        spacing=4,
        height=180,
        auto_scroll=True,
    )
    file_count_text = ft.Text("No files added", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

    output_path = ft.TextField(
        label="Output File Path",
        expand=True,
        value="",
        hint_text="e.g., C:\\Videos\\merged_output.mp4",
        border_color=ft.Colors.OUTLINE_VARIANT,
    )

    transcode = ft.Checkbox(
        label="Re-encode all files (use if formats differ)",
        value=False,
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
    run_btn = ft.Button(
        "Merge",
        icon=ft.Icons.MERGE_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
            padding=ft.Padding.symmetric(horizontal=32, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    def _rebuild_list_view():
        file_list_view.controls.clear()
        for i, fp in enumerate(file_list_data):
            idx = i

            def make_remove(index):
                def remove(_):
                    file_list_data.pop(index)
                    _rebuild_list_view()
                return remove

            def make_move_up(index):
                def move_up(_):
                    if index > 0:
                        file_list_data[index], file_list_data[index - 1] = file_list_data[index - 1], file_list_data[index]
                        _rebuild_list_view()
                return move_up

            def make_move_down(index):
                def move_down(_):
                    if index < len(file_list_data) - 1:
                        file_list_data[index], file_list_data[index + 1] = file_list_data[index + 1], file_list_data[index]
                        _rebuild_list_view()
                return move_down

            row = ft.Container(
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                content=ft.Row(
                    controls=[
                        ft.Text(f"{i + 1}.", size=13, weight=ft.FontWeight.BOLD, width=30),
                        ft.Text(os.path.basename(fp), size=13, expand=True, tooltip=fp),
                        ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_size=16, on_click=make_move_up(idx), tooltip="Move up"),
                        ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_size=16, on_click=make_move_down(idx), tooltip="Move down"),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=16, on_click=make_remove(idx), tooltip="Remove", icon_color=ft.Colors.ERROR),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            )
            file_list_view.controls.append(row)

        file_count_text.value = f"{len(file_list_data)} file(s) added"
        page.update()

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def pick_files(_):
        result = await file_picker.pick_files(
            dialog_title="Select Videos to Merge",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=VIDEO_EXTENSIONS,
        )
        if result:
            for f in result:
                file_list_data.append(f.path)
            _rebuild_list_view()

    def clear_files(_):
        file_list_data.clear()
        _rebuild_list_view()

    async def run_merge(_):
        if len(file_list_data) < 2:
            show_snackbar(page, "Please add at least 2 files to merge.", is_error=True)
            return

        out = output_path.value.strip()
        if not out:
            first_dir = os.path.dirname(file_list_data[0])
            out = os.path.join(first_dir, "merged_output.mp4")
            output_path.value = out
            page.update()

        # Calculate total duration for progress
        total_dur = 0.0
        for fp in file_list_data:
            d = await probe_duration(fp)
            if d:
                total_dur += d

        progress_bar.visible = True
        progress_bar.value = 0
        run_btn.disabled = True
        log_output.value = ""
        progress_text.value = "Merging..."
        page.update()

        def on_progress(p):
            progress_bar.value = p
            progress_text.value = f"{int(p * 100)}%"
            page.update()

        def on_log(line):
            log_output.value = (log_output.value or "") + line + "\n"
            page.update()

        if transcode.value:
            inputs = []
            for fp in file_list_data:
                inputs += ["-i", fp]

            filter_str = ""
            for i in range(len(file_list_data)):
                filter_str += f"[{i}:v:0][{i}:a:0]"
            filter_str += f"concat=n={len(file_list_data)}:v=1:a=1[outv][outa]"

            cmd = [
                "ffmpeg",
                *inputs,
                "-filter_complex", filter_str,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                out,
            ]

            code, _ = await run_ffmpeg(cmd, on_progress, on_log, total_dur if total_dur > 0 else None)
        else:
            concat_file = os.path.join(os.path.dirname(file_list_data[0]), "_concat_list.txt")
            with open(concat_file, "w", encoding="utf-8") as f:
                for fp in file_list_data:
                    escaped = fp.replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                out,
            ]

            code, _ = await run_ffmpeg(cmd, on_progress, on_log, total_dur if total_dur > 0 else None)

            try:
                os.remove(concat_file)
            except OSError:
                pass

        run_btn.disabled = False
        if code == 0:
            progress_text.value = f"✅ Done — {out}"
            show_snackbar(page, f"Merged: {os.path.basename(out)}")
        else:
            progress_text.value = "❌ Error — check log output"
            show_snackbar(page, "Merge failed. Check log.", is_error=True)
        page.update()

    run_btn.on_click = run_merge

    add_btn = ft.Button(
        "Add Files",
        icon=ft.Icons.ADD_ROUNDED,
        on_click=pick_files,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    clear_btn = ft.Button(
        "Clear All",
        icon=ft.Icons.CLEAR_ALL_ROUNDED,
        on_click=clear_files,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding.all(24),
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Text("Merge Videos", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Concatenate multiple video files into a single output file. Reorder with arrows.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row([add_btn, clear_btn, file_count_text], spacing=12),
                ft.Container(
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=12,
                    padding=ft.Padding.all(8),
                    content=file_list_view,
                ),
                transcode,
                ft.Row([output_path]),
                run_btn,
                progress_bar,
                progress_text,
                log_output,
            ],
        ),
    )
