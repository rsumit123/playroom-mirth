from app.services.game_state import RoomGameState, serialize_state, deserialize_state


def test_room_game_state_origin_default_friends():
    s = RoomGameState(room_id=1, room_code="ABC", rounds_total=1,
                      turn_seconds=60, difficulty=1)
    assert s.origin == "friends"


def test_room_game_state_origin_round_trip():
    s = RoomGameState(room_id=1, room_code="ABC", rounds_total=1,
                      turn_seconds=60, difficulty=1, origin="quickmatch")
    raw = serialize_state(s)
    restored = deserialize_state(raw)
    assert restored.origin == "quickmatch"


def test_deserialize_old_state_missing_origin_defaults_to_friends():
    """A state row persisted before this column existed should restore safely."""
    import json
    # Build a minimal payload missing the 'origin' key.
    payload = {
        "room_id": 1, "room_code": "OLD", "rounds_total": 1,
        "turn_seconds": 60, "difficulty": 1,
        "game_type": "trivia", "status": "active",
        "round_index": 1, "describer_index": 0, "turn_start_ts": 0.0,
        "player_order": [], "scores": {},
        "current_word_id": None, "current_word_text": None,
        "word_history_ids": [], "guessed_players": [],
        "trivia_questions": [], "current_question_index": 0,
        "player_answers": {}, "question_start_ts": 0.0,
        "question_time_seconds": 0, "trivia_category": "math",
        "used_question_ids": [],
    }
    restored = deserialize_state(json.dumps(payload))
    assert restored.origin == "friends"
