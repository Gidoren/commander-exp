"""Scryfall bulk data loading. Offline after the first fetch.

Scryfall requires clients to send a descriptive User-Agent and an Accept
header; requests without them are rejected with HTTP 400.
"""

from __future__ import annotations

import gzip
import json
import urllib.request
from pathlib import Path

from .models import Card

BULK_INDEX = "https://api.scryfall.com/bulk-data"
DATA = Path(__file__).resolve().parent.parent / "data" / "scryfall.json"

# Identify yourself here. Scryfall asks that clients do, and rejects the
# default urllib agent outright.
HEADERS = {
    "User-Agent": "deckcheck/0.1 (https://github.com/Gidoren/commander-exp)",
    "Accept": "application/json",
}


def _open(url: str, timeout: int = 120):
    """Open a URL with the headers Scryfall requires."""
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=HEADERS), timeout=timeout
    )


def fetch(dest: Path = DATA, *, force: bool = False) -> Path:
    """Download the default_cards bulk file once. Run via `make data`.

    Scryfall serves bulk data as gzip-compressed JSONL; this decompresses
    it and writes a plain JSON array to `dest`, so CardDB.load can read it
    directly. Writes to a .part file and renames on completion, so an
    interrupted download is not mistaken for a finished one on the next run.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return dest

    with _open(BULK_INDEX) as r:
        entries = json.load(r)["data"]
    entry = next(e for e in entries if e["type"] == "default_cards")
    url, size = entry["jsonl_download_uri"], entry.get("compressed_size", 0)
    print(f"downloading default_cards ({size / 1e6:.0f} MB compressed)")

    with _open(url, timeout=600) as r, gzip.GzipFile(fileobj=r) as gz:
        cards = [json.loads(line) for line in gz]

    if len(cards) < 10_000:
        raise RuntimeError(f"download truncated; got only {len(cards)} cards")

    tmp = dest.with_suffix(".part")
    tmp.write_text(json.dumps(cards))
    tmp.replace(dest)
    print(f"wrote {dest} ({dest.stat().st_size / 1e6:.0f} MB)")
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
        if not path.exists():
            raise FileNotFoundError(f"{path} missing - run `make data` first")
        raw = json.loads(path.read_text())
        keep = [r for r in raw if r.get("lang") == "en" and not r.get("digital")]
        return cls([_to_card(r) for r in keep])

    def get(self, name: str) -> Card | None:
        return self._by_name.get(name.strip().lower())

    def __contains__(self, name: str) -> bool:
        return name.strip().lower() in self._by_name

    def __len__(self) -> int:
        return len(self._by_name)
