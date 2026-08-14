"""Commander bracket classification and combo detection.

STUB MODULE - tasks t12, t13.
Signatures are fixed. Do not rename or change parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Deck


@dataclass(frozen=True)
class BracketReport:
    bracket: int                    # 1-5
    game_changers: list[str]
    mass_land_denial: list[str]
    extra_turns: list[str]
    tutors: list[str]
    combos: list[tuple[str, str]]
    reasons: list[str]


def classify(deck: Deck, game_changers: set[str], combo_list: list[tuple[str, str]]) -> BracketReport:
    """Classify a deck into brackets 1-5.

    Both `game_changers` (lowercase names) and `combo_list` are supplied by the
    caller. Do not hardcode either - they change with every update.

    Bracket guidance:
      1  Exhibition   no game changers, no mass land denial, no extra-turn
                      chains, no two-card infinite combos, minimal tutoring
      2  Core         as bracket 1, but a normal amount of tutoring
      3  Upgraded     up to three game changers; no mass land denial; no
                      two-card infinite combo that wins on the spot
      4  Optimized    no restrictions, but not built to win as fast as possible
      5  cEDH         built to win as fast as possible

    Distinguishing 4 from 5 is not mechanically decidable. Return 4 for decks
    that exceed bracket 3 and record the ambiguity in `reasons` rather than
    guessing at 5.

    Detect mass land denial and extra-turn effects from oracle text. Extra-turn
    cards that cannot be chained are treated more leniently than those that can.

    Task t12.
    """
    raise NotImplementedError


def find_combos(deck: Deck, combo_list: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return the two-card combos from combo_list where BOTH cards are present.

    Matching is by lowercase name. Commanders count as present. Return each
    matched pair once, in the order given by combo_list.

    Task t13.
    """
    raise NotImplementedError
