"""Color identity computation.

STUB MODULE - task t07.
Signatures are fixed. Do not rename or change parameters.
"""

from __future__ import annotations

from .models import Card


def color_identity(card: Card) -> frozenset[str]:
    """Compute a card's color identity from scratch.

    Do NOT read card.color_identity - that is Scryfall's precomputed answer and
    using it defeats the task. Derive it from mana_cost and oracle_text.

    Identity is the set of colors in W U B R G appearing in:
      - the mana cost, across all faces
      - mana symbols in rules text, across all faces
      - any color indicator

    Rules that matter:
      - hybrid {W/U} contributes both W and U
      - Phyrexian {U/P} contributes U
      - generic, colorless {C}, snow {S}, and {X} contribute nothing
      - reminder text in parentheses is excluded
      - both faces of a DFC or split card contribute

    Task t07.
    """
    raise NotImplementedError


def identity_string(identity: frozenset[str]) -> str:
    """Render an identity in WUBRG order, e.g. {'U','B','R'} -> 'UBR'.

    Empty identity renders as 'C'. Helper for messages; also task t07.
    """
    raise NotImplementedError
