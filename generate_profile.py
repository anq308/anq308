"""Build a monochrome GitHub profile from public repository language bytes."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = "anq308"
ROOT = Path(__file__).resolve().parent


def api(path):
    headers = {"User-Agent": "anq308-profile", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
        return json.load(response)


def collect():
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{OWNER}/repos?per_page=100&page={page}")
        repos.extend(r for r in batch if not r["fork"] and r["name"] != OWNER)
        if len(batch) < 100:
            break
        page += 1
    languages = Counter()
    rows = []
    for repo in repos:
        data = api(f"/repos/{OWNER}/{repo['name']}/languages")
        languages.update(data)
        rows.append({"name": repo["name"], "languages": data, "url": repo["html_url"]})
    if not languages:
        raise RuntimeError("No language data; preserve previous charts")
    return languages, rows


def render(languages, rows, dark):
    bg, fg, muted, line, track = ("#0d1117", "#f0f0f0", "#999999", "#303030", "#242424") if dark else ("#ffffff", "#151515", "#737373", "#dedede", "#ededed")
    total = sum(languages.values())
    ranked = languages.most_common(6)
    if len(languages) > 6:
        ranked.append(("Other", sum(v for _, v in languages.most_common()[6:])))
    height = 470 + 46 * len(ranked)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">anq308 / Web development / Language composition</title>',
             '<desc id="desc">Language shares by GitHub language bytes in original public repositories. Not a proficiency score.</desc>',
             f'<rect width="1000" height="{height}" fill="{bg}"/>']

    def text(x, y, value, size=20, color=fg, weight=400, spacing=0, anchor="start"):
        parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rule(y):
        parts.append(f'<path d="M36 {y}H964" stroke="{line}"/>')

    text(36, 40, "ANQ / 308", 14, muted, spacing=3)
    text(964, 40, "DEVELOPER PROFILE", 13, muted, spacing=2, anchor="end")
    text(31, 144, "anq308", 94, weight=600, spacing=-5)
    text(36, 188, "Веб-разработка. Интерфейсы. Эксперименты.", 22, muted)
    rule(222)
    text(36, 263, "01", 15, muted)
    text(92, 263, "Стек в репозиториях", 25, weight=600)
    text(964, 263, f"{len(rows):02d} PUBLIC PROJECTS", 13, muted, spacing=1, anchor="end")
    # All bars share a 0–100% scale, independent of the leading language.
    text(270, 306, "0", 12, muted)
    text(886, 306, "100%", 12, muted, anchor="end")
    for index, (name, value) in enumerate(ranked):
        y = 342 + index * 46
        share = value / total * 100
        text(36, y + 4, name, 20)
        parts.append(f'<rect x="270" y="{y - 12}" width="616" height="8" fill="{track}"/>')
        parts.append(f'<rect x="270" y="{y - 12}" width="{616 * share / 100:.3f}" height="8" fill="{fg}"/>')
        text(964, y + 4, f"{share:.1f}%", 18, anchor="end")
    bottom = 342 + len(ranked) * 46
    text(36, bottom + 18, "Доля кода по GitHub Languages · публичные проекты · без форков", 16, muted)
    text(36, bottom + 44, "Проценты показывают состав репозиториев, а не уровень владения.", 16, muted)
    rule(bottom + 76)
    text(36, bottom + 114, "HTML / CSS / JAVASCRIPT / VUE / PHP", 15, muted, spacing=1)
    text(964, bottom + 114, datetime.now(timezone.utc).strftime("%d.%m.%Y"), 14, muted, anchor="end")
    parts.append('</svg>')
    return '\n'.join(parts)


if __name__ == "__main__":
    languages, rows = collect()
    for dark in (False, True):
        name = "profile-dark.svg" if dark else "profile-light.svg"
        (ROOT / name).write_text(render(languages, rows, dark), encoding="utf-8")
    (ROOT / "language-source.json").write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "languages": dict(languages), "repositories": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dict(languages.most_common()), ensure_ascii=False))
