import re
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.src.logging import DownloadLogger
from app.src.constants import RESERVED
from app.src.utils.files import resolve_ffmpeg_location


class DownloadWorker(QObject):
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    completed = pyqtSignal(bool, str)

    def __init__(
        self,
        url: str,
        output_dir: str,
        target_format: str,
        custom_file_name: str | None = None,
        mp3_bitrate: str = "320",
    ) -> None:
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.target_format = target_format
        self.custom_file_name = self._sanitize_file_name(custom_file_name)
        self.mp3_bitrate = mp3_bitrate if mp3_bitrate in {"256", "320"} else "320"

    @staticmethod
    def _sanitize_file_name(file_name: str | None) -> str | None:
        if not file_name:
            return None
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", file_name).strip()
        sanitized = sanitized.rstrip(". ")
        for known_ext in (".mp3", ".mp4", ".m4a", ".webm", ".mkv", ".wav", ".aac", ".ogg"):
            if sanitized.lower().endswith(known_ext):
                sanitized = sanitized[: -len(known_ext)].rstrip(". ")
                break
        if sanitized and sanitized.split(".")[0].upper() in RESERVED:
            sanitized = f"{sanitized}_"
        return sanitized or None

    @staticmethod
    def _extract_percentage(raw_percent: str) -> int | None:
        cleaned = re.sub(r"\x1b\[[0-9;]*m", "", raw_percent).strip()
        match = re.search(r"(\d+(?:\.\d+)?)%", cleaned)
        if not match:
            return None
        value = float(match.group(1))
        return max(0, min(100, int(value)))

    def _on_progress(self, data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            raw_percent = data.get("_percent_str")
            if raw_percent:
                percent = self._extract_percentage(raw_percent)
                if percent is not None:
                    self.progress_changed.emit(percent)

            speed = (data.get("_speed_str") or "").strip()
            eta = (data.get("_eta_str") or "").strip()
            if speed or eta:
                details = " | ".join(part for part in [f"Speed: {speed}" if speed else "", f"ETA: {eta}" if eta else ""] if part)
                self.status_changed.emit(f"Downloading... {details}")
            else:
                self.status_changed.emit("Downloading...")

        elif status == "finished":
            self.progress_changed.emit(100)
            self.status_changed.emit("Download complete. Processing file...")

    @pyqtSlot()
    def run(self) -> None:
        self.status_changed.emit("Starting download...")
        self.progress_changed.emit(0)

        output_template = "%(title)s.%(ext)s"
        if self.custom_file_name:
            output_template = f"{self.custom_file_name}.%(ext)s"
            self.log_message.emit(f"Custom filename selected: {self.custom_file_name}")

        ydl_options = {
            "outtmpl": str(Path(self.output_dir) / output_template),
            "noplaylist": True,
            "progress_hooks": [self._on_progress],
            "logger": DownloadLogger(self.log_message.emit),
            "quiet": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["configs", "webpage"],
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        }
        ffmpeg_location = resolve_ffmpeg_location()
        if ffmpeg_location:
            ydl_options["ffmpeg_location"] = str(ffmpeg_location)

        if self.target_format == "mp3":
            self.status_changed.emit(f"Downloading audio for MP3 conversion ({self.mp3_bitrate} kbps)...")
            ydl_options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": self.mp3_bitrate,
                        }
                    ],
                }
            )
        else:
            ydl_options.update(
                {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
                    "merge_output_format": "mp4",
                }
            )

        try:
            with YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(self.url, download=True)
                downloaded_path = Path(ydl.prepare_filename(info))
                if self.target_format == "mp3":
                    downloaded_path = downloaded_path.with_suffix(".mp3")

            self.completed.emit(True, str(downloaded_path))
        except DownloadError as exc:
            message = str(exc)
            if "ffmpeg" in message.lower() and self.target_format == "mp3":
                message = (
                    "MP3 conversion needs FFmpeg installed and available in PATH. "
                    f"Original error: {exc}"
                )
            self.completed.emit(False, message)
        except Exception as exc:  # noqa: BLE001
            self.completed.emit(False, str(exc))
