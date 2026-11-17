"""Main application window with YouTube search and download functionality."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.src.components.buttons import BrowseButtonController, DownloadButtonController
from app.src.components.dialogs import SettingsDialog
from app.src.components.inputs import FileNameInput, OutputDirectoryInput, YouTubeUrlInput
from app.src.components.queue import BatchDownloadController
from app.src.components.search import SearchController, SearchResult
from app.src.components.widgets import QueueList, SearchResultsList
from app.src.settings import AppSettings, QueueItem
from app.src.utils.files import resolve_icon_path
from app.version import __version__


class SearchTab(QWidget):
    """Tab widget for YouTube search and queue management."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.search_controller = SearchController(settings.auth_config)
        self.batch_controller = BatchDownloadController(settings.auth_config)
        self._build_ui()
        self._load_saved_queue()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Search section
        search_group = QGroupBox("Search YouTube")
        search_layout = QVBoxLayout(search_group)

        # Search input row
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query (e.g., 'lofi hip hop beats')")
        self.search_input.returnPressed.connect(self._start_search)
        search_row.addWidget(self.search_input, stretch=1)

        self.search_button = QPushButton("Search")
        self.search_button.setFixedWidth(100)
        self.search_button.clicked.connect(self._start_search)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        search_row.addWidget(self.search_button)

        search_layout.addLayout(search_row)

        self.search_status = QLabel("Enter a search query to find YouTube videos")
        self.search_status.setStyleSheet("color: #aaa; font-size: 11px;")
        search_layout.addWidget(self.search_status)

        layout.addWidget(search_group)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Search results panel
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)

        results_header = QLabel("Search Results")
        results_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff;")
        results_layout.addWidget(results_header)

        self.results_list = SearchResultsList()
        self.results_list.selection_changed.connect(self._on_selection_changed)
        results_layout.addWidget(self.results_list)

        splitter.addWidget(results_panel)

        # Queue panel
        queue_panel = QWidget()
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(0, 0, 0, 0)

        queue_header_row = QHBoxLayout()
        self.queue_header = QLabel("Download Queue (0)")
        self.queue_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff;")
        queue_header_row.addWidget(self.queue_header)

        self.clear_queue_btn = QPushButton("Clear All")
        self.clear_queue_btn.setFixedWidth(80)
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        self.clear_queue_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        queue_header_row.addWidget(self.clear_queue_btn)
        queue_layout.addLayout(queue_header_row)

        self.queue_list = QueueList()
        self.queue_list.item_removed.connect(self._remove_from_queue)
        self.queue_list.item_format_changed.connect(self._update_queue_item)
        queue_layout.addWidget(self.queue_list)

        splitter.addWidget(queue_panel)

        # Set initial splitter sizes (60% results, 40% queue)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter, stretch=1)

        # Output directory row
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save To:"))

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(self.settings.output_directory)
        output_row.addWidget(self.output_dir_input, stretch=1)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._browse_output_dir)
        output_row.addWidget(self.browse_btn)

        layout.addLayout(output_row)

        # Download all button and progress
        download_row = QHBoxLayout()

        self.download_all_btn = QPushButton("⬇ Download All")
        self.download_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        self.download_all_btn.clicked.connect(self._start_batch_download)
        download_row.addWidget(self.download_all_btn)

        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setValue(0)
        self.batch_progress.setVisible(False)
        download_row.addWidget(self.batch_progress, stretch=1)

        self.batch_status = QLabel("")
        self.batch_status.setStyleSheet("color: #aaa;")
        download_row.addWidget(self.batch_status)

        layout.addLayout(download_row)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setPlaceholderText("Download logs will appear here...")
        layout.addWidget(self.log_output)

    def _load_saved_queue(self) -> None:
        """Load previously saved queue from settings."""
        for item in self.settings.download_queue:
            self.queue_list.add_item(item)
        self._update_queue_count()

    def _start_search(self) -> None:
        """Start a YouTube search."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Empty Query", "Please enter a search query.")
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        self.results_list.clear()
        self.search_status.setText("Searching...")

        # Update auth config in controller
        self.search_controller.auth_config = self.settings.auth_config

        self.search_controller.search(
            query=query,
            max_results=self.settings.search_results_limit,
            on_progress=self._on_search_progress,
            on_result=self._on_search_result,
            on_completed=self._on_search_completed,
        )

    def _on_search_progress(self, message: str) -> None:
        """Handle search progress update."""
        self.search_status.setText(message)

    def _on_search_result(self, result: SearchResult) -> None:
        """Handle a search result."""
        self.results_list.add_result(result)

        # Mark as selected if already in queue
        for item in self.settings.download_queue:
            if item.video_id == result.video_id:
                self.results_list.mark_as_added(result.video_id)
                break

    def _on_selection_changed(self, result: SearchResult, format_type: str, bitrate: str, is_selected: bool) -> None:
        """Handle checkbox selection change - add or remove from queue."""
        if is_selected:
            self._add_to_queue(result, format_type, bitrate)
        else:
            self.settings.remove_from_queue(result.video_id)
            self.queue_list.remove_item(result.video_id)
            self._update_queue_count()

    def _on_search_completed(self, success: bool, message: str) -> None:
        """Handle search completion."""
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

        if success:
            count = self.results_list.result_count()
            self.search_status.setText(f"Found {count} videos")
        else:
            self.search_status.setText(f"Search failed: {message}")
            if "authentication" in message.lower():
                QMessageBox.warning(
                    self,
                    "Authentication Required",
                    f"{message}\n\nGo to Settings (gear icon) to configure browser cookies.",
                )

    def _add_to_queue(self, result: SearchResult, format_type: str, bitrate: str) -> None:
        """Add a search result to the download queue."""
        item = QueueItem(
            url=result.url,
            video_id=result.video_id,
            title=result.title,
            channel=result.channel,
            duration=result.duration_string,
            thumbnail_url=result.thumbnail_url,
            target_format=format_type,
            mp3_bitrate=bitrate,
        )

        added = self.settings.add_to_queue(item)
        if added:
            self.queue_list.add_item(item)
            self._update_queue_count()
        else:
            # Item already in queue, make sure UI reflects it
            if not self.queue_list.item_count():
                self._update_queue_count()

    def _remove_from_queue(self, video_id: str) -> None:
        """Remove item from queue."""
        self.settings.remove_from_queue(video_id)
        self._update_queue_count()

    def _update_queue_item(self, video_id: str, format_type: str, bitrate: str) -> None:
        """Update queue item format settings."""
        self.settings.update_queue_item(
            video_id,
            target_format=format_type,
            mp3_bitrate=bitrate,
        )

    def _clear_queue(self) -> None:
        """Clear the entire queue."""
        if not self.settings.download_queue:
            return

        answer = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the entire download queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.settings.clear_queue()
            self.queue_list.clear()
            self._update_queue_count()

    def _update_queue_count(self) -> None:
        """Update queue header with count."""
        count = len(self.settings.download_queue)
        self.queue_header.setText(f"Download Queue ({count})")
        self.download_all_btn.setEnabled(count > 0)
        self.clear_queue_btn.setEnabled(count > 0)

    def _browse_output_dir(self) -> None:
        """Browse for output directory."""
        current = self.output_dir_input.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Folder", current)
        if chosen:
            self.output_dir_input.setText(chosen)
            self.settings.output_directory = chosen
            self.settings.save()

    def _start_batch_download(self) -> None:
        """Start downloading all items in queue."""
        if not self.settings.download_queue:
            QMessageBox.warning(self, "Empty Queue", "The download queue is empty.")
            return

        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "No Output Folder", "Please select an output folder.")
            return

        # Create output directory if needed
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Folder Error", f"Cannot create output folder:\n{e}")
            return

        # Save output directory
        self.settings.output_directory = output_dir
        self.settings.save()

        # Disable controls
        self._set_downloading_state(True)
        self.log_output.clear()
        self.batch_progress.setValue(0)
        self.batch_progress.setVisible(True)

        # Update auth config
        self.batch_controller.auth_config = self.settings.auth_config

        self.batch_controller.start_download(
            queue_items=self.settings.download_queue,
            output_dir=output_dir,
            on_item_started=self._on_item_started,
            on_item_progress=self._on_item_progress,
            on_item_status=self._on_item_status,
            on_item_completed=self._on_item_completed,
            on_log_message=self._on_log_message,
            on_all_completed=self._on_all_completed,
        )

    def _set_downloading_state(self, downloading: bool) -> None:
        """Set UI state during download."""
        self.download_all_btn.setEnabled(not downloading)
        self.clear_queue_btn.setEnabled(not downloading)
        self.browse_btn.setEnabled(not downloading)
        self.output_dir_input.setEnabled(not downloading)
        self.queue_list.set_all_enabled(not downloading)

        if downloading:
            self.download_all_btn.setText("Downloading...")
        else:
            self.download_all_btn.setText("⬇ Download All")

    def _on_item_started(self, video_id: str, current: int, total: int) -> None:
        """Handle item download start."""
        self.batch_status.setText(f"Downloading {current}/{total}")
        self.queue_list.set_item_downloading(video_id)

        # Update progress bar based on overall progress
        percent = int((current - 1) / total * 100)
        self.batch_progress.setValue(percent)

    def _on_item_progress(self, video_id: str, percent: int) -> None:
        """Handle item download progress."""
        self.queue_list.set_item_progress(video_id, percent)

    def _on_item_status(self, video_id: str, status: str) -> None:
        """Handle item status update."""
        self.queue_list.set_item_status(video_id, status)

    def _on_item_completed(self, video_id: str, success: bool, message: str) -> None:
        """Handle item download completion."""
        self.queue_list.mark_item_completed(video_id, success)

    def _on_log_message(self, message: str) -> None:
        """Handle log message."""
        self.log_output.append(message)

    def _on_all_completed(self, success_count: int, total: int) -> None:
        """Handle batch completion."""
        self._set_downloading_state(False)
        self.batch_progress.setValue(100)
        self.batch_status.setText(f"Complete: {success_count}/{total} succeeded")

        # Clear completed items from queue
        completed_ids = [
            item.video_id
            for item in self.settings.download_queue
        ]

        if success_count == total:
            self.settings.clear_queue()
            self.queue_list.clear()
            self._update_queue_count()
            QMessageBox.information(
                self,
                "Download Complete",
                f"Successfully downloaded all {total} videos!",
            )
        else:
            QMessageBox.warning(
                self,
                "Download Complete",
                f"Downloaded {success_count} of {total} videos.\n\n"
                f"Check the log for details on failed downloads.",
            )

    def is_busy(self) -> bool:
        """Check if any operations are running."""
        return self.search_controller.is_searching() or self.batch_controller.is_downloading()


class DirectUrlTab(QWidget):
    """Tab widget for direct URL download (original functionality)."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

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
        self.output_dir_input.setText(self.settings.output_directory)

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

        layout.addWidget(form_group)
        layout.addWidget(self.download_button_controller.button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_output)

        self._sync_mp3_bitrate_visibility()

    def _sync_mp3_bitrate_visibility(self, _index: int | None = None) -> None:
        is_mp3 = self.format_selector.currentData() == "mp3"
        self.mp3_bitrate_label.setVisible(is_mp3)
        self.mp3_bitrate_selector.setVisible(is_mp3)

    def is_busy(self) -> bool:
        """Check if download is running."""
        return self.download_button_controller._thread is not None and \
               self.download_button_controller._thread.isRunning()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings()

        self.setWindowTitle(f"YouTube to MP3 / MP4 Downloader v{__version__}")
        self.setMinimumSize(900, 700)
        icon_path = resolve_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with settings button
        header = QWidget()
        header.setStyleSheet("background-color: #2a2a2a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 8, 14, 8)

        title_label = QLabel(f"YouTube Downloader v{__version__}")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #fff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        settings_btn.clicked.connect(self._open_settings)
        header_layout.addWidget(settings_btn)

        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #2a2a2a;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #888;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid #444;
                border-bottom: none;
                font-size: 13px;
                font-weight: 500;
                min-width: 140px;
            }
            QTabBar::tab:selected {
                background-color: #2a2a2a;
                color: #ff0000;
                border: 1px solid #ff0000;
                border-bottom: none;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #454545;
                color: #fff;
                border-color: #555;
            }
            QTabBar::tab:selected:hover {
                border-color: #ff0000;
            }
        """)

        # Search & Queue tab
        self.search_tab = SearchTab(self.settings)
        self.tabs.addTab(self.search_tab, "🔍 Search & Queue")

        # Direct URL tab
        self.direct_tab = DirectUrlTab(self.settings)
        self.tabs.addTab(self.direct_tab, "📋 Direct URL")

        layout.addWidget(self.tabs)

        self.setCentralWidget(central_widget)

    def _open_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # Settings saved, update controllers with new auth config
            self.search_tab.search_controller.auth_config = self.settings.auth_config
            self.search_tab.batch_controller.auth_config = self.settings.auth_config

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle window close."""
        if self.search_tab.is_busy():
            QMessageBox.warning(
                self,
                "Operation Running",
                "Please wait for the current search or download to finish.",
            )
            event.ignore()
            return

        if self.direct_tab.is_busy():
            QMessageBox.warning(
                self,
                "Download Running",
                "Please wait for the active download to finish before closing.",
            )
            event.ignore()
            return

        # Save any pending settings
        self.settings.save()
        super().closeEvent(event)


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)

    # Set application-wide dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #2a2a2a;
            color: #fff;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #3a3a3a;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 6px;
            color: #fff;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #ff0000;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #aaa;
        }
        QProgressBar {
            background-color: #3a3a3a;
            border: none;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #ff0000;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #cc0000;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #888;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #444;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QScrollBar:vertical {
            background-color: #2a2a2a;
            width: 12px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background-color: #555;
            min-height: 30px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 1px solid #555;
        }
        QCheckBox::indicator:checked {
            background-color: #4CAF50;
            border-color: #4CAF50;
        }
    """)

    icon_path = resolve_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
