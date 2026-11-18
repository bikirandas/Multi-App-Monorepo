"""Persistent settings and authentication management."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSettings


@dataclass
class AuthConfig:
    """Authentication configuration for video site access."""

    browser: str | None = None  # Browser to extract cookies from
    cookies_file: str | None = None  # Path to cookies.txt file
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "browser": self.browser,
            "cookies_file": self.cookies_file,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthConfig:
        return cls(
            browser=data.get("browser"),
            cookies_file=data.get("cookies_file"),
            enabled=data.get("enabled", False),
        )


@dataclass
class QueueItem:
    """A video in the download queue."""

    url: str
    video_id: str
    title: str
    channel: str
    duration: str
    thumbnail_url: str | None
    target_format: str = "mp3"  # mp3 or mp4
    mp3_bitrate: str = "320"
    custom_filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "target_format": self.target_format,
            "mp3_bitrate": self.mp3_bitrate,
            "custom_filename": self.custom_filename,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueItem:
        return cls(
            url=data["url"],
            video_id=data["video_id"],
            title=data["title"],
            channel=data["channel"],
            duration=data["duration"],
            thumbnail_url=data.get("thumbnail_url"),
            target_format=data.get("target_format", "mp3"),
            mp3_bitrate=data.get("mp3_bitrate", "320"),
            custom_filename=data.get("custom_filename"),
        )


@dataclass
class AppSettings:
    """Application settings with persistence."""

    output_directory: str = ""
    default_format: str = "mp3"
    default_mp3_bitrate: str = "320"
    auth_config: AuthConfig = field(default_factory=AuthConfig)
    download_queue: list[QueueItem] = field(default_factory=list)
    search_results_limit: int = 20

    _settings: QSettings | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._settings = QSettings("YTDownloader", "YTDownloader")
        self._load()

    def _load(self) -> None:
        """Load settings from persistent storage."""
        if not self._settings:
            return

        self.output_directory = self._settings.value(
            "output_directory", str(Path.home() / "Downloads"), str
        )
        self.default_format = self._settings.value("default_format", "mp3", str)
        self.default_mp3_bitrate = self._settings.value("default_mp3_bitrate", "320", str)
        self.search_results_limit = self._settings.value("search_results_limit", 20, int)

        # Load auth config
        auth_json = self._settings.value("auth_config", "{}", str)
        try:
            auth_data = json.loads(auth_json)
            self.auth_config = AuthConfig.from_dict(auth_data)
        except (json.JSONDecodeError, TypeError):
            self.auth_config = AuthConfig()

        # Load download queue
        queue_json = self._settings.value("download_queue", "[]", str)
        try:
            queue_data = json.loads(queue_json)
            self.download_queue = [QueueItem.from_dict(item) for item in queue_data]
        except (json.JSONDecodeError, TypeError):
            self.download_queue = []

    def save(self) -> None:
        """Save settings to persistent storage."""
        if not self._settings:
            return

        self._settings.setValue("output_directory", self.output_directory)
        self._settings.setValue("default_format", self.default_format)
        self._settings.setValue("default_mp3_bitrate", self.default_mp3_bitrate)
        self._settings.setValue("search_results_limit", self.search_results_limit)
        self._settings.setValue("auth_config", json.dumps(self.auth_config.to_dict()))
        self._settings.setValue(
            "download_queue",
            json.dumps([item.to_dict() for item in self.download_queue]),
        )
        self._settings.sync()

    def add_to_queue(self, item: QueueItem) -> bool:
        """Add item to queue if not already present. Returns True if added."""
        if any(q.video_id == item.video_id for q in self.download_queue):
            return False
        self.download_queue.append(item)
        self.save()
        return True

    def remove_from_queue(self, video_id: str) -> bool:
        """Remove item from queue by video_id. Returns True if removed."""
        for i, item in enumerate(self.download_queue):
            if item.video_id == video_id:
                del self.download_queue[i]
                self.save()
                return True
        return False

    def clear_queue(self) -> None:
        """Clear the entire download queue."""
        self.download_queue.clear()
        self.save()

    def update_queue_item(self, video_id: str, **kwargs: Any) -> bool:
        """Update a queue item's properties."""
        for item in self.download_queue:
            if item.video_id == video_id:
                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self.save()
                return True
        return False


def get_available_browsers() -> list[str]:
    """Get list of browsers that can be used for cookie extraction."""
    browsers = ["chrome", "firefox", "edge", "opera", "brave", "vivaldi", "safari"]
    available = []

    for browser in browsers:
        # Check if browser data directory exists
        if sys.platform == "win32":
            if browser == "chrome":
                path = Path.home() / "AppData/Local/Google/Chrome/User Data"
            elif browser == "firefox":
                path = Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles"
            elif browser == "edge":
                path = Path.home() / "AppData/Local/Microsoft/Edge/User Data"
            elif browser == "opera":
                path = Path.home() / "AppData/Roaming/Opera Software/Opera Stable"
            elif browser == "brave":
                path = Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data"
            elif browser == "vivaldi":
                path = Path.home() / "AppData/Local/Vivaldi/User Data"
            else:
                continue

            if path.exists():
                available.append(browser)
        elif sys.platform == "darwin":
            if browser == "chrome":
                path = Path.home() / "Library/Application Support/Google/Chrome"
            elif browser == "firefox":
                path = Path.home() / "Library/Application Support/Firefox/Profiles"
            elif browser == "safari":
                path = Path.home() / "Library/Cookies"
            elif browser == "edge":
                path = Path.home() / "Library/Application Support/Microsoft Edge"
            elif browser == "opera":
                path = Path.home() / "Library/Application Support/com.operasoftware.Opera"
            elif browser == "brave":
                path = Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser"
            elif browser == "vivaldi":
                path = Path.home() / "Library/Application Support/Vivaldi"
            else:
                continue

            if path.exists():
                available.append(browser)
        else:  # Linux
            if browser == "chrome":
                path = Path.home() / ".config/google-chrome"
            elif browser == "firefox":
                path = Path.home() / ".mozilla/firefox"
            elif browser == "edge":
                path = Path.home() / ".config/microsoft-edge"
            elif browser == "opera":
                path = Path.home() / ".config/opera"
            elif browser == "brave":
                path = Path.home() / ".config/BraveSoftware/Brave-Browser"
            elif browser == "vivaldi":
                path = Path.home() / ".config/vivaldi"
            else:
                continue

            if path.exists():
                available.append(browser)

    return available


def test_browser_cookies(browser: str) -> tuple[bool, str]:
    """Test if cookies can be extracted from the specified browser."""
    try:
        # Try a simple yt-dlp extraction with cookies from browser
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "yt_dlp",
                "--cookies-from-browser",
                browser,
                "--skip-download",
                "--no-warnings",
                "-j",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "Successfully extracted cookies"
        return False, result.stderr or "Failed to extract cookies"
    except subprocess.TimeoutExpired:
        return False, "Timeout while testing cookies"
    except Exception as e:
        return False, str(e)
