"""Companion deckbuilding restrictions.

STUB MODULE - task t11. The highest-signal task in the set.

Each companion is a structurally different rule. They cannot be derived from
one another by pattern matching - implement each on its own terms.

Signatures are fixed. Do not rename or change parameters.
"""

from __future__ import annotations

from .models import Card, Deck, Violation


def check_companion(deck: Deck, companion: Card) -> list[Violation]:
    """Return violations of the companion's deckbuilding restriction.

    Empty list means the deck satisfies it. The companion itself is never
    part of the deck it constrains.

    The nine companions and their restrictions:

      Lurrus of the Dream-Den
          Every PERMANENT card in the starting deck has mana value 2 or less.
          Nonpermanents are unconstrained.

      Obosh, the Preypiercer
          Every NONLAND card has an ODD mana value.

      Gyruda, Doom of Depths
          Every NONLAND card has an EVEN mana value. Note 0 is even.

      Keruga, the Macrosage
          Every NONLAND card has mana value 3 or greater.

      Jegantha, the Wellspring
          No card has more than one of the SAME mana symbol in its mana cost.
          {1}{R}{R} violates. {1}{W}{U} does not. Hybrid and Phyrexian symbols
          count as the symbol they are written as. Read this one carefully -
          it is the most commonly misimplemented.

      Kaheera, the Orphanguard
          Every CREATURE card is a Cat, Elemental, Nightmare, Dinosaur, or
          Beast. A deck with no creatures satisfies it trivially.

      Umori, the Collector
          Every NONLAND card shares a card type. Any one shared type suffices,
          and cards with multiple types can satisfy it via any of them.

      Zirda, the Dawnwaker
          Every PERMANENT card has an activated ability. An activated ability
          is written "cost: effect" in the rules text. Beware colons that are
          not activated abilities, such as those inside keyword reminder text.

      Yorion, Sky Nomad
          The starting deck contains at least 20 cards MORE than the format
          minimum. In Commander that means 120 rather than 100.

    Task t11.
    """
    raise NotImplementedError


def companion_name_map() -> dict[str, str]:
    """Lowercase companion card name -> stable rule id.

    e.g. {"lurrus of the dream-den": "lurrus", ...}. Used for dispatch and for
    the `rule` field on returned Violations. Task t11.
    """
    raise NotImplementedError
