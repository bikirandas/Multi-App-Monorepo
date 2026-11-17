"""Download queue management with batch download support."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.src.logging import DownloadLogger
from app.src.utils.files import resolve_ffmpeg_location

if TYPE_CHECKING:
    from app.src.settings import AuthConfig, QueueItem


class BatchDownloadWorker(QObject):
    """Worker to download multiple videos from queue."""

    started = pyqtSignal()
    item_started = pyqtSignal(str, int, int)  # video_id, current_index, total_count
    item_progress = pyqtSignal(str, int)  # video_id, percent
    item_status = pyqtSignal(str, str)  # video_id, status
    item_completed = pyqtSignal(str, bool, str)  # video_id, success, message
    log_message = pyqtSignal(str)
    all_completed = pyqtSignal(int, int)  # success_count, total_count

    def __init__(
        self,
        queue_items: list[QueueItem],
        output_dir: str,
        auth_config: AuthConfig | None = None,
    ) -> None:
        super().__init__()
        self.queue_items = list(queue_items)  # Copy the list
        self.output_dir = output_dir
        self.auth_config = auth_config
        self._cancelled = False
        self._current_video_id: str | None = None

    def cancel(self) -> None:
        """Cancel the batch download."""
        self._cancelled = True

    def _make_progress_hook(self, video_id: str):
        """Create a progress hook for a specific video."""

        def hook(data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                raw_percent = data.get("_percent_str", "")
                # Clean ANSI codes
                import re

                cleaned = re.sub(r"\x1b\[[0-9;]*m", "", raw_percent).strip()
                match = re.search(r"(\d+(?:\.\d+)?)%", cleaned)
                if match:
                    percent = max(0, min(100, int(float(match.group(1)))))
                    self.item_progress.emit(video_id, percent)

                speed = (data.get("_speed_str") or "").strip()
                eta = (data.get("_eta_str") or "").strip()
                if speed or eta:
                    details = " | ".join(
                        part
                        for part in [
                            f"Speed: {speed}" if speed else "",
                            f"ETA: {eta}" if eta else "",
                        ]
                        if part
                    )
                    self.item_status.emit(video_id, f"Downloading... {details}")
                else:
                    self.item_status.emit(video_id, "Downloading...")

            elif status == "finished":
                self.item_progress.emit(video_id, 100)
                self.item_status.emit(video_id, "Processing...")

        return hook

    @pyqtSlot()
    def run(self) -> None:
        """Execute the batch download."""
        self.started.emit()
        total = len(self.queue_items)
        success_count = 0

        for index, item in enumerate(self.queue_items):
            if self._cancelled:
                break

            self._current_video_id = item.video_id
            self.item_started.emit(item.video_id, index + 1, total)
            self.log_message.emit(f"\n[{index + 1}/{total}] Starting: {item.title}")

            # Build output template
            if item.custom_filename:
                output_template = f"{item.custom_filename}.%(ext)s"
            else:
                output_template = "%(title)s.%(ext)s"

            ydl_options = {
                "outtmpl": str(Path(self.output_dir) / output_template),
                "noplaylist": True,
                "progress_hooks": [self._make_progress_hook(item.video_id)],
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

            # Add authentication if configured
            if self.auth_config and self.auth_config.enabled:
                if self.auth_config.browser:
                    ydl_options["cookiesfrombrowser"] = (self.auth_config.browser,)
                elif self.auth_config.cookies_file:
                    ydl_options["cookiefile"] = self.auth_config.cookies_file

            # Add FFmpeg location
            ffmpeg_location = resolve_ffmpeg_location()
            if ffmpeg_location:
                ydl_options["ffmpeg_location"] = str(ffmpeg_location)

            # Configure format
            if item.target_format == "mp3":
                self.item_status.emit(
                    item.video_id,
                    f"Downloading audio for MP3 ({item.mp3_bitrate} kbps)...",
                )
                ydl_options.update(
                    {
                        "format": "bestaudio/best",
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": item.mp3_bitrate,
                            }
                        ],
                    }
                )
            else:
                self.item_status.emit(item.video_id, "Downloading video...")
                ydl_options.update(
                    {
                        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
                        "merge_output_format": "mp4",
                    }
                )

            try:
                with YoutubeDL(ydl_options) as ydl:
                    info = ydl.extract_info(item.url, download=True)
                    downloaded_path = Path(ydl.prepare_filename(info))
                    if item.target_format == "mp3":
                        downloaded_path = downloaded_path.with_suffix(".mp3")

                self.item_completed.emit(item.video_id, True, str(downloaded_path))
                self.log_message.emit(f"✓ Saved: {downloaded_path}")
                success_count += 1

            except DownloadError as exc:
                message = str(exc)
                if "ffmpeg" in message.lower() and item.target_format == "mp3":
                    message = "MP3 conversion needs FFmpeg installed."
                self.item_completed.emit(item.video_id, False, message)
                self.log_message.emit(f"✗ Failed: {message}")

            except Exception as exc:
                self.item_completed.emit(item.video_id, False, str(exc))
                self.log_message.emit(f"✗ Failed: {exc}")

        self._current_video_id = None
        self.all_completed.emit(success_count, total)


class BatchDownloadController:
    """Controller for managing batch downloads."""

    def __init__(self, auth_config: AuthConfig | None = None) -> None:
        self.auth_config = auth_config
        self._thread: QThread | None = None
        self._worker: BatchDownloadWorker | None = None

    def is_downloading(self) -> bool:
        """Check if a batch download is currently running."""
        return self._thread is not None and self._thread.isRunning()

    def cancel(self) -> None:
        """Cancel the current batch download."""
        if self._worker:
            self._worker.cancel()

    def start_download(
        self,
        queue_items: list[QueueItem],
        output_dir: str,
        on_started: callable = None,
        on_item_started: callable = None,
        on_item_progress: callable = None,
        on_item_status: callable = None,
        on_item_completed: callable = None,
        on_log_message: callable = None,
        on_all_completed: callable = None,
    ) -> None:
        """
        Start downloading all items in the queue.

        Args:
            queue_items: List of QueueItem to download
            output_dir: Directory to save files
            on_started: Called when batch starts
            on_item_started: Called when each item starts (video_id, current, total)
            on_item_progress: Called for progress updates (video_id, percent)
            on_item_status: Called for status updates (video_id, status)
            on_item_completed: Called when each item completes (video_id, success, message)
            on_log_message: Called for log messages
            on_all_completed: Called when all complete (success_count, total)
        """
        if self.is_downloading():
            return

        if not queue_items:
            if on_all_completed:
                on_all_completed(0, 0)
            return

        self._thread = QThread()
        self._worker = BatchDownloadWorker(queue_items, output_dir, self.auth_config)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)

        if on_started:
            self._worker.started.connect(on_started)
        if on_item_started:
            self._worker.item_started.connect(on_item_started)
        if on_item_progress:
            self._worker.item_progress.connect(on_item_progress)
        if on_item_status:
            self._worker.item_status.connect(on_item_status)
        if on_item_completed:
            self._worker.item_completed.connect(on_item_completed)
        if on_log_message:
            self._worker.log_message.connect(on_log_message)
        if on_all_completed:
            self._worker.all_completed.connect(on_all_completed)

        # Cleanup
        self._worker.all_completed.connect(self._thread.quit)
        self._worker.all_completed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup)

        self._thread.start()

    def _cleanup(self) -> None:
        """Clean up after batch completes."""
        self._thread = None
        self._worker = None
