# 🎬 FFmpeg Studio

A modern, dark-themed desktop GUI for common FFmpeg operations — built with [Flet](https://flet.dev) (Python).

No more memorizing complex command-line flags. Just pick your files, tweak a few settings, and hit **Run**.

---

## ✨ Features

| Tab | Description |
|-----|-------------|
| 🔄 **Convert** | Convert between video/audio formats (MP4, AVI, MKV, MOV, MP3, WAV, FLAC, etc.) with codec selection |
| 🎵 **Extract Audio** | Pull the audio track out of any video — choose format (MP3/WAV/FLAC/AAC/OGG/M4A) and bitrate |
| ✂️ **Trim** | Cut a segment by start/end time, with optional re-encode for frame-accurate cuts |
| 📦 **Compress** | Shrink video file size using CRF quality presets (18–35), encoding speed, and H.264/H.265 |
| 📐 **Resize** | Scale to preset resolutions (4K → 360p) or custom dimensions, with aspect ratio lock |
| 🎞️ **GIF** | Create high-quality animated GIFs using two-pass palette generation |
| 🔗 **Merge** | Concatenate multiple videos with drag-to-reorder — supports both stream copy and re-encode modes |

### Highlights

- **Real-time progress** — progress bar driven by FFmpeg's time output
- **Live log output** — scrollable FFmpeg stderr display for debugging
- **Async throughout** — non-blocking UI during processing
- **FFmpeg auto-detection** — friendly error screen with download link if FFmpeg is missing
- **Dark theme** — deep purple accent, clean Material Design 3

---

## 📋 Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **[FFmpeg](https://ffmpeg.org/download.html)** — must be on your system `PATH`

### Verify FFmpeg is installed

```bash
ffmpeg -version
ffprobe -version
```

If not installed, download from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager:

```bash
# Windows (winget)
winget install FFmpeg

# Windows (scoop)
scoop install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd flet-test
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Run the app

```bash
uv run python main.py
```

The FFmpeg Studio window will open with the navigation rail on the left.

---

## 📁 Project Structure

```
flet-test/
├── main.py                  # App entry point — theme, NavigationRail, tab routing
├── tabs/
│   ├── convert.py           # Format conversion
│   ├── extract_audio.py     # Audio extraction from video
│   ├── trim.py              # Cut segments with start/end times
│   ├── compress.py          # CRF-based video compression
│   ├── resize.py            # Resolution scaling
│   ├── gif.py               # Two-pass high-quality GIF creation
│   └── merge.py             # Concatenate multiple videos
├── utils/
│   └── ffmpeg_runner.py     # Async subprocess runner with progress parsing
├── pyproject.toml
└── README.md
```

---

## 🛠️ How It Works

Each tab follows the same pattern:

1. **Pick a file** → native file picker dialog
2. **Configure settings** → dropdowns, text fields, checkboxes
3. **Click Run** → async FFmpeg subprocess launches
4. **Watch progress** → real-time progress bar + log output
5. **Get notified** → snackbar with output file path on completion

Under the hood, `utils/ffmpeg_runner.py` handles:
- Running FFmpeg as an async subprocess (`asyncio.create_subprocess_exec`)
- Parsing `time=HH:MM:SS.ms` from stderr to calculate progress percentage
- Probing media duration via `ffprobe` for progress normalization

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| [flet](https://pypi.org/project/flet/) | Cross-platform UI framework (Flutter-based) |

---

## 📄 License

MIT
