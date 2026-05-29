"""Light and dark QSS for the app.

Kept intentionally minimal — colors only. Layout/spacing stays in widget code
so themes don't accidentally reshape the UI.
"""

from __future__ import annotations

from enum import Enum


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"


_LIGHT_QSS = """
* {
    font-family: "Segoe UI", "SF Pro Text", "Inter", sans-serif;
    font-size: 10pt;
}
QMainWindow, QDialog, QWidget {
    background-color: #fafafa;
    color: #1c1c1e;
}
QLabel#brand {
    font-size: 18pt;
    font-weight: 600;
    color: #1c1c1e;
}
QLabel#muted {
    color: #6b7280;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #f3f4f6;
}
QPushButton:pressed {
    background-color: #e5e7eb;
}
QPushButton#primary {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
}
QPushButton#primary:hover {
    background-color: #1d4ed8;
}
QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 8px;
}
QStatusBar {
    background-color: #f3f4f6;
    color: #4b5563;
}
QLabel#statusDotOk { color: #16a34a; }
QLabel#statusDotBad { color: #dc2626; }
"""

_DARK_QSS = """
* {
    font-family: "Segoe UI", "SF Pro Text", "Inter", sans-serif;
    font-size: 10pt;
}
QMainWindow, QDialog, QWidget {
    background-color: #1a1b1e;
    color: #e5e7eb;
}
QLabel#brand {
    font-size: 18pt;
    font-weight: 600;
    color: #f3f4f6;
}
QLabel#muted {
    color: #9ca3af;
}
QPushButton {
    background-color: #2a2b2f;
    border: 1px solid #3a3b3f;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e5e7eb;
}
QPushButton:hover {
    background-color: #34353a;
}
QPushButton:pressed {
    background-color: #404146;
}
QPushButton#primary {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
}
QPushButton#primary:hover {
    background-color: #2563eb;
}
QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2a2b2f;
    border: 1px solid #3a3b3f;
    border-radius: 6px;
    padding: 4px 8px;
    color: #e5e7eb;
}
QStatusBar {
    background-color: #232428;
    color: #9ca3af;
}
QLabel#statusDotOk { color: #22c55e; }
QLabel#statusDotBad { color: #ef4444; }
"""


def stylesheet_for(theme: Theme) -> str:
    return _DARK_QSS if theme == Theme.DARK else _LIGHT_QSS
