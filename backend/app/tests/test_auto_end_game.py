import pytest

from app.services.game_state import RoomGameState, ROOM_STATES
from app.sockets.events import _auto_end_game


@pytest.mark.asyncio
async def test_auto_end_game_with_explicit_winner(monkeypatch):
    state = RoomGameState(
        room_id=1, room_code="AEG1", rounds_total=1,
        turn_seconds=60, difficulty=1, game_type="trivia",
    )
    state.scores = {10: 100, 20: 0}
    ROOM_STATES["AEG1"] = state

    emitted = []
    async def fake_emit(event, payload, *args, **kwargs):
        emitted.append((event, payload))

    from app.sockets import events as ev
    monkeypatch.setattr(ev.sio, "emit", fake_emit)

    await _auto_end_game(state, "AEG1", winner_player_id=10)

    # game:game_end should have been emitted with our explicit winner
    game_end = [p for e, p in emitted if e == "game:game_end"]
    assert game_end
    assert game_end[0]["winner_player_id"] == 10
