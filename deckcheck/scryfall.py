"""Scryfall bulk data loading. Complete. Offline after the first fetch."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from .models import Card

BULK_INDEX = "https://api.scryfall.com/bulk-data"
DATA = Path(__file__).resolve().parent.parent / "data" / "scryfall.json"


def fetch(dest: Path = DATA) -> Path:
    """Download the default_cards bulk file once. Run via `make data`."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    with urllib.request.urlopen(BULK_INDEX) as r:
        entries = json.load(r)["data"]
    url = next(e["download_uri"] for e in entries if e["type"] == "default_cards")
    urllib.request.urlretrieve(url, dest)
    return dest


def _to_card(raw: dict) -> Card:
    faces = tuple(
        Card(
            name=f.get("name", ""),
            mana_cost=f.get("mana_cost", ""),
            mana_value=float(f.get("cmc", raw.get("cmc", 0)) or 0),
            type_line=f.get("type_line", ""),
            oracle_text=f.get("oracle_text", ""),
            colors=frozenset(f.get("colors", [])),
            color_identity=frozenset(raw.get("color_identity", [])),
        )
        for f in raw.get("card_faces", [])
    )
    return Card(
        name=raw["name"],
        mana_cost=raw.get("mana_cost", ""),
        mana_value=float(raw.get("cmc", 0) or 0),
        type_line=raw.get("type_line", ""),
        oracle_text=raw.get("oracle_text", ""),
        colors=frozenset(raw.get("colors", [])),
        color_identity=frozenset(raw.get("color_identity", [])),
        layout=raw.get("layout", "normal"),
        legalities=raw.get("legalities", {}),
        faces=faces,
    )


class CardDB:
    """Name -> Card index. Front-face and full '//' names both resolve."""

    def __init__(self, cards: list[Card]):
        self._by_name: dict[str, Card] = {}
        for c in cards:
            self._by_name.setdefault(c.name.lower(), c)
            if "//" in c.name:
                front = c.name.split("//")[0].strip().lower()
                self._by_name.setdefault(front, c)

    @classmethod
    def load(cls, path: Path = DATA) -> "CardDB":
        raw = json.loads(path.read_text())
        keep = [r for r in raw if r.get("lang") == "en" and not r.get("digital")]
        return cls([_to_card(r) for r in keep])

    def get(self, name: str) -> Card | None:
        return self._by_name.get(name.strip().lower())

    def __contains__(self, name: str) -> bool:
        return name.strip().lower() in self._by_name

    def __len__(self) -> int:
        return len(self._by_name)
