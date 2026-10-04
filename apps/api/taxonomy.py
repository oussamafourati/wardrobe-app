import json
from functools import lru_cache
from pathlib import Path

# apps/api/taxonomy.py -> repo root -> packages/taxonomy/taxonomy.json
TAXONOMY_FILE = Path(__file__).resolve().parents[2] / "packages" / "taxonomy" / "taxonomy.json"


@lru_cache
def _domains() -> dict[str, list[str]]:
    with open(TAXONOMY_FILE, encoding="utf-8-sig") as handle:
        return json.load(handle)["domains"]


def keys(domain: str) -> set[str]:
    """All valid keys of one taxonomy domain, for example keys("hair_color")."""
    return set(_domains()[domain])
