from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cards import Card


@dataclass(frozen=True, slots=True)
class PlayerState:
    seat_id: int
    stack: int
    hole_cards: tuple[Card, ...] = ()
    folded: bool = False
    all_in: bool = False
    total_contribution: int = 0
    street_contribution: int = 0
    has_acted: bool = False


@dataclass(frozen=True, slots=True)
class HoldemState:
    players: tuple[PlayerState, ...]
    deck: tuple[Card, ...]
    deck_index: int
    community_cards: tuple[Card, ...]
    street: str
    dealer_seat: int
    small_blind_seat: int
    big_blind_seat: int
    current_seat: int | None
    current_bet: int
    min_raise: int
    small_blind: int
    big_blind: int
    hand_number: int = 1
    winners: tuple[int, ...] = ()
    payouts: tuple[tuple[int, int], ...] = ()
    # Every action taken this hand, in order. Public information: it is only
    # what everyone at the table watched happen.
    action_log: tuple[Mapping[str, Any], ...] = ()

    @property
    def pot(self) -> int:
        return sum(player.total_contribution for player in self.players)

    @property
    def total_chips(self) -> int:
        return self.pot + sum(player.stack for player in self.players)

    def player(self, seat_id: int) -> PlayerState:
        for player in self.players:
            if player.seat_id == seat_id:
                return player
        raise KeyError(f"unknown seat {seat_id}")

    def stacks(self) -> Mapping[int, int]:
        return {player.seat_id: player.stack for player in self.players}

    # A hand in progress has to survive a process restart, and PlayRoom keeps
    # room state as one JSON blob rather than as rows. These are the two halves
    # of that round trip; the shape is the one the client already reads.
    def to_dict(self) -> dict[str, Any]:
        return {
            "players": [
                {
                    "seat_id": player.seat_id,
                    "stack": player.stack,
                    "hole_cards": [_card_dict(card) for card in player.hole_cards],
                    "folded": player.folded,
                    "all_in": player.all_in,
                    "total_contribution": player.total_contribution,
                    "street_contribution": player.street_contribution,
                    "has_acted": player.has_acted,
                }
                for player in self.players
            ],
            "deck": [_card_dict(card) for card in self.deck],
            "deck_index": self.deck_index,
            "community_cards": [_card_dict(card) for card in self.community_cards],
            "street": self.street,
            "dealer_seat": self.dealer_seat,
            "small_blind_seat": self.small_blind_seat,
            "big_blind_seat": self.big_blind_seat,
            "current_seat": self.current_seat,
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "hand_number": self.hand_number,
            "winners": list(self.winners),
            "payouts": [list(payout) for payout in self.payouts],
            "action_log": [dict(entry) for entry in self.action_log],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HoldemState":
        return cls(
            players=tuple(
                PlayerState(
                    seat_id=player["seat_id"],
                    stack=player["stack"],
                    hole_cards=tuple(_card(card) for card in player.get("hole_cards", ())),
                    folded=player.get("folded", False),
                    all_in=player.get("all_in", False),
                    total_contribution=player.get("total_contribution", 0),
                    street_contribution=player.get("street_contribution", 0),
                    has_acted=player.get("has_acted", False),
                )
                for player in data["players"]
            ),
            deck=tuple(_card(card) for card in data.get("deck", ())),
            deck_index=data.get("deck_index", 0),
            community_cards=tuple(_card(card) for card in data.get("community_cards", ())),
            street=data["street"],
            dealer_seat=data["dealer_seat"],
            small_blind_seat=data["small_blind_seat"],
            big_blind_seat=data["big_blind_seat"],
            current_seat=data.get("current_seat"),
            current_bet=data.get("current_bet", 0),
            min_raise=data.get("min_raise", 0),
            small_blind=data["small_blind"],
            big_blind=data["big_blind"],
            hand_number=data.get("hand_number", 1),
            winners=tuple(data.get("winners", ())),
            payouts=tuple((seat, amount) for seat, amount in data.get("payouts", ())),
            action_log=tuple(dict(entry) for entry in data.get("action_log", ())),
        )


def _card_dict(card: Card) -> dict[str, Any]:
    return {"rank": card.rank, "suit": card.suit}


def _card(data: Mapping[str, Any]) -> Card:
    return Card(rank=data["rank"], suit=data["suit"])
