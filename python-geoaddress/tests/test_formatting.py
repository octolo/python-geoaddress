"""Tests for address display layouts."""

from geoaddress.formatting import format_address_lines, format_address_text, resolve_display

SAMPLE = {
    "address_line1": "123 Rue de la République",
    "address_line2": "Bâtiment A",
    "address_line3": "",
    "postal_code": "75001",
    "city": "Paris",
    "county": "Paris",
    "state": "Île-de-France",
    "country": "France",
    "country_code": "FR",
}


def test_resolve_display_aliases() -> None:
    assert resolve_display("3lines") == resolve_display("text_3lines")
    assert resolve_display("full") == resolve_display("text_full")


def test_text_full_is_one_line() -> None:
    lines = format_address_lines(SAMPLE, "text_full")
    assert len(lines) == 1
    assert lines[0] == "123 Rue de la République, Bâtiment A, Paris, 75001, Île-de-France, France"


def test_text_3lines_is_three_concatenated_lines() -> None:
    lines = format_address_lines(SAMPLE, "text_3lines")
    assert lines == [
        "123 Rue de la République, Bâtiment A",
        "75001, Paris, Paris, Île-de-France",
        "France, FR",
    ]


def test_text_2lines_is_two_concatenated_lines() -> None:
    lines = format_address_lines(SAMPLE, "text_2lines")
    assert lines == [
        "123 Rue de la République, Bâtiment A",
        "75001, Paris, Paris, Île-de-France",
    ]


def test_text_aligned_one_line_per_top_level_item() -> None:
    lines = format_address_lines(SAMPLE, "text_aligned")
    assert "123 Rue de la République" in lines
    assert "Bâtiment A" in lines
    assert "75001, Paris" in lines
    assert "France, FR" in lines


def test_empty_values_are_skipped() -> None:
    assert format_address_lines({}, "text_3lines") == []
    assert format_address_text({"city": "Paris"}, "text_full") == "Paris"


def test_custom_layout() -> None:
    lines = format_address_lines(SAMPLE, [["address_line1"], ["city", "country"]])
    assert lines == ["123 Rue de la République", "Paris, France"]
