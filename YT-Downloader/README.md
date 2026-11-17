# YouTube Downloader (PyQt6)

## Introduction
YouTube Downloader is a desktop application built with **PyQt6** that lets you download YouTube content to your local machine as either:

- **MP3** (audio only)
- **MP4** (video with audio)

The app provides a simple UI with YouTube search, download queue management, URL input, output folder selection, progress tracking, and status logs so downloads are easy to manage without using terminal commands.

## Features

### 🔍 YouTube Search (New in v2.0)
- **Search YouTube directly** from within the app — no need to open a browser
- View search results with thumbnails, titles, channels, duration, and view counts
- Select format (MP3/MP4) and bitrate for each video before adding to queue
- **Works without login** for most videos

### 📋 Download Queue
- **Stack videos from multiple searches** into a single download queue
- Each video can have its own format (MP3/MP4) and bitrate settings
- Queue persists across app restarts
- Batch download all queued videos at once
- Real-time progress tracking for each video

### 🔐 Optional Authentication
- Configure browser cookie extraction for access to age-restricted content
- Avoid "Sign in to confirm you're not a bot" errors
- **Login persists across app restarts** — no need to re-authenticate
- Supports Chrome, Firefox, Edge, Brave, Opera, Vivaldi

### 📥 Direct URL Download
- Paste a YouTube link and download directly (original functionality)
- Choose output format: MP3 or MP4
- Select high-quality MP3 bitrate: `256 kbps` or `320 kbps`
- Optionally set a custom output file name

### General
- Select your local save folder (remembered across sessions)
- Standalone packaged build with bundled `ffmpeg`/`ffprobe` for MP3/MP4 processing
- Live progress bar and download status messages
- Error handling for invalid links and conversion issues
- Modern dark theme UI

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

### Search & Queue (Recommended)
1. Launch the application.
2. Go to the **🔍 Search & Queue** tab.
3. Enter a search query (e.g., "lofi hip hop beats") and click **Search**.
4. Browse the search results:
   - Each result shows a **selection checkbox**, thumbnail, title, channel, duration, and views
   - Select **MP3** or **MP4** format for each video
   - For MP3, choose bitrate (320 kbps or 256 kbps)
   - **Check the checkbox** to add videos to your download queue
   - Uncheck the checkbox to remove videos from queue
5. Perform more searches and add more videos — they stack in the queue!
7. Set the output folder using **Browse**.
8. Click **⬇ Download All** to download everything in the queue.
9. Watch the progress for each video and check the logs.

### Direct URL Download
1. Go to the **📋 Direct URL** tab.
2. Paste a valid YouTube URL in the **YouTube URL** field.
3. Optionally enter a custom name in **File Name**.
4. Select format: **MP3 (Audio)** or **MP4 (Video)**.
5. If you selected MP3, choose bitrate.
6. Click **Browse** and choose the destination folder.
7. Click **Download**.

### Settings (Authentication)
1. Click **⚙ Settings** in the header.
2. Enable authentication if you encounter "Sign in" errors.
3. Select your browser (Chrome, Firefox, Edge, etc.).
4. Click **Test** to verify cookie extraction works.
5. Click **Save** — your login will persist across app restarts.

## Changelog

### v2.0.0
- ✨ **YouTube Search**: Search videos directly from the app
- ✨ **Download Queue**: Stack videos from multiple searches
- ✨ **Batch Download**: Download all queued videos at once
- ✨ **Per-Video Format Selection**: Choose MP3/MP4 for each video
- ✨ **Persistent Settings**: Queue, output folder, and auth persist across restarts
- ✨ **Optional Authentication**: Browser cookie extraction for age-restricted content
- ✨ **Modern Dark Theme**: New sleek UI design
- ✨ **Tabbed Interface**: Separate Search/Queue and Direct URL modes

### v1.0.0
- Initial release with direct URL download

## Notes
- For packaged `.exe` builds generated with the command above, `ffmpeg`/`ffprobe` are already bundled.
- **Search works without login** for most public videos. Authentication is only needed for age-restricted content or if you encounter "Sign in to confirm you're not a bot" errors.
- Download queue and settings are stored locally using Qt's QSettings.
- Downloading copyrighted content may violate laws or platform terms depending on usage. Use this tool responsibly.
