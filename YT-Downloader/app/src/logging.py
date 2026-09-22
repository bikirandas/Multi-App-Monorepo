class DownloadLogger:
    """Bridge yt-dlp log messages into Qt signals."""

    def __init__(self, emit_message):
        self._emit_message = emit_message

    def debug(self, message: str) -> None:
        if message.startswith("[download]"):
            return
        self._emit_message(message)

    def warning(self, message: str) -> None:
        self._emit_message(f"Warning: {message}")

    def error(self, message: str) -> None:
        self._emit_message(f"Error: {message}")