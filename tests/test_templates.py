"""Template save/load/list round-trips against an isolated tmp dir."""

from __future__ import annotations

import json

from rtib.core.schema import Header
from rtib.core.templates import (
    delete_template,
    list_templates,
    load_template,
    save_template,
    template_exists,
)


class TestRoundTrip:
    def test_save_then_load(self, temp_templates_dir):
        headers = [
            Header(name="Title", description="movie title"),
            Header(name="Year", description="release year"),
        ]
        saved = save_template("Movies", headers, hint="movie filenames")
        assert saved.name == "Movies"
        assert len(saved.headers) == 2

        loaded = load_template("Movies")
        assert loaded is not None
        assert loaded.name == "Movies"
        assert loaded.hint == "movie filenames"
        assert [h.name for h in loaded.headers] == ["Title", "Year"]
        assert [h.description for h in loaded.headers] == [
            "movie title",
            "release year",
        ]

    def test_save_without_hint(self, temp_templates_dir):
        save_template("Bare", [Header(name="X")], hint=None)
        loaded = load_template("Bare")
        assert loaded is not None
        assert loaded.hint is None

    def test_save_strips_empty_headers(self, temp_templates_dir):
        save_template(
            "Mixed",
            [Header(name="Real"), Header(name=""), Header(name="Other")],
        )
        loaded = load_template("Mixed")
        assert loaded is not None
        assert [h.name for h in loaded.headers] == ["Real", "Other"]


class TestList:
    def test_empty_dir(self, temp_templates_dir):
        assert list_templates() == []

    def test_lists_saved_templates(self, temp_templates_dir):
        save_template("A", [Header(name="X")])
        save_template("B", [Header(name="Y")])
        names = sorted(t.name for t in list_templates())
        assert names == ["A", "B"]

    def test_ignores_malformed_json(self, temp_templates_dir):
        (temp_templates_dir / "broken.json").write_text("{not json", encoding="utf-8")
        save_template("Good", [Header(name="X")])
        names = [t.name for t in list_templates()]
        assert names == ["Good"]

    def test_ignores_template_with_no_name_or_filename_fallback(
        self, temp_templates_dir
    ):
        # JSON with neither `name` nor usable headers is dropped.
        (temp_templates_dir / "empty.json").write_text(
            json.dumps({"headers": []}), encoding="utf-8"
        )
        # But the filename stem is used as fallback name if not set in JSON.
        results = list_templates()
        assert len(results) == 1
        assert results[0].name == "empty"


class TestExistsAndDelete:
    def test_exists(self, temp_templates_dir):
        assert not template_exists("Foo")
        save_template("Foo", [Header(name="X")])
        assert template_exists("Foo")

    def test_delete_existing(self, temp_templates_dir):
        save_template("Foo", [Header(name="X")])
        assert delete_template("Foo") is True
        assert not template_exists("Foo")
        assert load_template("Foo") is None

    def test_delete_missing(self, temp_templates_dir):
        assert delete_template("nothing here") is False


class TestSlugCollisions:
    def test_overwrite_via_same_slug(self, temp_templates_dir):
        """'Movies' and 'movies' collide on slug — second save overwrites."""
        save_template("Movies", [Header(name="A")])
        save_template("movies", [Header(name="B")])
        loaded = load_template("movies")
        assert loaded is not None
        assert loaded.headers[0].name == "B"
