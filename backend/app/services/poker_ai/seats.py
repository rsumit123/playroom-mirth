"""House players: a language model in a seat.

The seat is an ordinary bot user, so display names, room joins, history and the
leaderboard all keep working without knowing a model is behind it. What the
model is told, and how much of the table it is allowed to remember between
hands, is the tier's business - see policy.py.

Every decision costs a fraction of a cent at OpenRouter, which makes this the
first thing in PlayRoom with a running cost. Guests get the cheapest seat;
signed-in players can sit any of them.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from app.services import poker
from app.services.poker_ai.adapter import AIAdapter
from app.services.poker_ai.policy import policy_for_tier
from app.services.poker_ai.reads import summarize, update_from_hand

_logger = logging.getLogger(__name__)

TIERS = ("Easy", "Medium", "Hard")
GUEST_TIER = "Easy"


def tiers_for(signed_in: bool) -> tuple[str, ...]:
    """Which seats this player may sit a model in.

    A guest is anonymous and costs us the same money as anybody else, so they
    get the cheap model. Somebody who signed in can pick the table they want.
    """
    return TIERS if signed_in else (GUEST_TIER,)


def is_allowed(tier: str, signed_in: bool) -> bool:
    return tier in tiers_for(signed_in)


def provider():
    """The thing that actually talks to a model, or None if we have no key."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    from app.services.poker_ai.openrouter import OpenRouterProvider

    return OpenRouterProvider(key)


async def decide(blob: Mapping[str, Any], seat_id: int, tier: str, reads: Mapping[int, Any], names: Mapping[int, str]):
    """What the model in this seat does. Falls back to a safe move."""
    policy = policy_for_tier(tier)
    live = provider()
    if live is None:
        _logger.warning("no OPENROUTER_API_KEY: seat %s plays the timeout move", seat_id)
        return _safe_move(blob, seat_id)

    view = poker.projection_for(blob, seat_id, names)
    # The reads are the AI's memory of earlier hands. They never reach a human:
    # this dictionary is built for the prompt and thrown away.
    ai_view = dict(view)
    ai_view["opponent_reads"] = summarize(reads, for_seat_id=seat_id) if policy.sees_reads else {}

    adapter = AIAdapter(live, policy)
    schema = {"actions": list(view.get("legal_actions") or ())}
    # The model gets the seat's own clock, less a beat to submit the answer in.
    deadline = datetime.now(timezone.utc) + timedelta(seconds=max(2.0, poker.ACTION_SECONDS - 6))
    try:
        decision = await adapter.decide(ai_view, schema, view.get("revision"), deadline)
    except Exception:  # pragma: no cover - a dead model must not hang the table
        _logger.exception("house player at seat %s could not decide", seat_id)
        return _safe_move(blob, seat_id)
    if decision is None:
        return _safe_move(blob, seat_id)
    _logger.info("poker seat %s played %s because: %s", seat_id, dict(decision.action), decision.reason)
    return dict(decision.action)


def remember(reads: dict[int, dict[str, int]], blob: Mapping[str, Any]) -> None:
    """Fold a finished hand into what the table knows about everyone at it."""
    from app.services.holdem.state import HoldemState

    update_from_hand(reads, HoldemState.from_dict(blob["hand"]))


def _safe_move(blob: Mapping[str, Any], seat_id: int) -> dict[str, Any]:
    """Check when checking is free, otherwise fold: what a timeout would do."""
    view = poker.projection_for(blob, seat_id, {})
    kinds = {action["type"] for action in view.get("legal_actions") or ()}
    return {"type": "check"} if "check" in kinds else {"type": "fold"}
