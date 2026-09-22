from __future__ import annotations

from PyQt6.QtWidgets import QLineEdit


class YouTubeUrlInput(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText("Paste YouTube URL here...")
        self.previous_url: str | None = None


class FileNameInput(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText("Optional custom file name (without extension)")


class OutputDirectoryInput(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText("Choose output folder...")
