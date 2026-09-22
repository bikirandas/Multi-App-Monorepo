from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.src.components.buttons import BrowseButtonController, DownloadButtonController
from app.src.components.inputs import FileNameInput, OutputDirectoryInput, YouTubeUrlInput
from app.src.utils.files import resolve_icon_path


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("YouTube to MP3 / MP4 Downloader")
        self.setMinimumSize(760, 520)
        icon_path = resolve_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        self.browse_button_controller: BrowseButtonController | None = None
        self.download_button_controller: DownloadButtonController | None = None

        self._build_ui()
        self._set_default_output_dir()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        form_group = QGroupBox("Download Options")
        form_layout = QGridLayout(form_group)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)

        self.url_input = YouTubeUrlInput()

        self.format_selector = QComboBox()
        self.format_selector.addItem("MP3 (Audio)", userData="mp3")
        self.format_selector.addItem("MP4 (Video)", userData="mp4")
        self.format_selector.currentIndexChanged.connect(self._sync_mp3_bitrate_visibility)

        self.file_name_input = FileNameInput()

        self.mp3_bitrate_label = QLabel("MP3 Bitrate")
        self.mp3_bitrate_selector = QComboBox()
        self.mp3_bitrate_selector.addItem("320 kbps (Best)", userData="320")
        self.mp3_bitrate_selector.addItem("256 kbps", userData="256")

        self.output_dir_input = OutputDirectoryInput()

        form_layout.addWidget(QLabel("YouTube URL"), 0, 0)
        form_layout.addWidget(self.url_input, 0, 1, 1, 2)

        form_layout.addWidget(QLabel("Format"), 1, 0)
        form_layout.addWidget(self.format_selector, 1, 1, 1, 2)

        form_layout.addWidget(QLabel("File Name"), 2, 0)
        form_layout.addWidget(self.file_name_input, 2, 1, 1, 2)

        form_layout.addWidget(self.mp3_bitrate_label, 3, 0)
        form_layout.addWidget(self.mp3_bitrate_selector, 3, 1, 1, 2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Download logs will appear here.")

        self.browse_button_controller = BrowseButtonController(
            self,
            output_dir_input=self.output_dir_input,
        )
        self.download_button_controller = DownloadButtonController(
            self,
            url_input=self.url_input,
            format_selector=self.format_selector,
            file_name_input=self.file_name_input,
            mp3_bitrate_selector=self.mp3_bitrate_selector,
            output_dir_input=self.output_dir_input,
            progress_bar=self.progress_bar,
            status_label=self.status_label,
            log_output=self.log_output,
            browse_button_controller=self.browse_button_controller,
        )

        form_layout.addWidget(QLabel("Save To"), 4, 0)
        form_layout.addWidget(self.output_dir_input, 4, 1)
        form_layout.addWidget(self.browse_button_controller.button, 4, 2)

        root_layout.addWidget(form_group)
        root_layout.addWidget(self.download_button_controller.button)
        root_layout.addWidget(self.progress_bar)
        root_layout.addWidget(self.status_label)
        root_layout.addWidget(self.log_output)

        self.setCentralWidget(central_widget)
        self._sync_mp3_bitrate_visibility()

    def _sync_mp3_bitrate_visibility(self, _index: int | None = None) -> None:
        is_mp3 = self.format_selector.currentData() == "mp3"
        self.mp3_bitrate_label.setVisible(is_mp3)
        self.mp3_bitrate_selector.setVisible(is_mp3)

    def _set_default_output_dir(self) -> None:
        downloads_dir = Path.home() / "Downloads"
        self.output_dir_input.setText(str(downloads_dir))

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.download_button_controller and not self.download_button_controller.can_close():
            event.ignore()
            return
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    icon_path = resolve_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
