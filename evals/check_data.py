"""Consistency checks for the taxonomy and the golden evaluation cases.

Run from the repo root:
    uv run --no-project --python 3.13 evals/check_data.py

Standard library only. Exits with a non-zero code if anything is wrong.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_DIR = ROOT / "packages" / "taxonomy"
GOLDEN_FILE = ROOT / "evals" / "golden" / "events.json"

MIN_CASES = 20
LANGUAGES = {"fr", "en", "mixed"}
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
# Inclusive-writing rule from the style guide: no "(e)" and no middle dot.
GENDERED_PATTERNS = [re.compile(r"\(es?\)"), re.compile("\u00b7")]

SINGLE_FIELDS = ["event_type", "dress_code", "role", "time_of_day", "indoor_outdoor"]
LIST_FIELDS = {"activities_include": "activity", "impression_include": "impression"}
ALLOWED_EXPECTED = set(SINGLE_FIELDS) | set(LIST_FIELDS) | {"formality", "needs_clarification"}

errors = []


def load(path):
    # utf-8-sig also accepts files that were saved with a BOM.
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def check_taxonomy():
    domains = load(TAXONOMY_DIR / "taxonomy.json")["domains"]
    all_keys = set()
    for domain, keys in domains.items():
        if not KEY_PATTERN.match(domain):
            errors.append(f"bad domain name: {domain}")
        if len(keys) != len(set(keys)):
            errors.append(f"duplicate keys in domain: {domain}")
        for key in keys:
            if not KEY_PATTERN.match(key):
                errors.append(f"bad key: {domain}.{key}")
            all_keys.add(f"{domain}.{key}")

    for lang in ("fr", "en"):
        labels = load(TAXONOMY_DIR / f"labels.{lang}.json")
        for key in sorted(all_keys - labels.keys()):
            errors.append(f"labels.{lang}: missing label for {key}")
        for key in sorted(labels.keys() - all_keys):
            errors.append(f"labels.{lang}: label for unknown key {key}")
        for key, label in labels.items():
            if not label.strip():
                errors.append(f"labels.{lang}: empty label for {key}")
            if lang == "fr":
                for pattern in GENDERED_PATTERNS:
                    if pattern.search(label):
                        errors.append(f"labels.fr: gendered construct in {key}")
    return domains, len(all_keys)


def check_golden(domains):
    cases = load(GOLDEN_FILE)
    seen = set()
    for index, case in enumerate(cases, start=1):
        cid = case.get("id", f"#{index}")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        if case.get("language") not in LANGUAGES:
            errors.append(f"{cid}: language must be one of {sorted(LANGUAGES)}")
        if not str(case.get("prompt", "")).strip():
            errors.append(f"{cid}: empty prompt")
        expected = case.get("expected")
        if not isinstance(expected, dict) or not expected:
            errors.append(f"{cid}: 'expected' must be a non-empty object")
            continue
        for field in sorted(set(expected) - ALLOWED_EXPECTED):
            errors.append(f"{cid}: unknown expected field {field}")
        for field in SINGLE_FIELDS:
            if field in expected and expected[field] not in domains[field]:
                errors.append(f"{cid}: {field}={expected[field]!r} is not in the taxonomy")
        for field, domain in LIST_FIELDS.items():
            for value in expected.get(field, []):
                if value not in domains[domain]:
                    errors.append(f"{cid}: {field} contains {value!r}, not in the taxonomy")
        if "formality" in expected:
            value = expected["formality"]
            valid = (
                isinstance(value, list)
                and len(value) == 2
                and all(isinstance(n, int) and 1 <= n <= 5 for n in value)
                and value[0] <= value[1]
            )
            if not valid:
                errors.append(f"{cid}: formality must be [min, max] within 1..5")

    if len(cases) < MIN_CASES:
        errors.append(f"only {len(cases)} golden cases, at least {MIN_CASES} required")
    languages = Counter(case.get("language") for case in cases)
    for lang in sorted(LANGUAGES):
        if languages[lang] == 0:
            errors.append(f"no golden case in language: {lang}")
    return cases, languages


def main():
    domains, key_count = check_taxonomy()
    cases, languages = check_golden(domains)
    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for message in errors:
            print(f"  - {message}")
        return 1
    summary = ", ".join(f"{lang} {languages[lang]}" for lang in sorted(LANGUAGES))
    print(f"OK: {key_count} taxonomy keys, {len(cases)} golden cases ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
