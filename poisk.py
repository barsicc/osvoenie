#!/usr/bin/env python3
"""Поиск ответа на вопрос теста по лекциям и банку проверенных ответов.

Использование:
    python3 poisk.py "глубина моря Приразломное"
    python3 poisk.py            # интерактивный режим
    python3 poisk.py --build    # пересобрать poisk.html (поиск в браузере / на телефоне)

Сначала показываются совпадения из банка вопросов (data/questions.json) —
там ответы, проверенные на учебном портале. Затем — фрагменты лекций и справочника.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUESTIONS = ROOT / "data" / "questions.json"
NOTES = sorted((ROOT / "lectures").glob("*.md"))

STOP = set("""и в во на не что как к ко с со по из за от до о об а но или ли же бы для при
это этот эта эти тот та те так также его ее их он она они мы вы я который которая которые
какой какая какие каков какова каково чем где когда является являются относится относятся
находится расположено расположены вопрос ответ выберите один верно ли""".split())


def norm(text):
    text = text.lower().replace("ё", "е")
    return re.findall(r"[a-zа-я]+|\d+(?:[.,]\d+)?", text)


def stems(text):
    out = []
    for w in norm(text):
        if w in STOP:
            continue
        if w[0].isdigit():
            out.append(w.replace(",", "."))
        elif len(w) <= 3:
            out.append(w)
        else:
            out.append(w[:5])  # грубая «основа» слова: первые 5 букв
    return out


def build_corpus():
    docs = []
    for q in json.loads(QUESTIONS.read_text(encoding="utf-8")):
        # текст вопроса весит больше, чем варианты и пояснение
        body = q["q"] + " " + q["q"] + " " + " ".join(q.get("opts", [])) + " " + " ".join(q["ans"])
        docs.append({"kind": "test", "title": q["q"], "ans": q["ans"], "opts": q.get("opts", []),
                     "multi": q.get("multi", False), "status": q.get("status", ""),
                     "note": q.get("note", ""), "src": q.get("src", ""), "id": q["id"],
                     "text": body})
    for path in NOTES:
        section = path.stem
        para = []

        def flush():
            if para:
                txt = "\n".join(para).strip()
                if txt:
                    docs.append({"kind": "note", "title": section, "file": path.name, "text": txt})
                para.clear()

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                flush()
                section = line.lstrip("#").strip()
                continue
            if not line.strip():
                flush()
                continue
            # каждый пункт списка / строка таблицы — отдельный фрагмент, с заголовком раздела
            if line.lstrip().startswith(("-", "|", "*")) or re.match(r"\s*\d+\.", line):
                flush()
                docs.append({"kind": "note", "title": section, "file": path.name, "text": line.strip()})
            else:
                para.append(line)
        flush()
    return docs


def search(query, docs, top=6):
    qs = stems(query)
    if not qs:
        return []
    n = len(docs)
    toks = [stems(d["title"] + " " + d["text"]) if d["kind"] == "note" else stems(d["text"]) for d in docs]
    df = {}
    for t in toks:
        for s in set(t):
            df[s] = df.get(s, 0) + 1
    avg = sum(len(t) for t in toks) / n
    res = []
    for d, t in zip(docs, toks):
        if not t:
            continue
        tf = {}
        for s in t:
            tf[s] = tf.get(s, 0) + 1
        score, hit = 0.0, 0
        for s in set(qs):
            if s in tf:
                hit += 1
                idf = math.log(1 + (n - df[s] + 0.5) / (df[s] + 0.5))
                f = tf[s]
                score += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * len(t) / avg))
        if not hit:
            continue
        score *= (hit / len(set(qs))) ** 1.5
        if d["kind"] == "test":
            score *= 1.6
        res.append((score, d))
    res.sort(key=lambda x: -x[0])
    return res[:top]


def show(results):
    if not results:
        print("  Ничего не найдено — попробуй другие ключевые слова (название месторождения, термин, число).")
        return
    for score, d in results:
        if d["kind"] == "test":
            print(f"\n★ БАНК ОТВЕТОВ [{d['id']}]  {d['title']}")
            print("  ✅ ОТВЕТ: " + "  |  ".join(d["ans"]) + ("   (несколько ответов)" if d["multi"] else ""))
            if d["note"]:
                print("  💡 " + d["note"])
            if d["status"]:
                print("  ↳ " + d["status"])
        else:
            print(f"\n• {d['title']}  ({d['file']})")
            print("  " + d["text"].replace("\n", "\n  "))


def build_html(docs):
    tpl = (ROOT / "tools" / "poisk_template.html").read_text(encoding="utf-8")
    data = json.dumps(docs, ensure_ascii=False)
    stop = json.dumps(sorted(STOP), ensure_ascii=False)
    out = tpl.replace("/*__DATA__*/[]", data).replace("/*__STOP__*/[]", stop)
    (ROOT / "poisk.html").write_text(out, encoding="utf-8")
    print(f"poisk.html собран: {len(docs)} фрагментов")
    lines = ["# Банк ответов (проверено на учебном портале)", "",
             "Файл собирается командой `python3 poisk.py --build` из `data/questions.json`.", ""]
    for d in docs:
        if d["kind"] != "test":
            continue
        lines.append(f"### {d['id']}. {d['title']}")
        if d["opts"]:
            lines.append("Варианты: " + " · ".join(d["opts"]))
        lines.append("**Ответ: " + " | ".join(d["ans"]) + "**" + (" *(несколько ответов)*" if d["multi"] else ""))
        if d["note"]:
            lines.append("> " + d["note"])
        if d["status"]:
            lines.append(f"<sub>{d['status']}</sub>")
        lines.append("")
    (ROOT / "OTVETY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    docs = build_corpus()
    args = sys.argv[1:]
    if args and args[0] == "--build":
        build_html(docs)
        return
    if args:
        show(search(" ".join(args), docs))
        return
    print("Введите вопрос (пустая строка — выход).")
    while True:
        try:
            q = input("\n? ").strip()
        except EOFError:
            break
        if not q:
            break
        show(search(q, docs))


if __name__ == "__main__":
    main()
