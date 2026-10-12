"""
E2E tests for charades and scribble game modes.
Plays full games via Socket.IO against the running local server and
verifies game flow, scoring, and scoreboard persistence.
"""
import os
import time
import pytest
import requests
import socketio

API = os.getenv("LIVE_API_BASE", "http://localhost:8005")

pytestmark = pytest.mark.live


def _drain(sio, timeout=0.3):
    events = []
    while True:
        try:
            events.append(sio.receive(timeout=timeout))
        except socketio.exceptions.TimeoutError:
            break
    return events


def _recv_until(sio, target_event, timeout=10):
    """Receive events until we get target_event or timeout."""
    deadline = time.time() + timeout
    collected = []
    while time.time() < deadline:
        try:
            ev_name, ev_data = sio.receive(timeout=2)
            collected.append((ev_name, ev_data))
            if ev_name == target_event:
                return ev_data, collected
        except socketio.exceptions.TimeoutError:
            continue
    return None, collected


def _setup_room(game_type, p1_name, p2_name, turn_seconds=30):
    """Create 2 guests, a room, join, connect sockets, register."""
    r = requests.post(f"{API}/guest", json={"display_name": p1_name})
    gt1 = r.json()["guest_token"]
    r = requests.post(f"{API}/guest", json={"display_name": p2_name})
    gt2 = r.json()["guest_token"]

    r = requests.post(f"{API}/rooms/guest", json={
        "guest_token": gt1, "game_type": game_type,
        "rounds_total": 1, "difficulty": 1, "turn_seconds": turn_seconds,
    })
    assert r.status_code == 201, f"Room creation failed: {r.text}"
    code = r.json()["room"]["code"]

    r = requests.post(f"{API}/rooms/join", json={"room_code": code, "guest_token": gt2})
    assert r.status_code == 200

    sio1 = socketio.SimpleClient()
    sio2 = socketio.SimpleClient()
    sio1.connect(API, socketio_path="/socket.io", transports=["polling"])
    sio2.connect(API, socketio_path="/socket.io", transports=["polling"])
    sio1.emit("room:register", {"room_code": code, "guest_token": gt1})
    sio2.emit("room:register", {"room_code": code, "guest_token": gt2})
    time.sleep(1)
    _drain(sio1)
    _drain(sio2)

    return code, gt1, gt2, sio1, sio2


def test_charades_full_game():
    """Play a 1-round charades game: both players describe, guesses happen, scoreboard saved."""
    code, gt1, gt2, sio1, sio2 = _setup_room("charades", "CharAlice", "CharBob", turn_seconds=30)
    print(f"\n[charades] Room: {code}")

    # Start game (host = sio1)
    sio1.emit("game:start", {"room_code": code, "guest_token": gt1})
    time.sleep(2)

    game_ended = False
    deadline = time.time() + 120
    current_word = None
    turns_played = 0

    # We need both sockets — describer gets game:new_word, guesser guesses via chat
    while time.time() < deadline and not game_ended:
        # Check both sockets for events
        for label, sio, other_sio in [("sio1", sio1, sio2), ("sio2", sio2, sio1)]:
            try:
                ev_name, ev_data = sio.receive(timeout=1)
            except socketio.exceptions.TimeoutError:
                continue

            if ev_name == "game:new_word":
                current_word = ev_data.get("word")
                print(f"  [{label}] got word: {current_word}")
                # The OTHER player should guess it
                time.sleep(0.5)
                other_sio.emit("chat:message", {"room_code": code, "message": current_word})
                print(f"  [other] guessing: {current_word}")

            elif ev_name == "game:turn_start":
                turns_played += 1
                print(f"  [{label}] turn_start: describer={ev_data.get('describer_id')}, round={ev_data.get('round_index')}")

            elif ev_name == "game:correct_guess":
                print(f"  [{label}] correct_guess! scores={ev_data.get('scores')}")

            elif ev_name == "game:round_end":
                print(f"  [{label}] round_end — triggering next round")
                sio1.emit("game:next_round", {"room_code": code})

            elif ev_name == "game:game_end":
                print(f"  [{label}] GAME ENDED! scores={ev_data}")
                game_ended = True
                break

            elif ev_name == "game:hint":
                print(f"  [{label}] hint: {ev_data.get('hint')}")

            else:
                print(f"  [{label}] [{ev_name}]")

    sio1.disconnect()
    sio2.disconnect()

    assert game_ended, "Charades game never ended!"
    assert turns_played >= 2, f"Expected at least 2 turns (both players describe), got {turns_played}"
    time.sleep(1)

    # Verify scoreboard
    r = requests.get(f"{API}/rooms/{code}/scoreboard")
    assert r.status_code == 200
    data = r.json()
    print(f"  Scoreboard: {data}")

    assert len(data["games"]) >= 1, f"No games in scoreboard: {data}"
    assert len(data["totals"]) == 2, f"Expected 2 players: {data['totals']}"
    names = {t["display_name"] for t in data["totals"]}
    assert "CharAlice" in names, f"CharAlice missing from {names}"
    assert "CharBob" in names, f"CharBob missing from {names}"

    # At least one player should have scored (guesser gets 10, describer gets 5)
    total_score = sum(t["total_score"] for t in data["totals"])
    assert total_score > 0, f"Total score should be > 0, got {total_score}"
    print("  CHARADES PASS!")


def test_scribble_full_game():
    """Play a 1-round scribble game: both players draw, guesses happen, scoreboard saved."""
    code, gt1, gt2, sio1, sio2 = _setup_room("scribble", "ScribAlice", "ScribBob", turn_seconds=15)
    print(f"\n[scribble] Room: {code}")

    # Start game
    sio1.emit("game:start", {"room_code": code, "guest_token": gt1})
    time.sleep(2)

    game_ended = False
    deadline = time.time() + 120
    current_word = None
    turns_played = 0
    word_holder = None  # which sio has the word

    while time.time() < deadline and not game_ended:
        for label, sio, other_sio in [("sio1", sio1, sio2), ("sio2", sio2, sio1)]:
            try:
                ev_name, ev_data = sio.receive(timeout=1)
            except socketio.exceptions.TimeoutError:
                continue

            if ev_name == "game:word_choices":
                words = ev_data.get("words") or []
                assert words, f"Expected scribble word choices, got {ev_data}"
                picked = words[0]
                print(f"  [{label}] picking word: {picked}")
                sio.emit("game:word_pick", {"room_code": code, "word": picked})

            elif ev_name == "game:new_word":
                current_word = ev_data.get("word")
                word_holder = label
                print(f"  [{label}] drawing word: {current_word}")
                # In scribble, the OTHER player guesses
                time.sleep(0.5)
                other_sio.emit("chat:message", {"room_code": code, "message": current_word})
                print(f"  [other] guessing: {current_word}")

            elif ev_name == "game:turn_start":
                turns_played += 1
                print(f"  [{label}] turn_start: describer={ev_data.get('describer_id')}, round={ev_data.get('round_index')}")

            elif ev_name == "game:correct_guess":
                print(f"  [{label}] correct_guess! scores={ev_data.get('scores')}, points={ev_data.get('points_awarded')}")

            elif ev_name == "game:round_end":
                print(f"  [{label}] round_end — triggering next round")
                sio1.emit("game:next_round", {"room_code": code})

            elif ev_name == "game:game_end":
                print(f"  [{label}] GAME ENDED! scores={ev_data}")
                game_ended = True
                break

            else:
                pass  # scribble:draw, chat:message, etc.

    sio1.disconnect()
    sio2.disconnect()

    assert game_ended, "Scribble game never ended!"
    assert turns_played >= 2, f"Expected at least 2 turns, got {turns_played}"
    time.sleep(1)

    # Verify scoreboard
    r = requests.get(f"{API}/rooms/{code}/scoreboard")
    assert r.status_code == 200
    data = r.json()
    print(f"  Scoreboard: {data}")

    assert len(data["games"]) >= 1, f"No games in scoreboard: {data}"
    assert len(data["totals"]) == 2, f"Expected 2 players: {data['totals']}"
    names = {t["display_name"] for t in data["totals"]}
    assert "ScribAlice" in names
    assert "ScribBob" in names

    total_score = sum(t["total_score"] for t in data["totals"])
    assert total_score > 0, f"Total score should be > 0, got {total_score}"
    print("  SCRIBBLE PASS!")
