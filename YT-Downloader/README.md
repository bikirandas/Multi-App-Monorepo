# YouTube Downloader (PyQt6)

## Introduction
YouTube Downloader is a desktop application built with **PyQt6** that lets you download YouTube content to your local machine as either:

- **MP3** (audio only)
- **MP4** (video with audio)

The app provides a simple UI with URL input, output folder selection, progress tracking, and status logs so downloads are easy to manage without using terminal commands.

## Features
- Paste a YouTube link and download directly from the UI
- Choose output format: MP3 or MP4
- Select high-quality MP3 bitrate: `256 kbps` or `320 kbps`
- Optionally set a custom output file name
- Select your local save folder
- Standalone packaged build with bundled `ffmpeg`/`ffprobe` for MP3/MP4 processing
- Live progress bar and download status messages
- Error handling for invalid links and conversion issues

## Requirements
- Python `3.11` to `3.14`
- `PyQt6`
- `yt-dlp`
- `ffmpeg` (required only for source/dev runs; bundled in packaged `.exe`)

## Installation
### Option 1: Using pip
```powershell
pip install pyqt6 yt-dlp
```

### Option 2: Using Poetry
```powershell
poetry install
```

## Run the Application
### With Python
```powershell
python -m app.main
```

### With Poetry script
```powershell
poetry run yt-downloader
```

### With Windows executable
```powershell
.\dist\yt-downloader.exe
```

### Install on another Windows PC
From a package that contains `yt-downloader.exe` and the installer scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-YT-Downloader.ps1
```

## Build the `.exe`
Use PyInstaller from the project root:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name yt-downloader --icon app/icons/yt-downloader-icon.ico --add-data "app/icons/yt-downloader-icon.png;app/icons" --add-binary "app/bin/ffmpeg.exe;app/bin" --add-binary "app/bin/ffprobe.exe;app/bin" run.py
```

The executable will be generated at:

```text
dist\yt-downloader.exe
```

Optional transfer package:

```powershell
Compress-Archive -Path .\dist\yt-downloader.exe -DestinationPath .\dist\yt-downloader-portable.zip -Force
```

Installable package (exe + install/uninstall scripts):

```powershell
Copy-Item .\installer\Install-YT-Downloader.ps1 .\dist\Install-YT-Downloader.ps1 -Force
Copy-Item .\installer\Uninstall-YT-Downloader.ps1 .\dist\Uninstall-YT-Downloader.ps1 -Force
Compress-Archive -Path .\dist\yt-downloader.exe,.\dist\Install-YT-Downloader.ps1,.\dist\Uninstall-YT-Downloader.ps1 -DestinationPath .\dist\yt-downloader-installer-package.zip -Force
```

## How to Use
1. Launch the application.
2. Paste a valid YouTube URL in the **YouTube URL** field.
3. Optionally enter a custom name in **File Name**.
4. Select format:
   - **MP3 (Audio)** for audio-only download
   - **MP4 (Video)** for video download
5. If you selected MP3, choose bitrate:
   - **320 kbps (Best)** or
   - **256 kbps**
6. Click **Browse** and choose the destination folder.
7. Click **Download**.
8. Wait for completion and check the output file path shown in the app.

## Notes
- For packaged `.exe` builds generated with the command above, `ffmpeg`/`ffprobe` are already bundled.
- Downloading copyrighted content may violate laws or platform terms depending on usage. Use this tool responsibly.
