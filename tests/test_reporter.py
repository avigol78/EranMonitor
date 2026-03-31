from reporter import _gap


def test_gap_shortage():
    """supply=5, demand=6 → gap=-1 (shortage)."""
    row = {"calls": 4, "waiting": 2, "connected": 10, "on_break": 5}
    assert _gap(row) == -1


def test_gap_surplus():
    """supply=8, demand=3 → gap=+5 (surplus)."""
    row = {"calls": 2, "waiting": 1, "connected": 10, "on_break": 2}
    assert _gap(row) == 5


def test_gap_handles_none_values():
    """None fields default to 0."""
    row = {"calls": None, "waiting": None, "connected": 5, "on_break": 0}
    assert _gap(row) == 5
