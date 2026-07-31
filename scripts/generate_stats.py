from __future__ import annotations

import json
import math
import os
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from svg_theme import ACCENT, ACCENT_SOFT, BG, BG_RAISED, FG, LINE, MUTED, font_css, shell, svg_document

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
LOGIN = os.getenv("GH_LOGIN", "ov3rf1w")

QUERY = r'''
query Profile($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
'''


def api_data() -> dict:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN or GH_TOKEN before generating live statistics.")

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=370)
    variables = {
        "login": LOGIN,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{today.isoformat()}T23:59:59Z",
    }
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "ov3rf1w-profile"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]["user"]


def calendar_days(collection: dict) -> list[tuple[date, int]]:
    result = []
    for week in collection["contributionCalendar"]["weeks"]:
        for item in week["contributionDays"]:
            result.append((date.fromisoformat(item["date"]), int(item["contributionCount"])))
    return sorted(result)


def streaks(days: list[tuple[date, int]]) -> tuple[int, int, str, str]:
    active = {day: count for day, count in days}
    today = datetime.now(timezone.utc).date()
    cursor = today if active.get(today, 0) else today - timedelta(days=1)
    current = 0
    current_end = cursor
    while active.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    current_start = cursor + timedelta(days=1)

    longest = 0
    run = 0
    longest_start = longest_end = days[0][0] if days else today
    run_start = longest_start
    for day, count in days:
        if count > 0:
            if run == 0:
                run_start = day
            run += 1
            if run > longest:
                longest = run
                longest_start, longest_end = run_start, day
        else:
            run = 0

    current_range = "—" if current == 0 else f"{current_start:%d %b} — {current_end:%d %b}"
    longest_range = "—" if longest == 0 else f"{longest_start:%d %b} — {longest_end:%d %b %Y}"
    return current, longest, current_range.upper(), longest_range.upper()


def panel_title(index: str, title: str) -> str:
    return f'''
<text x="24" y="31" fill="{ACCENT}" font-family="'Geist Mono'" font-size="10" letter-spacing="1.6">{index}</text>
<text x="24" y="58" fill="{FG}" font-family="'Archivo'" font-size="22">{title}</text>
'''


def make_stats(collection: dict, days: list[tuple[date, int]]) -> str:
    total = collection["contributionCalendar"]["totalContributions"]
    parts = {
        "COMMITS": collection["totalCommitContributions"],
        "PULL REQUESTS": collection["totalPullRequestContributions"],
        "REVIEWS": collection["totalPullRequestReviewContributions"],
        "ISSUES": collection["totalIssueContributions"],
    }
    recent = days[-84:]
    buckets = [sum(count for _, count in recent[i:i + 7]) for i in range(0, len(recent), 7)]
    maximum = max(buckets or [1]) or 1
    points = []
    for index, value in enumerate(buckets):
        x = 26 + index * (438 / max(1, len(buckets) - 1))
        y = 184 - (value / maximum) * 52
        points.append((x, y))
    path = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points))

    metrics = []
    for index, (label, value) in enumerate(parts.items()):
        x = 25 + (index % 2) * 225
        y = 91 + (index // 2) * 45
        metrics.append(f'<text x="{x}" y="{y}" fill="{FG}" font-family="\'Manrope\'" font-size="17">{value}</text>')
        metrics.append(f'<text x="{x + 43}" y="{y}" fill="{MUTED}" font-family="\'Geist Mono\'" font-size="9" letter-spacing="1">{label}</text>')

    body = shell(490, 220) + panel_title("01 / SIGNAL", "CONTRIBUTIONS") + f'''
<text x="466" y="54" text-anchor="end" fill="{ACCENT}" font-family="'Archivo'" font-size="34">{total}</text>
{''.join(metrics)}
<path d="M26 187H464" stroke="{LINE}"/>
<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="2"/>
<path d="{path} L464 187 L26 187 Z" fill="{ACCENT}" fill-opacity=".08"/>
'''
    return svg_document(490, 220, body, font_css(FONTS))


def make_streak(days: list[tuple[date, int]]) -> str:
    current, longest, current_range, longest_range = streaks(days)
    body = shell(490, 220) + panel_title("02 / RHYTHM", "STREAKS") + f'''
<path d="M245 78V190" stroke="{LINE}"/>
<text x="24" y="117" fill="{ACCENT}" font-family="'Archivo'" font-size="48">{current}</text>
<text x="24" y="142" fill="{FG}" font-family="'Geist Mono'" font-size="10" letter-spacing="1.5">CURRENT DAYS</text>
<text x="24" y="169" fill="{MUTED}" font-family="'Geist Mono'" font-size="9">{current_range}</text>
<text x="270" y="117" fill="{FG}" font-family="'Archivo'" font-size="48">{longest}</text>
<text x="270" y="142" fill="{FG}" font-family="'Geist Mono'" font-size="10" letter-spacing="1.5">LONGEST DAYS</text>
<text x="270" y="169" fill="{MUTED}" font-family="'Geist Mono'" font-size="9">{longest_range}</text>
<circle cx="458" cy="30" r="4" fill="{ACCENT}"/>
'''
    return svg_document(490, 220, body, font_css(FONTS))


def language_totals(user: dict) -> list[tuple[str, int, str]]:
    totals: defaultdict[str, int] = defaultdict(int)
    colors: dict[str, str] = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] += int(edge["size"])
            colors[name] = edge["node"].get("color") or ACCENT
    return [(name, size, colors[name]) for name, size in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:5]]


def make_languages(user: dict) -> str:
    languages = language_totals(user)
    total = sum(size for _, size, _ in languages) or 1
    rows = []
    for index, (name, size, _color) in enumerate(languages):
        percent = size / total * 100
        y = 92 + index * 24
        rows.append(f'<text x="24" y="{y}" fill="{FG}" font-family="\'Geist Mono\'" font-size="10">{name.upper()}</text>')
        rows.append(f'<rect x="152" y="{y - 9}" width="270" height="6" rx="3" fill="{LINE}"/>')
        opacity = max(.38, 1 - index * .13)
        rows.append(f'<rect x="152" y="{y - 9}" width="{270 * percent / 100:.1f}" height="6" rx="3" fill="{ACCENT}" fill-opacity="{opacity:.2f}"/>')
        rows.append(f'<text x="464" y="{y}" text-anchor="end" fill="{MUTED}" font-family="\'Geist Mono\'" font-size="9">{percent:.1f}%</text>')
    if not rows:
        rows.append(f'<text x="24" y="112" fill="{MUTED}" font-family="\'Manrope\'" font-size="14">Public language data will appear after the first run.</text>')
    body = shell(490, 220) + panel_title("03 / MATERIAL", "LANGUAGES") + "".join(rows)
    return svg_document(490, 220, body, font_css(FONTS))


def make_year(days: list[tuple[date, int]]) -> str:
    recent = days[-371:]
    max_count = max((count for _, count in recent), default=1) or 1
    marks = []
    for index, (day, count) in enumerate(recent):
        col, row = divmod(index, 7)
        x, y = 25 + col * 8.25, 82 + row * 16
        if count == 0:
            char, color, opacity = "·", LINE, 1
        else:
            level = min(4, max(1, math.ceil(count / max_count * 4)))
            char = ["·", "░", "▒", "▓", "█"][level]
            color = ACCENT_SOFT if level < 4 else ACCENT
            opacity = 0.48 + level * 0.13
        marks.append(f'<text x="{x:.1f}" y="{y}" fill="{color}" fill-opacity="{opacity:.2f}" font-family="\'JetBrains Mono\'" font-size="11">{char}</text>')
    total = sum(count for _, count in recent)
    body = shell(490, 220) + panel_title("04 / YEAR", "ACTIVITY FIELD") + f'''
<text x="464" y="52" text-anchor="end" fill="{MUTED}" font-family="'Geist Mono'" font-size="9">{total} CONTRIBUTIONS / 53 WEEKS</text>
{''.join(marks)}
<text x="24" y="207" fill="{MUTED}" font-family="'Geist Mono'" font-size="8" letter-spacing="1">ONE CHARACTER PER DAY</text>
'''
    return svg_document(490, 220, body, font_css(FONTS, include_portrait=True))


def main() -> None:
    user = api_data()
    collection = user["contributionsCollection"]
    days = calendar_days(collection)
    ASSETS.mkdir(parents=True, exist_ok=True)
    outputs = {
        "stats.svg": make_stats(collection, days),
        "streak.svg": make_streak(days),
        "languages.svg": make_languages(user),
        "year.svg": make_year(days),
    }
    for filename, content in outputs.items():
        (ASSETS / filename).write_text(content, encoding="utf-8")
        print(f"wrote assets/{filename}")


if __name__ == "__main__":
    main()
