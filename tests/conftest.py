"""Shared pytest fixtures.

QApplication is session-scoped because Qt only lets you have one per process.
Tests that touch ``templates_dir()`` get an isolated temp dir via monkeypatch
so they never pollute the user's real ``%APPDATA%/Rtib/`` location.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("RtibTest")
    app.setOrganizationName("RtibTest")
    yield app


@pytest.fixture
def temp_templates_dir(tmp_path, monkeypatch, qapp):
    from rtib.core import templates as templates_mod

    d = tmp_path / "templates"
    d.mkdir()
    monkeypatch.setattr(templates_mod, "templates_dir", lambda: d)
    return d
