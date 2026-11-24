"""Проверить относительные Markdown-ссылки и ссылки на карточки источников."""
import re
from pathlib import Path
from urllib.parse import unquote

PROJECT = Path(__file__).resolve().parents[1]
INLINE_LINK = re.compile(r'!?\[[^]\n]*\]\((<[^>\n]+>|[^)\n]+)\)')
CARD_REF = re.compile(r"\[(S\d{3})(?=[,;\]–])")
CARD_ID = re.compile(r"^(S\d{3})(?:\b|_)")


def main():
    errors = []
    cards = {}
    for path in sorted((PROJECT / "source_cards").glob("*.md")):
        match = CARD_ID.match(path.stem)
        if not match:
            continue
        source_id = match[1]
        if source_id in cards:
            errors.append(f"Повторный ID {source_id}: {path.name}")
        cards[source_id] = path

    docs = sorted(PROJECT.rglob("*.md"))
    for path in docs:
        if "sources" in path.relative_to(PROJECT).parts or path.name == "research_brief.md":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in INLINE_LINK.finditer(line):
                target = unquote(match[1].strip("<>").split("#", 1)[0])
                if not target or re.match(r"^[a-zA-Z][\w+.-]*:", target):
                    continue
                if not (path.parent / target).exists():
                    errors.append(f"{path.relative_to(PROJECT)}:{number}: {target}")
            for match in CARD_REF.finditer(line):
                if match[1] not in cards:
                    errors.append(f"{path.relative_to(PROJECT)}:{number}: {match[1]}")
    for error in errors:
        print(error)
    print(f"Markdown: {len(docs)}, карточек: {len(cards)}, ошибок: {len(errors)}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
