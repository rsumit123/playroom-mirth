"""A poker table, as PlayRoom holds a game.

The engine underneath is the one from the card_games project and knows nothing
about rooms, sockets or databases. This is the thin layer between it and
PlayRoom: it keeps one hand at a time inside the room's state blob, decides who
may act and when their time is up, and hands each seat the view it is allowed
to see.

Two things are deliberately kept from the original server, because both fixed
real bugs there: every state carries a revision, and a submitted action carries
the revision it was decided on plus a key that makes a repeat harmless. A phone
on a train will send the same fold twice.
"""
from __future__ import annotations

import time
from typing import Any, Mapping

from app.services.holdem.engine import (
    InvalidAction,
    apply_action,
    legal_actions,
    public_projection,
    resolve_showdown,
    start_hand,
)
from app.services.holdem.evaluator import evaluate_hand
from app.services.holdem.state import HoldemState

# How long a seat has to act before it is folded for them, and how long the
# table lingers on a finished hand before the next one is dealt.
ACTION_SECONDS = 30.0
REVEAL_SECONDS = 6.0


def new_table(seat_ids: list[int], starting_chips: int, small_blind: int) -> dict[str, Any]:
    """Deal the first hand of a session."""
    stacks = {seat_id: starting_chips for seat_id in seat_ids}
    hand = start_hand(stacks, small_blind=small_blind, big_blind=small_blind * 2)
    return _blob(hand, revision=1, small_blind=small_blind)


def deal_next(blob: Mapping[str, Any]) -> dict[str, Any] | None:
    """The next hand, or None when only one seat still has chips."""
    hand = _hand(blob)
    stacks = {player.seat_id: player.stack for player in hand.players}
    if sum(1 for chips in stacks.values() if chips > 0) < 2:
        return None
    next_hand = start_hand(
        stacks,
        dealer_seat=hand.dealer_seat + 1,
        small_blind=blob["small_blind"],
        big_blind=blob["small_blind"] * 2,
        hand_number=hand.hand_number + 1,
    )
    return _blob(next_hand, revision=blob["revision"] + 1, small_blind=blob["small_blind"])


def projection_for(blob: Mapping[str, Any], seat_id: int | None, names: Mapping[int, str]) -> dict[str, Any]:
    """What one seat is allowed to see.

    Never broadcast this: the whole point is that it carries hole cards.
    """
    hand = _hand(blob)
    public = dict(public_projection(hand))
    public["names"] = {player.seat_id: names.get(player.seat_id) for player in hand.players}

    view: dict[str, Any] = {
        "public": public,
        "seat_id": seat_id,
        "hole_cards": [],
        "legal_actions": [],
        "hand_rank": None,
        "revision": blob["revision"],
        "deadline_ts": blob.get("deadline_ts"),
        "reveal_ts": blob.get("reveal_ts"),
    }
    if seat_id is None:
        return view
    try:
        player = hand.player(seat_id)
    except KeyError:
        return view

    view["hole_cards"] = [{"rank": card.rank, "suit": card.suit} for card in player.hole_cards]
    if hand.current_seat == seat_id:
        view["legal_actions"] = [dict(action) for action in legal_actions(hand, seat_id)]
    if len(hand.community_cards) + len(player.hole_cards) >= 5:
        rank = evaluate_hand(player.hole_cards + hand.community_cards)
        view["hand_rank"] = {"category": rank.category_name, "tiebreakers": list(rank.tiebreakers)}
    return view


def submit(
    blob: Mapping[str, Any],
    seat_id: int,
    action: Mapping[str, Any],
    *,
    expected_revision: int | None = None,
    idempotency_key: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Take one action. Returns the new blob and an ack, or the old one and an error."""
    blob = dict(blob)
    hand = _hand(blob)

    # The same action arriving twice is the same action, not two.
    if idempotency_key and blob.get("seen", {}).get(str(seat_id)) == idempotency_key:
        return blob, {"ok": True, "repeat": True, "revision": blob["revision"]}

    if hand.current_seat != seat_id:
        return blob, {"ok": False, "error": "NOT_YOUR_TURN"}
    # A client that decided on an older table is answering a question nobody
    # asked any more.
    if expected_revision is not None and expected_revision != blob["revision"]:
        return blob, {"ok": False, "error": "STALE", "revision": blob["revision"]}

    try:
        played = apply_action(hand, seat_id, dict(action))
    except (InvalidAction, KeyError, ValueError) as exc:
        return blob, {"ok": False, "error": "ILLEGAL_ACTION", "detail": str(exc)}

    if played.street == "complete" and not played.payouts:
        played = resolve_showdown(played)

    seen = dict(blob.get("seen", {}))
    if idempotency_key:
        seen[str(seat_id)] = idempotency_key
    updated = _blob(played, revision=blob["revision"] + 1, small_blind=blob["small_blind"], seen=seen)
    return updated, {"ok": True, "revision": updated["revision"]}


def fold_for_timeout(blob: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Whoever is holding the table up folds, or checks when that is free."""
    hand = _hand(blob)
    seat_id = hand.current_seat
    if seat_id is None:
        return dict(blob), {"ok": False, "error": "NOBODY_TO_ACT"}
    free = any(option["type"] == "check" for option in legal_actions(hand, seat_id))
    return submit(blob, seat_id, {"type": "check" if free else "fold"})


def is_complete(blob: Mapping[str, Any]) -> bool:
    return _hand(blob).street == "complete"


def stacks(blob: Mapping[str, Any]) -> dict[int, int]:
    return {player.seat_id: player.stack for player in _hand(blob).players}


def current_seat(blob: Mapping[str, Any]) -> int | None:
    return _hand(blob).current_seat


def _hand(blob: Mapping[str, Any]) -> HoldemState:
    return HoldemState.from_dict(blob["hand"])


def _blob(hand: HoldemState, *, revision: int, small_blind: int, seen: dict[str, str] | None = None) -> dict[str, Any]:
    complete = hand.street == "complete"
    now = time.time()
    return {
        "hand": hand.to_dict(),
        "revision": revision,
        "small_blind": small_blind,
        "seen": seen or {},
        # Only one clock runs at a time: somebody's turn, or the pause before
        # the next deal.
        "deadline_ts": None if complete or hand.current_seat is None else now + ACTION_SECONDS,
        "reveal_ts": now + REVEAL_SECONDS if complete else None,
    }
