"""Modal asking 'what is this data?' before auto-suggesting headers."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class HintDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Describe your data")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("What is this data? (optional)")
        title.setObjectName("brand")
        layout.addWidget(title)

        help_text = QLabel(
            "One line is enough — e.g. \"movie filenames from torrent sites\" or "
            "\"lab order log lines\". Leave blank to let the model figure it out."
        )
        help_text.setObjectName("muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        self._input = QLineEdit()
        self._input.setPlaceholderText("e.g. movie filenames")
        self._input.returnPressed.connect(self.accept)
        layout.addWidget(self._input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continue")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)

    @property
    def hint(self) -> str:
        return self._input.text().strip()
