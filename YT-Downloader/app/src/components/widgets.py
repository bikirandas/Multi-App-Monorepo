"""Custom widgets for search results and download queue display."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from app.src.components.search import SearchResult
    from app.src.settings import QueueItem


class ThumbnailLabel(QLabel):
    """Label that loads and displays a thumbnail from URL."""

    def __init__(self, width: int = 120, height: int = 68, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #2a2a2a; border-radius: 4px;")
        self.setText("Loading...")
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_thumbnail_loaded)

    def load_thumbnail(self, url: str | None) -> None:
        """Load thumbnail from URL."""
        if not url:
            self.setText("No Image")
            return

        request = QNetworkRequest(QUrl(url))
        self._network_manager.get(request)

    def _on_thumbnail_loaded(self, reply: QNetworkReply) -> None:
        """Handle thumbnail download completion."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                scaled = pixmap.scaled(
                    self.width(),
                    self.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setPixmap(scaled)
            else:
                self.setText("Error")
        else:
            self.setText("Error")
        reply.deleteLater()


class SearchResultCard(QFrame):
    """Card widget displaying a single search result."""

    # video_id is emitted when selection state changes
    selection_changed = pyqtSignal(str, bool)  # video_id, is_selected

    def __init__(self, result: SearchResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result = result
        self.is_added = False
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            SearchResultCard {
                background-color: #3a3a3a;
                border-radius: 6px;
                padding: 8px;
            }
            SearchResultCard:hover {
                background-color: #454545;
            }
            SearchResultCard[selected="true"] {
                background-color: #4a4a4a;
                border: 2px solid #4CAF50;
            }
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Selection checkbox
        self.select_checkbox = QCheckBox()
        self.select_checkbox.setFixedSize(24, 24)
        self.select_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background-color: #3a3a3a;
                border: 2px solid #666;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            }
        """)
        self.select_checkbox.stateChanged.connect(self._on_selection_changed)
        layout.addWidget(self.select_checkbox)

        # Thumbnail
        self.thumbnail = ThumbnailLabel()
        self.thumbnail.load_thumbnail(self.result.thumbnail_url)
        layout.addWidget(self.thumbnail)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Title
        title_label = QLabel(self.result.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #fff;")
        title_label.setMaximumWidth(400)
        info_layout.addWidget(title_label)

        # Channel and metadata
        meta_text = f"{self.result.channel}"
        if self.result.view_count:
            meta_text += f" • {self.result.format_view_count()}"
        meta_text += f" • {self.result.duration_string}"

        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #aaa; font-size: 11px;")
        info_layout.addWidget(meta_label)

        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)

        # Format selector
        format_layout = QVBoxLayout()
        format_layout.setSpacing(4)

        self.format_selector = QComboBox()
        self.format_selector.addItem("MP3", "mp3")
        self.format_selector.addItem("MP4", "mp4")
        self.format_selector.setFixedWidth(80)
        self.format_selector.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_selector)

        self.bitrate_selector = QComboBox()
        self.bitrate_selector.addItem("320 kbps", "320")
        self.bitrate_selector.addItem("256 kbps", "256")
        self.bitrate_selector.setFixedWidth(80)
        format_layout.addWidget(self.bitrate_selector)

        layout.addLayout(format_layout)

        # Selected indicator (shown when selected)
        self.selected_label = QLabel("✓ Selected")
        self.selected_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 11px;")
        self.selected_label.setFixedWidth(80)
        self.selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_label.setVisible(False)
        layout.addWidget(self.selected_label)

    def _on_format_changed(self, _index: int) -> None:
        """Toggle bitrate selector visibility based on format."""
        is_mp3 = self.format_selector.currentData() == "mp3"
        self.bitrate_selector.setVisible(is_mp3)

    def _on_selection_changed(self, state: int) -> None:
        """Handle checkbox state change."""
        is_checked = state == Qt.CheckState.Checked.value
        self.is_selected = is_checked
        self.setProperty("selected", is_checked)
        self.style().polish(self)
        self.selected_label.setVisible(is_checked)

        if is_checked:
            self.select_checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    background-color: #4CAF50;
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 2px solid #4CAF50;
                    image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-ok-16.png);
                }
            """)
        else:
            self.select_checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    background-color: #3a3a3a;
                    border: 2px solid #666;
                    border-radius: 4px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 2px solid #4CAF50;
                    image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-ok-16.png);
                }
            """)

        # Emit selection changed signal so parent can queue/un-queue
        self.selection_changed.emit(self.result.video_id, is_checked)

    def select(self) -> None:
        """Programmatically select this card."""
        self.select_checkbox.setChecked(True)

    def deselect(self) -> None:
        """Programmatically deselect this card."""
        self.select_checkbox.setChecked(False)

    def is_selected(self) -> bool:
        """Return whether this card is selected."""
        return getattr(self, 'is_selected', False)

    def mark_added(self) -> None:
        """Mark this card as already added to queue."""
        self.is_added = True
        self.is_selected = True
        self.select_checkbox.setChecked(True)
        self.select_checkbox.setEnabled(False)
        self.setProperty("selected", True)
        self.style().polish(self)
        self.selected_label.setVisible(True)
        self.format_selector.setEnabled(False)
        self.bitrate_selector.setEnabled(False)
        # Apply selected checkbox style with tick
        self.select_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 4px;
            }
        """)


class SearchResultsList(QScrollArea):
    """Scrollable list of search results."""

    # Emitted when selection changes: (result, format_type, bitrate, is_selected)
    selection_changed = pyqtSignal(object, str, str, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background-color: #2a2a2a; }")

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(8)
        self._layout.addStretch()

        self.setWidget(self._container)
        self._cards: dict[str, SearchResultCard] = {}

    def clear(self) -> None:
        """Clear all results."""
        for card in self._cards.values():
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def add_result(self, result: SearchResult) -> None:
        """Add a search result to the list."""
        if result.video_id in self._cards:
            return

        card = SearchResultCard(result)
        card.selection_changed.connect(self._on_selection_changed)
        self._cards[result.video_id] = card

        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, card)

    def _on_selection_changed(self, video_id: str, is_selected: bool) -> None:
        """Forward selection change to parent."""
        card = self._cards.get(video_id)
        if not card:
            return

        result = card.result
        format_type = card.format_selector.currentData()
        bitrate = card.bitrate_selector.currentData() if format_type == "mp3" else "320"
        self.selection_changed.emit(result, format_type, bitrate, is_selected)

    def mark_as_added(self, video_id: str) -> None:
        """Mark a specific result as added/selected in queue."""
        if video_id in self._cards:
            self._cards[video_id].mark_added()

    def mark_all_added(self) -> None:
        """Mark all cards as added."""
        for card in self._cards.values():
            card.mark_added()

    def result_count(self) -> int:
        """Return the number of results."""
        return len(self._cards)

    def set_all_selected(self, selected: bool) -> None:
        """Select or deselect all results."""
        for card in self._cards.values():
            if selected:
                card.select()
            else:
                card.deselect()

    def get_selected_items(self) -> list:
        """Return list of cards that are selected."""
        return [card for card in self._cards.values() if card.is_selected()]


class QueueItemCard(QFrame):
    """Card widget displaying a single queue item."""

    remove_clicked = pyqtSignal(str)  # video_id
    format_changed = pyqtSignal(str, str, str)  # video_id, format, bitrate

    def __init__(self, item: QueueItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QueueItemCard {
                background-color: #3a3a3a;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Thumbnail
        self.thumbnail = ThumbnailLabel(width=100, height=56)
        self.thumbnail.load_thumbnail(self.item.thumbnail_url)
        layout.addWidget(self.thumbnail)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_label = QLabel(self.item.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #fff;")
        title_label.setMaximumWidth(350)
        info_layout.addWidget(title_label)

        meta_label = QLabel(f"{self.item.channel} • {self.item.duration}")
        meta_label.setStyleSheet("color: #aaa; font-size: 10px;")
        info_layout.addWidget(meta_label)

        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)

        # Status label (for download progress)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        self.status_label.setFixedWidth(100)
        layout.addWidget(self.status_label)

        # Format selector
        format_layout = QVBoxLayout()
        format_layout.setSpacing(2)

        self.format_selector = QComboBox()
        self.format_selector.addItem("MP3", "mp3")
        self.format_selector.addItem("MP4", "mp4")
        self.format_selector.setFixedWidth(70)
        # Set current format
        idx = 0 if self.item.target_format == "mp3" else 1
        self.format_selector.setCurrentIndex(idx)
        self.format_selector.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_selector)

        self.bitrate_selector = QComboBox()
        self.bitrate_selector.addItem("320", "320")
        self.bitrate_selector.addItem("256", "256")
        self.bitrate_selector.setFixedWidth(70)
        # Set current bitrate
        bitrate_idx = 0 if self.item.mp3_bitrate == "320" else 1
        self.bitrate_selector.setCurrentIndex(bitrate_idx)
        self.bitrate_selector.setVisible(self.item.target_format == "mp3")
        self.bitrate_selector.currentIndexChanged.connect(self._on_bitrate_changed)
        format_layout.addWidget(self.bitrate_selector)

        layout.addLayout(format_layout)

        # Remove button
        self.remove_button = QPushButton("✕")
        self.remove_button.setFixedSize(30, 30)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.remove_button.clicked.connect(lambda: self.remove_clicked.emit(self.item.video_id))
        layout.addWidget(self.remove_button)

    def _on_format_changed(self, _index: int) -> None:
        """Handle format change."""
        format_type = self.format_selector.currentData()
        is_mp3 = format_type == "mp3"
        self.bitrate_selector.setVisible(is_mp3)
        bitrate = self.bitrate_selector.currentData() if is_mp3 else "320"
        self.format_changed.emit(self.item.video_id, format_type, bitrate)

    def _on_bitrate_changed(self, _index: int) -> None:
        """Handle bitrate change."""
        format_type = self.format_selector.currentData()
        bitrate = self.bitrate_selector.currentData()
        self.format_changed.emit(self.item.video_id, format_type, bitrate)

    def set_progress(self, percent: int) -> None:
        """Update download progress."""
        self.status_label.setText(f"⬇ {percent}%")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 11px;")

    def set_status(self, status: str) -> None:
        """Update status text."""
        self.status_label.setText(status[:15] + "..." if len(status) > 15 else status)

    def mark_completed(self, success: bool) -> None:
        """Mark download as completed."""
        if success:
            self.status_label.setText("✓ Done")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        else:
            self.status_label.setText("✗ Failed")
            self.status_label.setStyleSheet("color: #f44336; font-size: 11px; font-weight: bold;")
        self.format_selector.setEnabled(False)
        self.bitrate_selector.setEnabled(False)
        self.remove_button.setEnabled(False)

    def set_downloading(self) -> None:
        """Mark as currently downloading."""
        self.status_label.setText("Starting...")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 11px;")
        self.format_selector.setEnabled(False)
        self.bitrate_selector.setEnabled(False)
        self.remove_button.setEnabled(False)


class QueueList(QScrollArea):
    """Scrollable list of queue items."""

    item_removed = pyqtSignal(str)  # video_id
    item_format_changed = pyqtSignal(str, str, str)  # video_id, format, bitrate

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background-color: #2a2a2a; }")

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        self.setWidget(self._container)
        self._cards: dict[str, QueueItemCard] = {}

    def clear(self) -> None:
        """Clear all items."""
        for card in self._cards.values():
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def add_item(self, item: QueueItem) -> None:
        """Add a queue item to the list."""
        if item.video_id in self._cards:
            return

        card = QueueItemCard(item)
        card.remove_clicked.connect(self._on_remove)
        card.format_changed.connect(self.item_format_changed.emit)
        self._cards[item.video_id] = card

        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, card)

    def remove_item(self, video_id: str) -> None:
        """Remove an item from the list."""
        if video_id in self._cards:
            card = self._cards.pop(video_id)
            self._layout.removeWidget(card)
            card.deleteLater()

    def _on_remove(self, video_id: str) -> None:
        """Handle remove button click."""
        self.remove_item(video_id)
        self.item_removed.emit(video_id)

    def set_item_progress(self, video_id: str, percent: int) -> None:
        """Update progress for a specific item."""
        if video_id in self._cards:
            self._cards[video_id].set_progress(percent)

    def set_item_status(self, video_id: str, status: str) -> None:
        """Update status for a specific item."""
        if video_id in self._cards:
            self._cards[video_id].set_status(status)

    def set_item_downloading(self, video_id: str) -> None:
        """Mark item as currently downloading."""
        if video_id in self._cards:
            self._cards[video_id].set_downloading()

    def mark_item_completed(self, video_id: str, success: bool) -> None:
        """Mark item as completed."""
        if video_id in self._cards:
            self._cards[video_id].mark_completed(success)

    def item_count(self) -> int:
        """Return the number of items in queue."""
        return len(self._cards)

    def set_all_enabled(self, enabled: bool) -> None:
        """Enable or disable all card controls."""
        for card in self._cards.values():
            card.format_selector.setEnabled(enabled)
            card.bitrate_selector.setEnabled(enabled)
            card.remove_button.setEnabled(enabled)
