from scraper import _extract_int, _FIELD_PATTERNS


def test_calls_extracted_from_bishia_label():
    """Page uses 'בשיחה' not 'שיחות' — must match correctly."""
    text = "שלוחה: none | בשיחה: 4 | בהמתנה: 2 | פנויים/ות: 0 | בהפסקה: 5 | מחוברים/ות: 10"
    assert _extract_int(text, _FIELD_PATTERNS["calls"]) == 4


def test_waiting_extracted():
    text = "בהמתנה: 2"
    assert _extract_int(text, _FIELD_PATTERNS["waiting"]) == 2


def test_connected_extracted_with_gender_suffix():
    """Page label is 'מחוברים/ות' — the slash must not break the pattern."""
    text = "מחוברים/ות: 10"
    assert _extract_int(text, _FIELD_PATTERNS["connected"]) == 10


def test_on_break_extracted():
    text = "בהפסקה: 5"
    assert _extract_int(text, _FIELD_PATTERNS["on_break"]) == 5


def test_returns_none_when_no_match():
    assert _extract_int("no relevant text here", _FIELD_PATTERNS["calls"]) is None
