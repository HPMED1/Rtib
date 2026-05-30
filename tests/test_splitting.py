"""Tests for the row splitter."""

from __future__ import annotations

from rtib.core.splitting import SeparatorKind, SplitResult, split_input


class TestNamedSeparators:
    def test_newline(self):
        text = "a\nb\nc"
        r = split_input(text, SeparatorKind.NEWLINE)
        assert r.rows == ["a", "b", "c"]
        assert r.chosen == SeparatorKind.NEWLINE

    def test_crlf_newline(self):
        text = "a\r\nb\r\nc"
        r = split_input(text, SeparatorKind.NEWLINE)
        assert r.rows == ["a", "b", "c"]

    def test_comma(self):
        text = "one, two, three"
        r = split_input(text, SeparatorKind.COMMA)
        assert r.rows == ["one", "two", "three"]
        assert r.chosen == SeparatorKind.COMMA

    def test_semicolon(self):
        text = "alpha;beta;gamma"
        r = split_input(text, SeparatorKind.SEMICOLON)
        assert r.rows == ["alpha", "beta", "gamma"]

    def test_tab(self):
        text = "x\ty\tz"
        r = split_input(text, SeparatorKind.TAB)
        assert r.rows == ["x", "y", "z"]

    def test_pipe(self):
        text = "foo|bar|baz"
        r = split_input(text, SeparatorKind.PIPE)
        assert r.rows == ["foo", "bar", "baz"]

    def test_blank_items_filtered(self):
        text = "a,,b,  ,c"
        r = split_input(text, SeparatorKind.COMMA)
        assert r.rows == ["a", "b", "c"]


class TestRegex:
    def test_split_by_two_or_more_spaces(self):
        text = "John Smith   Jane Doe   Bob Roberts"
        r = split_input(text, SeparatorKind.REGEX, custom_pattern=r"\s{2,}")
        assert r.rows == ["John Smith", "Jane Doe", "Bob Roberts"]

    def test_split_after_phone_number(self):
        text = "John Smith 555-1234 Jane Doe 555-5678 Bob 555-9999"
        # Lookbehind: split AFTER a 4-digit number, before any whitespace.
        r = split_input(text, SeparatorKind.REGEX, custom_pattern=r"(?<=\d{4})\s+")
        assert r.rows == ["John Smith 555-1234", "Jane Doe 555-5678", "Bob 555-9999"]

    def test_empty_pattern_returns_empty(self):
        r = split_input("hello", SeparatorKind.REGEX, custom_pattern="")
        assert r.rows == []

    def test_invalid_regex_returns_empty(self):
        # Unbalanced bracket.
        r = split_input("a,b", SeparatorKind.REGEX, custom_pattern="[")
        assert r.rows == []


class TestAuto:
    def test_picks_newline_for_line_per_row(self):
        text = "movie 1\nmovie 2\nmovie 3\nmovie 4"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.NEWLINE
        assert r.rows == ["movie 1", "movie 2", "movie 3", "movie 4"]

    def test_picks_comma_when_single_line(self):
        text = "The Matrix 1999, Inception 2010, Interstellar 2014"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.COMMA
        assert len(r.rows) == 3
        assert r.rows[0].startswith("The Matrix")

    def test_picks_semicolon_when_dominant(self):
        text = "alpha; beta; gamma; delta; epsilon"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.SEMICOLON
        assert len(r.rows) == 5

    def test_tsv_multiline_picks_newline(self):
        """When a TSV has multiple lines, each line is a record; we sort one
        record at a time so newline (not tab) is the row separator."""
        text = "name\tage\tcity\nAlice\t30\tNYC"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.NEWLINE
        assert r.rows == ["name\tage\tcity", "Alice\t30\tNYC"]

    def test_tsv_single_line_picks_tab(self):
        """Single line of tab-separated values — tab IS the row separator."""
        text = "Alice\t30\tNYC\tEng"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.TAB
        assert r.rows == ["Alice", "30", "NYC", "Eng"]

    def test_prefers_newline_when_both_present(self):
        """When the user has line-per-row data with commas INSIDE rows (e.g.
        'Romeo, Juliet, 1996' is a single row), Auto should prefer newline."""
        text = (
            "Romeo, Juliet, 1996\n"
            "Goodfellas, 1990, mkv\n"
            "Pulp Fiction, 1994, mp4\n"
            "Fight Club, 1999, mp4"
        )
        r = split_input(text, SeparatorKind.AUTO)
        assert r.chosen == SeparatorKind.NEWLINE
        assert len(r.rows) == 4

    def test_single_item_falls_back(self):
        text = "just one item with no separator"
        r = split_input(text, SeparatorKind.AUTO)
        assert r.rows == ["just one item with no separator"]

    def test_empty_input_returns_empty(self):
        r = split_input("", SeparatorKind.AUTO)
        assert r.rows == []

    def test_whitespace_only_returns_empty(self):
        r = split_input("   \n  \n  ", SeparatorKind.AUTO)
        assert r.rows == []


class TestResultShape:
    def test_returns_split_result(self):
        r = split_input("a\nb", SeparatorKind.NEWLINE)
        assert isinstance(r, SplitResult)
