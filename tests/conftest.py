"""Shared fixtures. Visible to the agent."""

import pytest

from deckcheck.models import Card


def card(name, cost="", mv=0.0, types="Creature", text="", **kw):
    """Build a Card without touching Scryfall. Use this in unit tests."""
    return Card(name=name, mana_cost=cost, mana_value=mv,
                type_line=types, oracle_text=text, **kw)


@pytest.fixture
def mk():
    return card
