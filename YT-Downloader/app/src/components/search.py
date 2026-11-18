"""Video search functionality using yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from yt_dlp import YoutubeDL

if TYPE_CHECKING:
    from app.src.settings import AuthConfig


@dataclass
class SearchResult:
    """A single video search result."""

    video_id: str
    url: str
    title: str
    channel: str
    duration: int  # seconds
    duration_string: str
    view_count: int
    thumbnail_url: str | None
    upload_date: str | None

    @classmethod
    def from_yt_dlp(cls, entry: dict) -> SearchResult:
        """Create SearchResult from yt-dlp entry."""
        video_id = entry.get("id", "")
        duration = entry.get("duration") or 0

        # Format duration - use duration_string if available, otherwise calculate
        duration_str = entry.get("duration_string")
        if not duration_str and duration:
            hours, remainder = divmod(int(duration), 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        elif not duration_str:
            duration_str = "N/A"

        # Get best thumbnail
        thumbnails = entry.get("thumbnails", [])
        thumbnail_url = None
        if thumbnails:
            # Prefer medium quality thumbnail (around 360px wide)
            for thumb in thumbnails:
                url = thumb.get("url", "")
                if "mqdefault" in url or thumb.get("id") == "mqdefault":
                    thumbnail_url = url
                    break
                # Also check for hq720 which is common in search results
                if "hq720" in url and thumb.get("width", 0) <= 400:
                    thumbnail_url = url
                    break
            # Fallback to first available thumbnail
            if not thumbnail_url and thumbnails:
                thumbnail_url = thumbnails[0].get("url")

        # Build URL - prefer webpage_url, fallback to url field, then construct from id
        url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"

        return cls(
            video_id=video_id,
            url=url,
            title=entry.get("title", "Unknown Title"),
            channel=entry.get("channel") or entry.get("uploader", "Unknown Channel"),
            duration=int(duration) if duration else 0,
            duration_string=duration_str,
            view_count=entry.get("view_count") or 0,
            thumbnail_url=thumbnail_url,
            upload_date=entry.get("upload_date"),
        )

    def format_view_count(self) -> str:
        """Format view count for display."""
        if self.view_count >= 1_000_000_000:
            return f"{self.view_count / 1_000_000_000:.1f}B views"
        elif self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M views"
        elif self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K views"
        elif self.view_count > 0:
            return f"{self.view_count} views"
        return ""


class SearchWorker(QObject):
    """Worker to perform video search in background thread."""

    started = pyqtSignal()
    progress = pyqtSignal(str)  # Status message
    result_found = pyqtSignal(object)  # SearchResult
    completed = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        query: str,
        max_results: int = 20,
        auth_config: AuthConfig | None = None,
    ) -> None:
        super().__init__()
        self.query = query
        self.max_results = max_results
        self.auth_config = auth_config
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the search."""
        self._cancelled = True

    @pyqtSlot()
    def run(self) -> None:
        """Execute the search."""
        self.started.emit()
        self.progress.emit(f"Searching for: {self.query}")

        # Note: Don't use extractor_args for search - it can interfere with the search extractor
        # Use extract_flat: 'in_playlist' to get metadata without downloading
        ydl_options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",  # Get metadata without full extraction
            "skip_download": True,
            "ignoreerrors": True,
        }

        # Add authentication if configured
        if self.auth_config and self.auth_config.enabled:
            if self.auth_config.browser:
                ydl_options["cookiesfrombrowser"] = (self.auth_config.browser,)
            elif self.auth_config.cookies_file:
                ydl_options["cookiefile"] = self.auth_config.cookies_file

        try:
            search_url = f"ytsearch{self.max_results}:{self.query}"

            with YoutubeDL(ydl_options) as ydl:
                self.progress.emit("Fetching search results...")
                info = ydl.extract_info(search_url, download=False)

                if self._cancelled:
                    self.completed.emit(False, "Search cancelled")
                    return

                if not info:
                    self.completed.emit(False, "No results found")
                    return

                entries = info.get("entries", [])
                if not entries:
                    self.completed.emit(False, "No results found")
                    return

                found_count = 0
                for entry in entries:
                    if self._cancelled:
                        break
                    if entry is None:
                        continue

                    try:
                        result = SearchResult.from_yt_dlp(entry)
                        self.result_found.emit(result)
                        found_count += 1
                        self.progress.emit(f"Found {found_count} results...")
                    except Exception:
                        continue

                if self._cancelled:
                    self.completed.emit(False, "Search cancelled")
                else:
                    self.completed.emit(True, f"Found {found_count} results")

        except Exception as e:
            error_msg = str(e)
            if "Sign in" in error_msg or "login" in error_msg.lower():
                self.completed.emit(
                    False,
                    "Authentication required. Please configure browser cookies in Settings.",
                )
            else:
                self.completed.emit(False, f"Search failed: {error_msg}")


class SearchController:
    """Controller for managing search operations."""

    def __init__(self, auth_config: AuthConfig | None = None) -> None:
        self.auth_config = auth_config
        self._thread: QThread | None = None
        self._worker: SearchWorker | None = None

    def is_searching(self) -> bool:
        """Check if a search is currently running."""
        return self._thread is not None and self._thread.isRunning()

    def cancel_search(self) -> None:
        """Cancel the current search if running."""
        if self._worker:
            self._worker.cancel()

    def search(
        self,
        query: str,
        max_results: int = 20,
        on_started: callable = None,
        on_progress: callable = None,
        on_result: callable = None,
        on_completed: callable = None,
    ) -> None:
        """
        Start a video search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            on_started: Callback when search starts
            on_progress: Callback for progress updates (str)
            on_result: Callback for each result (SearchResult)
            on_completed: Callback when search completes (success: bool, message: str)
        """
        if self.is_searching():
            self.cancel_search()
            # Wait for thread to finish
            if self._thread:
                self._thread.quit()
                self._thread.wait(1000)

        self._thread = QThread()
        self._worker = SearchWorker(query, max_results, self.auth_config)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)

        if on_started:
            self._worker.started.connect(on_started)
        if on_progress:
            self._worker.progress.connect(on_progress)
        if on_result:
            self._worker.result_found.connect(on_result)
        if on_completed:
            self._worker.completed.connect(on_completed)

        # Cleanup
        self._worker.completed.connect(self._thread.quit)
        self._worker.completed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup)

        self._thread.start()

    def _cleanup(self) -> None:
        """Clean up after search completes."""
        self._thread = None
        self._worker = None
