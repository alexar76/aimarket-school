"""Lesson 04 handles a real, spendable key: it must not end up in code or in saved output.

Notebooks are shared and saved with their outputs; the lesson used to have learners paste
a topped-up key into a code cell and printed a freshly opened key in full.
"""

from pathlib import Path

import yaml

SCHOOL = Path(__file__).resolve().parents[1]


def _code(lesson_id: str) -> str:
    data = yaml.safe_load((SCHOOL / "lessons.yaml").read_text(encoding="utf-8"))
    lesson = next(L for L in data["lessons"] if L["id"] == lesson_id)
    cells = lesson.get("notebook") or lesson.get("code") or lesson.get("cells") or []
    return "\n".join(str(c) for c in cells) if isinstance(cells, list) else str(cells)


def test_lesson_04_never_puts_the_key_in_code_or_output():
    text = (SCHOOL / "notebooks" / "ai-pays-ai.ipynb").read_text(encoding="utf-8")
    assert "API_KEY = ''" not in text and 'API_KEY = \\"\\"' not in text
    assert "print('  ' + API_KEY)" not in text
    assert "getpass.getpass(" in text
    assert "AIMARKET_API_KEY" in text
