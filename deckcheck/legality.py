"""Commander format legality.

STUB MODULE - tasks t05, t06, t08, t09, t10.
Signatures are fixed. Do not rename or change parameters.
Every function returns a list of Violation; an empty list means legal.

NAME CONVENTION (applies to every function in this module)

Lowercasing applies to MATCHING only, never to what is reported. Every card
name returned - in `Violation.card` and in `Violation.message` - holds the
card's original `Card.name` casing, e.g. "Sol Ring", not "sol ring". Compare
case-insensitively, then use `card.name` unchanged.

Returned lists preserve deck order - iterate `Deck.unique_cards()` (mainboard
first, each distinct name at its first occurrence, then commanders) and append
as you go. Do not sort.
"""

from __future__ import annotations

from .models import Card, Deck, Violation

# Cards whose text reads "A deck can have any number of cards named ...".
ANY_NUMBER = {
    "relentless rats", "shadowborn apostle", "rat colony",
    "persistent petitioners", "dragon's approach", "slime against humanity",
    "tempest hawk",
}

# Cards with a specific numeric cap rather than an unlimited allowance.
CAPPED = {"seven dwarves": 7, "nazg\u00fbl": 9}


def check_deck_size(deck: Deck) -> list[Violation]:
    """Commander decks are exactly 100 cards including commanders.

    A companion sits outside the 100. A deck running Yorion as companion has a
    different floor - that interaction belongs to companions.py, not here.

    Task t05.
    """
    raise NotImplementedError


def check_singleton(deck: Deck) -> list[Violation]:
    """At most one copy of each card by name.

    Exempt: basic lands (any number), names in ANY_NUMBER (any number), and
    names in CAPPED (up to the stated limit).

    One Violation per offending name, not per excess copy.

    See NAME CONVENTION at the top of this module for name casing and order.

    Task t06.
    """
    raise NotImplementedError


def check_color_identity(deck: Deck) -> list[Violation]:
    """Every card's color identity must be a subset of the commanders' union.

    Use identity.color_identity, not the Scryfall field. With two commanders,
    the permitted identity is the union of both.

    No commanders declared: return an empty list. This function only checks
    cards against a commander-derived identity; with no commander to derive
    one from, there is nothing for it to flag. (The missing commander itself
    is check_commanders's problem, not this one's.)

    See NAME CONVENTION at the top of this module for name casing and order.

    Task t08.
    """
    raise NotImplementedError


def check_banlist(deck: Deck, banned: set[str]) -> list[Violation]:
    """Flag any card on the Commander banlist.

    `banned` is a set of lowercase card names, supplied by the caller. Do not
    hardcode a list - it changes. Card.legalities may carry a 'commander' key
    of 'banned' or 'legal'; prefer the passed-in set and fall back to that.

    See NAME CONVENTION at the top of this module for name casing and order.

    Task t09.
    """
    raise NotImplementedError


def check_commanders(deck: Deck) -> list[Violation]:
    """Validate the commander slot, including every partner variant.

    A single commander must be legendary, and either a creature or a
    planeswalker whose text says it can be your commander.

    Two commanders are legal only via one of these, and the variants do not
    mix - two cards with different mechanisms cannot pair:

      Partner              any two cards that both say plain "Partner"
      Partner with X       only with the named card X, and only that card
      Choose a Background   one commander with "Choose a Background",
                            paired with one legendary enchantment Background
      Friends forever      any two cards that both say "Friends forever"
      Doctor's companion   one card with "Doctor's companion", paired with
                           one legendary Time Lord Doctor

    Detect each from oracle_text and type_line.

    See NAME CONVENTION at the top of this module for name casing and order.

    Task t10.
    """
    raise NotImplementedError
