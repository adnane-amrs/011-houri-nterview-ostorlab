"""Whole-file local storage. One operator, atomic replacement, no network."""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

from dispatch_cli import models


def read_object(path: str | pathlib.Path) -> models.Record:
    with pathlib.Path(path).open(encoding="utf-8") as stream:
        document = json.load(stream)
    if isinstance(document, dict) is False:
        raise models.Error("input must be a JSON object")
    return document


def write_object(path: str | pathlib.Path, document: models.Record) -> None:
    """Serialize before touching the target; replace only complete local JSON."""
    target = pathlib.Path(path)
    encoded = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
            temporary = stream.name
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            pathlib.Path(temporary).unlink(missing_ok=True)
