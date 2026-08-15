"""Core data types. Complete - do not modify without updating every module."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator

# Matches {W}, {2/U}, {U/P}, {X}, {C}, {S}
SYMBOL = re.compile(r"\{([^}]+)\}")
COLORS = ("W", "U", "B", "R", "G")

BASIC_LANDS = {
    "plains", "island", "swamp", "mountain", "forest", "wastes",
    "snow-covered plains", "snow-covered island", "snow-covered swamp",
    "snow-covered mountain", "snow-covered forest",
}


@dataclass(frozen=True)
class Card:
    name: str
    mana_cost: str = ""
    mana_value: float = 0.0
    type_line: str = ""
    oracle_text: str = ""
    colors: frozenset[str] = frozenset()
    color_identity: frozenset[str] = frozenset()
    layout: str = "normal"
    legalities: dict[str, str] = field(default_factory=dict)
    faces: tuple["Card", ...] = ()

    @property
    def types(self) -> frozenset[str]:
        """Card types only, left of the em dash."""
        left = self.type_line.split("\u2014")[0]
        return frozenset(left.replace("Legendary", "").split())

    @property
    def subtypes(self) -> frozenset[str]:
        if "\u2014" not in self.type_line:
            return frozenset()
        return frozenset(self.type_line.split("\u2014", 1)[1].split())

    @property
    def is_land(self) -> bool:
        return "Land" in self.types

    @property
    def is_basic_land(self) -> bool:
        return self.name.lower() in BASIC_LANDS

    @property
    def is_permanent(self) -> bool:
        return bool(self.types & {
            "Artifact", "Creature", "Enchantment", "Land",
            "Planeswalker", "Battle",
        })

    def cost_symbols(self) -> list[str]:
        """Symbols in the mana cost: '{1}{W}{W}' -> ['1', 'W', 'W']."""
        return SYMBOL.findall(self.mana_cost)

    def all_faces(self) -> Iterator["Card"]:
        """Self, then each face for split / MDFC / transform cards."""
        yield self
        yield from self.faces


@dataclass(frozen=True)
class Entry:
    count: int
    card: Card


@dataclass
class Deck:
    mainboard: list[Entry] = field(default_factory=list)
    commanders: list[Card] = field(default_factory=list)
    companion: Card | None = None

    def cards(self) -> Iterator[Card]:
        """Every card instance, respecting counts. Commanders included."""
        for e in self.mainboard:
            for _ in range(e.count):
                yield e.card
        yield from self.commanders

    def unique_cards(self) -> Iterator[Card]:
        seen: set[str] = set()
        for c in self.cards():
            if c.name not in seen:
                seen.add(c.name)
                yield c

    @property
    def size(self) -> int:
        return sum(e.count for e in self.mainboard) + len(self.commanders)


@dataclass(frozen=True)
class Violation:
    rule: str          # stable machine-readable id, e.g. "singleton"
    message: str       # human-readable, one line
    card: str | None = None

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"
