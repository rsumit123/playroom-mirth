import inspect
from app.sockets.events import _scribble_guess_score, chat_message


def test_scribble_lightning_fast():
    assert _scribble_guess_score(0) == 15
    assert _scribble_guess_score(2.5) == 15
    assert _scribble_guess_score(4.9) == 15


def test_scribble_fast():
    assert _scribble_guess_score(5) == 12
    assert _scribble_guess_score(7) == 12
    assert _scribble_guess_score(9.9) == 12


def test_scribble_normal():
    assert _scribble_guess_score(10) == 10
    assert _scribble_guess_score(15) == 10
    assert _scribble_guess_score(19.9) == 10


def test_scribble_slow():
    assert _scribble_guess_score(20) == 7
    assert _scribble_guess_score(25) == 7
    assert _scribble_guess_score(29.9) == 7


def test_scribble_very_slow():
    assert _scribble_guess_score(30) == 5
    assert _scribble_guess_score(60) == 5
    assert _scribble_guess_score(120) == 5


def test_scribble_boundary_values():
    """Exact tier boundaries land in the correct (lower) tier."""
    assert _scribble_guess_score(5) == 12   # 5s boundary -> tier 2
    assert _scribble_guess_score(10) == 10  # 10s boundary -> tier 3
    assert _scribble_guess_score(20) == 7   # 20s boundary -> tier 4
    assert _scribble_guess_score(30) == 5   # 30s boundary -> tier 5


def test_scribble_negative_elapsed():
    """Edge case: negative elapsed (clock skew) should give max points."""
    assert _scribble_guess_score(-1) == 15


def test_charades_guesser_flat_10():
    """Charades guesser scoring is flat 10 points — verified via source."""
    src = inspect.getsource(chat_message)
    assert "state.scores.get(player_id, 0) + 10" in src


def test_charades_describer_flat_5():
    """Charades describer scoring is flat 5 points — verified via source."""
    src = inspect.getsource(chat_message)
    assert "state.scores.get(describer_id, 0) + 5" in src
