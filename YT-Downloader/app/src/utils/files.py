import sys
from pathlib import Path


def resolve_icon_path() -> Path | None:
    icon_name = "yt-downloader-icon.png"
    app_root = Path(__file__).resolve().parents[2]
    candidates = [app_root / "icons" / icon_name]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled_root = Path(meipass)
        candidates.append(bundled_root / "app" / "icons" / icon_name)
        candidates.append(bundled_root / "icons" / icon_name)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_ffmpeg_location() -> Path | None:
    candidates: list[Path] = []

    app_root = Path(__file__).resolve().parents[2]
    candidates.append(app_root / "bin")

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled_root = Path(meipass)
        candidates.append(bundled_root / "app" / "bin")
        candidates.append(bundled_root / "bin")

    for candidate in candidates:
        if (candidate / "ffmpeg.exe").exists():
            return candidate
    return None
