"""Parser tests. Complete - this is the house style to follow."""

import pytest

from deckcheck.models import Card
from deckcheck.parse import UnknownCard, parse


class FakeDB:
    def __init__(self, names):
        self._d = {n.lower(): Card(name=n) for n in names}
        for n in names:
            if "//" in n:
                self._d[n.split("//")[0].strip().lower()] = self._d[n.lower()]

    def get(self, name):
        return self._d.get(name.strip().lower())


@pytest.fixture
def db():
    return FakeDB(["Sol Ring", "Lightning Bolt", "Fire // Ice",
                   "Kefka, Court Mage", "Lurrus of the Dream-Den"])


def test_counts_and_names(db):
    deck = parse("1 Sol Ring\n4 Lightning Bolt", db)
    assert [(e.count, e.card.name) for e in deck.mainboard] == [
        (1, "Sol Ring"), (4, "Lightning Bolt")
    ]


def test_set_code_and_collector_number_ignored(db):
    deck = parse("4 Lightning Bolt (2XM) 129", db)
    assert deck.mainboard[0].card.name == "Lightning Bolt"


def test_foil_marker_ignored(db):
    deck = parse("1 Sol Ring (C21) 263 *F*", db)
    assert deck.mainboard[0].count == 1


def test_split_card_front_name_resolves(db):
    deck = parse("1 Fire", db)
    assert deck.mainboard[0].card.name == "Fire // Ice"


def test_sections(db):
    text = "Commander\n1 Kefka, Court Mage\n\nCompanion\n1 Lurrus of the Dream-Den\n\nDeck\n1 Sol Ring"
    deck = parse(text, db)
    assert [c.name for c in deck.commanders] == ["Kefka, Court Mage"]
    assert deck.companion.name == "Lurrus of the Dream-Den"
    assert len(deck.mainboard) == 1


def test_sideboard_skipped(db):
    deck = parse("Deck\n1 Sol Ring\n\nSideboard\n1 Lightning Bolt", db)
    assert len(deck.mainboard) == 1


def test_comments_and_blanks(db):
    deck = parse("// a comment\n\n# another\n1 Sol Ring", db)
    assert len(deck.mainboard) == 1


def test_unknown_card_strict(db):
    with pytest.raises(UnknownCard):
        parse("1 Not A Real Card", db)


def test_unknown_card_lenient(db):
    deck = parse("1 Not A Real Card\n1 Sol Ring", db, strict=False)
    assert len(deck.mainboard) == 1
