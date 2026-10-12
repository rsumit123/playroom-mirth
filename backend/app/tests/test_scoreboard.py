"""
Test that game history is saved and the scoreboard endpoint works.
Plays a full trivia game via Socket.IO against the running local server.
"""
import os
import time
import pytest
import requests
import socketio

API = os.getenv("LIVE_API_BASE", "http://localhost:8005")

pytestmark = pytest.mark.live


def test_trivia_game_saves_history_and_scoreboard():
    """Play a full 1-round trivia game and verify scoreboard."""

    # Create guests
    r = requests.post(f"{API}/guest", json={"display_name": "ScoreAlice"})
    gt1 = r.json()["guest_token"]
    r = requests.post(f"{API}/guest", json={"display_name": "ScoreBob"})
    gt2 = r.json()["guest_token"]

    # Create room (1 round trivia)
    r = requests.post(f"{API}/rooms/guest", json={
        "guest_token": gt1, "game_type": "trivia",
        "rounds_total": 1, "difficulty": 1, "turn_seconds": 60,
    })
    assert r.status_code == 201, f"Room creation failed: {r.text}"
    code = r.json()["room"]["code"]
    print(f"\nRoom: {code}")

    # Join
    r = requests.post(f"{API}/rooms/join", json={"room_code": code, "guest_token": gt2})
    assert r.status_code == 200

    # Scoreboard empty before game
    r = requests.get(f"{API}/rooms/{code}/scoreboard")
    assert r.json()["games"] == []

    # Connect sockets
    sio1 = socketio.SimpleClient()
    sio2 = socketio.SimpleClient()
    sio1.connect(API, socketio_path="/socket.io", transports=["polling"])
    sio2.connect(API, socketio_path="/socket.io", transports=["polling"])
    sio1.emit("room:register", {"room_code": code, "guest_token": gt1})
    sio2.emit("room:register", {"room_code": code, "guest_token": gt2})
    time.sleep(1)
    _drain(sio1)
    _drain(sio2)

    # Start game
    sio1.emit("game:start", {"room_code": code, "guest_token": gt1})
    time.sleep(2)

    # Play until game ends — simple event-driven loop
    game_ended = False
    deadline = time.time() + 120  # 2 min max

    while time.time() < deadline and not game_ended:
        try:
            ev_name, ev_data = sio1.receive(timeout=8)
        except socketio.exceptions.TimeoutError:
            print("  timeout waiting for event")
            continue

        if ev_name == "trivia:question":
            q_idx = ev_data.get("question_index", "?")
            print(f"  Q{q_idx}: answering...")
            sio1.emit("trivia:answer", {"room_code": code, "answer_index": 0})
            sio2.emit("trivia:answer", {"room_code": code, "answer_index": 0})

        elif ev_name == "game:game_end":
            print(f"  GAME ENDED! scores={ev_data}")
            game_ended = True

        elif ev_name == "game:round_end":
            print(f"  Round ended, triggering next round")
            sio1.emit("game:next_round", {"room_code": code})

        elif ev_name == "trivia:question_result":
            print(f"  Question result received, waiting for next...")

        else:
            print(f"  [{ev_name}]")

    sio1.disconnect()
    sio2.disconnect()

    assert game_ended, "Game never ended!"
    time.sleep(1)  # let DB flush

    # Check scoreboard
    r = requests.get(f"{API}/rooms/{code}/scoreboard")
    assert r.status_code == 200
    data = r.json()
    print(f"Scoreboard: {data}")

    assert len(data["games"]) >= 1, f"Expected games, got: {data['games']}"
    assert len(data["totals"]) == 2, f"Expected 2 players, got: {data['totals']}"
    names = {t["display_name"] for t in data["totals"]}
    assert "ScoreAlice" in names
    assert "ScoreBob" in names
    print("PASS!")


def _drain(sio, timeout=0.3):
    events = []
    while True:
        try:
            events.append(sio.receive(timeout=timeout))
        except socketio.exceptions.TimeoutError:
            break
    return events
