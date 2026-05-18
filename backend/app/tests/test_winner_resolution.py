from app.services.game_state import RoomGameState
from app.sockets.events import _resolve_winner


def _make_state(scores: dict):
    s = RoomGameState(room_id=1, room_code="X", rounds_total=1,
                      turn_seconds=60, difficulty=1)
    s.player_order = list(scores.keys())
    s.scores = dict(scores)
    return s


def test_resolve_winner_picks_highest_score():
    state = _make_state({1: 100, 2: 250, 3: 50})
    assert _resolve_winner(state) == 2


def test_resolve_winner_tie_returns_none():
    state = _make_state({1: 100, 2: 100})
    assert _resolve_winner(state) is None


def test_resolve_winner_empty_returns_none():
    state = _make_state({})
    assert _resolve_winner(state) is None
