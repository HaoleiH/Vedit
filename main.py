"""
FFmpeg GUI — A modern desktop application built with Flet.

Provides common FFmpeg operations through an intuitive interface:
- Format Conversion
- Audio Extraction
- Trim / Cut
- Video Compression
- Resolution Resize
- Video to GIF
- Video Merging
"""

import asyncio
import flet as ft

from utils.ffmpeg_runner import check_ffmpeg
from tabs.convert import create_convert_tab
from tabs.extract_audio import create_extract_audio_tab
from tabs.trim import create_trim_tab
from tabs.compress import create_compress_tab
from tabs.resize import create_resize_tab
from tabs.gif import create_gif_tab
from tabs.merge import create_merge_tab


# ── Theme colors ──────────────────────────────────────────────────────────
SEED_COLOR = ft.Colors.DEEP_PURPLE
BG_DARK = "#0f0f17"
SURFACE_DARK = "#1a1a2e"
NAV_BG = "#12121e"


async def main(page: ft.Page):
    # ── Page setup ────────────────────────────────────────────────────────
    page.title = "FFmpeg Studio"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DARK
    page.padding = 0
    page.window.width = 1100
    page.window.height = 750
    page.window.min_width = 900
    page.window.min_height = 600

    page.theme = ft.Theme(
        color_scheme_seed=SEED_COLOR,
        font_family="Segoe UI",
    )

    page.fonts = {
        "Segoe UI": "Segoe UI",
    }

    # ── Check FFmpeg availability ─────────────────────────────────────────
    ffmpeg_ok = await check_ffmpeg()

    if not ffmpeg_ok:
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.ERROR),
                        ft.Text("FFmpeg Not Found", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Please install FFmpeg and ensure it is available on your system PATH.",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.TextButton(
                            "Download FFmpeg",
                            url="https://ffmpeg.org/download.html",
                            icon=ft.Icons.DOWNLOAD,
                        ),
                    ],
                ),
            )
        )
        return

    # ── Build tab content ─────────────────────────────────────────────────
    tab_builders = [
        lambda: create_convert_tab(page),
        lambda: create_extract_audio_tab(page),
        lambda: create_trim_tab(page),
        lambda: create_compress_tab(page),
        lambda: create_resize_tab(page),
        lambda: create_gif_tab(page),
        lambda: create_merge_tab(page),
    ]

    # Lazy tab cache
    tab_cache: dict[int, ft.Control] = {}

    content_area = ft.Container(
        expand=True,
        bgcolor=SURFACE_DARK,
        border_radius=ft.BorderRadius.only(top_left=20),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    )

    def get_tab(index: int) -> ft.Control:
        if index not in tab_cache:
            tab_cache[index] = ft.Column(
                controls=[tab_builders[index]()],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        return tab_cache[index]

    def on_nav_change(e):
        idx = e.control.selected_index
        content_area.content = get_tab(idx)
        page.update()

    # ── Navigation Rail ───────────────────────────────────────────────────
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=90,
        min_extended_width=200,
        group_alignment=-0.9,
        bgcolor=NAV_BG,
        indicator_color=ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY),
        on_change=on_nav_change,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.SWAP_HORIZ_OUTLINED,
                selected_icon=ft.Icons.SWAP_HORIZ_ROUNDED,
                label="Convert",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.MUSIC_NOTE_OUTLINED,
                selected_icon=ft.Icons.MUSIC_NOTE_ROUNDED,
                label="Audio",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CONTENT_CUT_OUTLINED,
                selected_icon=ft.Icons.CONTENT_CUT_ROUNDED,
                label="Trim",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.COMPRESS_OUTLINED,
                selected_icon=ft.Icons.COMPRESS_ROUNDED,
                label="Compress",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ASPECT_RATIO_OUTLINED,
                selected_icon=ft.Icons.ASPECT_RATIO_ROUNDED,
                label="Resize",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.GIF_OUTLINED,
                selected_icon=ft.Icons.GIF_ROUNDED,
                label="GIF",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.MERGE_OUTLINED,
                selected_icon=ft.Icons.MERGE_ROUNDED,
                label="Merge",
            ),
        ],
        leading=ft.Container(
            padding=ft.Padding.only(top=16, bottom=8),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Container(
                        width=48,
                        height=48,
                        border_radius=14,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=[ft.Colors.DEEP_PURPLE_400, ft.Colors.INDIGO_400],
                        ),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.MOVIE_FILTER_ROUNDED, size=26, color=ft.Colors.WHITE),
                    ),
                    ft.Text("FFmpeg", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Studio", size=9, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
            ),
        ),
    )

    # ── Load initial tab ──────────────────────────────────────────────────
    content_area.content = get_tab(0)

    # ── Layout ────────────────────────────────────────────────────────────
    page.add(
        ft.Row(
            expand=True,
            spacing=0,
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
                content_area,
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)
