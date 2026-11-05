"""Small shared vocabulary; dictionaries preserve operator extension fields."""
from __future__ import annotations

import typing

Record = dict[str, typing.Any]
STATES = ("queued", "running", "done", "failed", "cancelled")
TERMINAL_STATES = ("done", "failed", "cancelled")


class Error(ValueError):
    """A local input or operation violates the documented ledger contract."""


def is_nonnegative_int(value: object) -> bool:
    """JSON true/false are not clocks or retry counts."""
    return type(value) is int and value >= 0


def require_schema(ledger: Record, schema: int = 2) -> None:
    if type(ledger.get("schema")) is not int or ledger["schema"] != schema:
        raise Error(f"expected ledger schema {schema}")
    for key in ("jobs", "attempts", "audit"):
        if isinstance(ledger.get(key), list) is False:
            raise Error(f"{key} must be a list")
