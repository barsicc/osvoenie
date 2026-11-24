"""Собрать навигационную библиографию из первых строк карточек."""
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
GROUPS = {
    "0": "Определения и методика сравнения",
    "1": "Геология, месторождения и ресурсы",
    "2": "Лёд, волнение, батиметрия и мерзлота",
    "3": "Технологии и транспорт",
    "4": "Статус, экономика и экология",
    "5": "Дополнительная научная и отраслевая литература",
}


def main():
    cards = sorted((PROJECT / "source_cards").glob("S[0-9][0-9][0-9].md"))
    lines = [
        "# Библиография и карточки",
        "",
        "Карточка содержит полное описание, точные указатели, степень доступа и",
        "ссылку на издателя или официальный архив. Заголовки ниже служат навигацией.",
        "Учебные материалы указаны отдельно в [контексте курса](../course_context/COURSE_CONTEXT.md).",
        "Карта запросов и ограничений доступа — в [журнале поиска](bibliographic_search.md).",
        "",
    ]
    for digit, group in GROUPS.items():
        group_cards = [card for card in cards if card.stem[1] == digit]
        if not group_cards:
            continue
        lines.extend([f"## {group}", ""])
        for card in group_cards:
            title = card.read_text(encoding="utf-8").splitlines()[0]
            label = re.sub(r"^#\s+S\d{3}\s*[.·—–-]?\s*", "", title)
            lines.append(f"- [{card.stem}](../source_cards/{card.name}) — {label}")
        lines.append("")
    (PROJECT / "research" / "10_bibliography.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
