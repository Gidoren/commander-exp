"""Decklist parsing. Complete for the common cases.

Handles the Moxfield / Archidekt export shape:

    Commander
    1 Kefka, Court Mage

    Deck
    1 Sol Ring
    4 Lightning Bolt (2XM) 129
    1 Fire // Ice
"""

from __future__ import annotations

import re

from .models import Card, Deck, Entry
from .scryfall import CardDB

LINE = re.compile(
    r"^\s*(?P<count>\d+)\s*x?\s+"
    r"(?P<name>.+?)"
    r"(?:\s+\((?P<set>[A-Za-z0-9]{3,6})\)(?:\s+(?P<num>\S+))?)?"
    r"(?:\s+\*F\*)?"
    r"\s*$"
)

SECTIONS = {
    "commander": "commander", "commanders": "commander",
    "companion": "companion",
    "deck": "main", "mainboard": "main", "main": "main",
    "sideboard": "skip", "maybeboard": "skip", "considering": "skip",
}


class UnknownCard(ValueError):
    pass


def parse(text: str, db: CardDB, *, strict: bool = True) -> Deck:
    deck = Deck()
    section = "main"

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue

        key = line.rstrip(":").strip().lower()
        if key in SECTIONS:
            section = SECTIONS[key]
            continue
        if section == "skip":
            continue

        m = LINE.match(line)
        if not m:
            if strict:
                raise ValueError(f"unparseable line: {raw!r}")
            continue

        name = m.group("name").strip()
        card = db.get(name)
        if card is None:
            if strict:
                raise UnknownCard(name)
            continue

        count = int(m.group("count"))
        if section == "commander":
            deck.commanders.extend([card] * count)
        elif section == "companion":
            deck.companion = card
        else:
            deck.mainboard.append(Entry(count=count, card=card))

    return deck


def parse_file(path, db: CardDB, *, strict: bool = True) -> Deck:
    from pathlib import Path
    return parse(Path(path).read_text(), db, strict=strict)
