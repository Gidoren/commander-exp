"""Mana curve and deck statistics.

STUB MODULE - tasks t01, t02, t03.
Signatures are fixed. Do not rename or change parameters.
"""

from __future__ import annotations

from .models import Deck


def nonland_count(deck: Deck) -> int:
    """Number of nonland card instances in the deck, commanders included.

    Task t01.
    """
    raise NotImplementedError


def average_mana_value(deck: Deck) -> float:
    """Mean mana value across nonland cards, respecting counts.

    Lands are excluded entirely. Returns 0.0 for a deck with no nonlands.
    For split and modal double-faced cards, use the card's own mana_value.

    Task t02.
    """
    raise NotImplementedError


def curve_histogram(deck: Deck) -> dict[int, int]:
    """Map integer mana value -> count of nonland cards at that value.

    X in a mana cost counts as 0. Values of 7 or more collapse into the key 7.
    Mana values are integers in practice; floor any halves. Keys with a count
    of zero are omitted.

    Task t03.
    """
    raise NotImplementedError
