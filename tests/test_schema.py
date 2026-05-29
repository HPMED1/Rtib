"""Schema construction and slugify behaviour."""

from __future__ import annotations

from rtib.core.schema import (
    Header,
    header_suggestion_schema,
    row_schema,
    slugify,
)


class TestSlugify:
    def test_simple(self):
        assert slugify("Title") == "title"

    def test_spaces_become_underscores(self):
        assert slugify("Release Year") == "release_year"

    def test_hyphens_become_underscores(self):
        assert slugify("release-year") == "release_year"

    def test_mixed_separators_collapse(self):
        assert slugify("  Release   Year  ") == "release_year"

    def test_strips_special_chars(self):
        assert slugify("Codec/Format!") == "codecformat"

    def test_unicode_is_stripped(self):
        # Arabic gets stripped because slugify is ASCII-only by design.
        assert slugify("عنوان") == "field"

    def test_empty_returns_field(self):
        assert slugify("") == "field"
        assert slugify("   ") == "field"
        assert slugify("!!!") == "field"

    def test_collapses_repeated_separators(self):
        assert slugify("name___here") == "name_here"

    def test_leading_trailing_underscores_stripped(self):
        assert slugify("_title_") == "title"


class TestHeaderKey:
    def test_key_matches_slug(self):
        h = Header(name="Release Year")
        assert h.key == "release_year"

    def test_description_does_not_affect_key(self):
        h = Header(name="Title", description="the movie title")
        assert h.key == "title"


class TestRowSchema:
    def test_basic_structure(self):
        headers = [Header(name="Title"), Header(name="Year")]
        schema = row_schema(headers)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == {"title", "year"}
        assert set(schema["properties"].keys()) == {"title", "year"}

    def test_every_field_is_nullable(self):
        """If the model can't determine a field, it must return null."""
        schema = row_schema([Header(name="Foo"), Header(name="Bar")])
        for prop in schema["properties"].values():
            assert prop["type"] == ["string", "null"]

    def test_descriptions_passed_through(self):
        h = Header(name="Year", description="release year")
        schema = row_schema([h])
        assert schema["properties"]["year"]["description"] == "release year"

    def test_no_description_means_no_description_key(self):
        schema = row_schema([Header(name="Title")])
        assert "description" not in schema["properties"]["title"]

    def test_empty_headers_returns_valid_empty_schema(self):
        schema = row_schema([])
        assert schema["properties"] == {}
        assert schema["required"] == []


class TestHeaderSuggestionSchema:
    def test_structure(self):
        schema = header_suggestion_schema()
        assert schema["type"] == "object"
        assert "headers" in schema["properties"]
        headers_prop = schema["properties"]["headers"]
        assert headers_prop["type"] == "array"
        assert headers_prop["minItems"] == 1

    def test_item_shape(self):
        schema = header_suggestion_schema()
        item = schema["properties"]["headers"]["items"]
        assert item["type"] == "object"
        assert set(item["required"]) == {"name", "description"}
