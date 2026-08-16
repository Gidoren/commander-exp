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

    The boundaries are numeric, not qualitative - apply them in this order:

      4  if there is ANY mass land denial card, OR ANY two-card combo present
         (both cards of a combo_list pair in the deck), OR 4 or more game
         changers.
      3  else if there is 1, 2, or 3 game changers.
      2  else if there is 1 or more tutors.
      1  otherwise (0 game changers, 0 tutors, no mass land denial, no combo).
      5  never returned automatically - distinguishing 4 from 5 is not
         mechanically decidable. Decks that would exceed bracket 3 always
         classify as 4; record why in `reasons` rather than guessing at 5.

    Extra-turn effects are detected and recorded on the report but do not by
    themselves change the bracket.

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
