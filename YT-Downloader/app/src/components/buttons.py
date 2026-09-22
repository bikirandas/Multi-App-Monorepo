from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QWidget,
)

from app.src.components.inputs import FileNameInput, OutputDirectoryInput, YouTubeUrlInput
from app.src.components.workers import DownloadWorker


class BrowseButtonController:
    def __init__(self, parent: QWidget, *, output_dir_input: OutputDirectoryInput) -> None:
        self.parent = parent
        self.output_dir_input = output_dir_input
        self.button = QPushButton("Browse", parent)
        self.button.clicked.connect(self._select_output_dir)

    def _select_output_dir(self) -> None:
        chosen_dir = QFileDialog.getExistingDirectory(
            self.parent,
            "Select Output Folder",
            self.output_dir_input.text().strip() or str(Path.home()),
        )
        if chosen_dir:
            self.output_dir_input.setText(chosen_dir)


class DownloadButtonController:
    def __init__(
        self,
        parent: QWidget,
        *,
        url_input: YouTubeUrlInput,
        format_selector: QComboBox,
        file_name_input: FileNameInput,
        mp3_bitrate_selector: QComboBox,
        output_dir_input: OutputDirectoryInput,
        progress_bar: QProgressBar,
        status_label: QLabel,
        log_output: QTextEdit,
        browse_button_controller: BrowseButtonController,
    ) -> None:
        self.parent = parent
        self.url_input = url_input
        self.format_selector = format_selector
        self.file_name_input = file_name_input
        self.mp3_bitrate_selector = mp3_bitrate_selector
        self.output_dir_input = output_dir_input
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.log_output = log_output
        self.browse_button_controller = browse_button_controller

        self._thread: QThread | None = None
        self._worker: DownloadWorker | None = None

        self.button = QPushButton("Download", parent)
        self.button.clicked.connect(self._start_download)

    @staticmethod
    def _is_youtube_url(url: str) -> bool:
        pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
        return re.match(pattern, url, flags=re.IGNORECASE) is not None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.url_input.setEnabled(enabled)
        self.format_selector.setEnabled(enabled)
        self.file_name_input.setEnabled(enabled)
        self.mp3_bitrate_selector.setEnabled(enabled)
        self.output_dir_input.setEnabled(enabled)
        self.browse_button_controller.button.setEnabled(enabled)
        self.button.setEnabled(enabled)

    def _append_log(self, message: str) -> None:
        clean_message = message.strip()
        if not clean_message:
            return
        self.log_output.append(clean_message)

    def _start_download(self) -> None:
        url = self.url_input.text().strip()
        output_dir = self.output_dir_input.text().strip()
        target_format = self.format_selector.currentData()
        file_name = self.file_name_input.text().strip()
        mp3_bitrate = self.mp3_bitrate_selector.currentData() or "320"

        if not url:
            QMessageBox.warning(self.parent, "Validation Error", "Please provide a YouTube URL.")
            return
        if url == self.url_input.previous_url:
            answer = QMessageBox.question(
                self.parent,
                "Already Downloaded",
                "This URL was downloaded previously. Do you want to download it again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.No:
                self.url_input.clear()
                return
        if not output_dir:
            QMessageBox.warning(self.parent, "Validation Error", "Please select an output folder.")
            return
        if not self._is_youtube_url(url):
            QMessageBox.warning(self.parent, "Validation Error", "Please provide a valid YouTube URL.")
            return

        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self.parent, "Folder Error", f"Cannot use output folder:\n{exc}")
            return

        self.log_output.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing...")
        self._set_controls_enabled(False)

        self._thread = QThread(self.parent)
        self._worker = DownloadWorker(
            url=url,
            output_dir=str(output_path),
            target_format=target_format,
            custom_file_name=file_name or None,
            mp3_bitrate=str(mp3_bitrate),
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self.progress_bar.setValue)
        self._worker.status_changed.connect(self.status_label.setText)
        self._worker.log_message.connect(self._append_log)
        self._worker.completed.connect(self._on_download_completed)

        self._worker.completed.connect(self._thread.quit)
        self._worker.completed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_download_completed(self, success: bool, message: str) -> None:
        self._set_controls_enabled(True)
        self._worker = None
        self._thread = None

        if success:
            self.status_label.setText("Completed")
            self.progress_bar.setValue(100)
            self.log_output.append(f"Saved to: {message}")
            QMessageBox.information(self.parent, "Success", f"Download completed.\n\n{message}")
            self.url_input.previous_url = self.url_input.text().strip()
            self.url_input.setText("")
            self.file_name_input.setText("")
        else:
            self.status_label.setText("Failed")
            self.log_output.append(f"Failed: {message}")
            QMessageBox.critical(self.parent, "Download Failed", message)

    def can_close(self) -> bool:
        if self._thread and self._thread.isRunning():
            QMessageBox.warning(
                self.parent,
                "Download Running",
                "Please wait for the active download to finish before closing.",
            )
            return False
        return True
