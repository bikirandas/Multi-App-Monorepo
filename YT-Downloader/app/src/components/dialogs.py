"""Dialog windows for settings and authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.src.settings import get_available_browsers, test_browser_cookies

if TYPE_CHECKING:
    from app.src.settings import AppSettings


class SettingsDialog(QDialog):
    """Settings dialog for configuring app preferences and authentication."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()
        self._load_current_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Authentication section
        auth_group = QGroupBox("Authentication (Optional)")
        auth_layout = QVBoxLayout(auth_group)

        auth_description = QLabel(
            "Authentication helps avoid 'Sign in to confirm you're not a bot' errors "
            "and allows access to age-restricted content. Your login credentials are "
            "extracted from your browser's cookies and persist across app restarts."
        )
        auth_description.setWordWrap(True)
        auth_description.setStyleSheet("color: #aaa; font-size: 11px; margin-bottom: 8px;")
        auth_layout.addWidget(auth_description)

        self.auth_enabled = QCheckBox("Enable authentication")
        self.auth_enabled.stateChanged.connect(self._on_auth_toggle)
        auth_layout.addWidget(self.auth_enabled)

        # Browser selection
        browser_layout = QHBoxLayout()
        browser_layout.addWidget(QLabel("Extract cookies from:"))

        self.browser_selector = QComboBox()
        self.browser_selector.addItem("Select browser...", "")
        for browser in get_available_browsers():
            self.browser_selector.addItem(browser.capitalize(), browser)
        browser_layout.addWidget(self.browser_selector, stretch=1)

        self.test_browser_btn = QPushButton("Test")
        self.test_browser_btn.setFixedWidth(80)
        self.test_browser_btn.clicked.connect(self._test_browser_cookies)
        browser_layout.addWidget(self.test_browser_btn)

        auth_layout.addLayout(browser_layout)

        # Or cookies file
        or_label = QLabel("— OR —")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_label.setStyleSheet("color: #666; margin: 8px 0;")
        auth_layout.addWidget(or_label)

        cookies_layout = QHBoxLayout()
        cookies_layout.addWidget(QLabel("Cookies file:"))

        self.cookies_file_input = QLineEdit()
        self.cookies_file_input.setPlaceholderText("Path to cookies.txt file (Netscape format)")
        cookies_layout.addWidget(self.cookies_file_input, stretch=1)

        self.browse_cookies_btn = QPushButton("Browse")
        self.browse_cookies_btn.setFixedWidth(80)
        self.browse_cookies_btn.clicked.connect(self._browse_cookies_file)
        cookies_layout.addWidget(self.browse_cookies_btn)

        auth_layout.addLayout(cookies_layout)

        layout.addWidget(auth_group)

        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)

        self.results_limit = QSpinBox()
        self.results_limit.setRange(5, 50)
        self.results_limit.setValue(20)
        search_layout.addRow("Results per search:", self.results_limit)

        layout.addWidget(search_group)

        # Default format settings
        format_group = QGroupBox("Default Download Settings")
        format_layout = QFormLayout(format_group)

        self.default_format = QComboBox()
        self.default_format.addItem("MP3 (Audio)", "mp3")
        self.default_format.addItem("MP4 (Video)", "mp4")
        format_layout.addRow("Default format:", self.default_format)

        self.default_bitrate = QComboBox()
        self.default_bitrate.addItem("320 kbps (Best)", "320")
        self.default_bitrate.addItem("256 kbps", "256")
        format_layout.addRow("Default MP3 bitrate:", self.default_bitrate)

        layout.addWidget(format_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _load_current_settings(self) -> None:
        """Load current settings into UI."""
        auth = self.settings.auth_config
        self.auth_enabled.setChecked(auth.enabled)

        if auth.browser:
            idx = self.browser_selector.findData(auth.browser)
            if idx >= 0:
                self.browser_selector.setCurrentIndex(idx)

        if auth.cookies_file:
            self.cookies_file_input.setText(auth.cookies_file)

        self.results_limit.setValue(self.settings.search_results_limit)

        format_idx = self.default_format.findData(self.settings.default_format)
        if format_idx >= 0:
            self.default_format.setCurrentIndex(format_idx)

        bitrate_idx = self.default_bitrate.findData(self.settings.default_mp3_bitrate)
        if bitrate_idx >= 0:
            self.default_bitrate.setCurrentIndex(bitrate_idx)

        self._on_auth_toggle()

    def _on_auth_toggle(self) -> None:
        """Handle auth enabled toggle."""
        enabled = self.auth_enabled.isChecked()
        self.browser_selector.setEnabled(enabled)
        self.test_browser_btn.setEnabled(enabled)
        self.cookies_file_input.setEnabled(enabled)
        self.browse_cookies_btn.setEnabled(enabled)

    def _test_browser_cookies(self) -> None:
        """Test if cookies can be extracted from selected browser."""
        browser = self.browser_selector.currentData()
        if not browser:
            QMessageBox.warning(self, "No Browser", "Please select a browser first.")
            return

        self.test_browser_btn.setEnabled(False)
        self.test_browser_btn.setText("Testing...")

        try:
            success, message = test_browser_cookies(browser)
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully extracted cookies from {browser.capitalize()}!\n\n"
                    "Your login session will be used for searches and downloads.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Failed",
                    f"Could not extract cookies from {browser.capitalize()}.\n\n"
                    f"Make sure you're logged into the video site in this browser.\n\n"
                    f"Error: {message}",
                )
        finally:
            self.test_browser_btn.setEnabled(True)
            self.test_browser_btn.setText("Test")

    def _browse_cookies_file(self) -> None:
        """Browse for cookies.txt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            "",
            "Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            self.cookies_file_input.setText(file_path)

    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        # Update auth config
        self.settings.auth_config.enabled = self.auth_enabled.isChecked()
        self.settings.auth_config.browser = self.browser_selector.currentData() or None
        self.settings.auth_config.cookies_file = self.cookies_file_input.text().strip() or None

        # Clear browser if cookies file is set (cookies file takes precedence)
        if self.settings.auth_config.cookies_file:
            self.settings.auth_config.browser = None

        # Update other settings
        self.settings.search_results_limit = self.results_limit.value()
        self.settings.default_format = self.default_format.currentData()
        self.settings.default_mp3_bitrate = self.default_bitrate.currentData()

        self.settings.save()
        self.accept()
