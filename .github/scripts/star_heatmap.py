#!/usr/bin/env python3
"""Render the GitHub contribution calendar as a minimal terminal-style star map.

Each day is a star: the more contributions, the bigger and brighter it is.
Days on the busiest level glow green and twinkle. Neighbouring active days are
joined with faint lines so streaks look like constellations.

Usage (in GitHub Actions):
    GITHUB_TOKEN=... python star_heatmap.py --user karloks2005 --out assets/star-heatmap.svg
Preview with local data:
    python star_heatmap.py --input days.json --out preview.svg
"""
import argparse
import datetime as dt
import json
import os
import urllib.request

from stars import STAR_CSS, starfield

BG, FG, DIM, LINE, ACC = "#05070a", "#e6edf3", "#7d8590", "#30363d", "#7ee787"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""


def fetch(user: str, token: str):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "star-heatmap"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        {"date": d["date"], "count": d["contributionCount"], "level": LEVELS[d["contributionLevel"]]}
        for w in weeks for d in w["contributionDays"]
    ]


def streaks(days):
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)
    # current streak: allow today to be empty (day isn't over yet)
    current = 0
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current += 1
    return longest, current


def render(days, user):
    W, H = 1200, 300
    pitch = 17.5
    vpitch = 22
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    cells = []
    for i, d in enumerate(days):
        idx = i + offset
        cells.append((idx // 7, idx % 7, d))
    ncols = cells[-1][0] + 1
    gx = (W - (ncols - 1) * pitch) / 2 + 18
    gy = 112
    pos = {(c, r): (gx + c * pitch, gy + r * vpitch) for c, r, _ in cells}
    lvl = {(c, r): d["level"] for c, r, d in cells}

    total = sum(d["count"] for d in days)
    longest, current = streaks(days)

    out = []
    # constellation lines between neighbouring active days
    for (c, r), l in lvl.items():
        if l < 2:
            continue
        for nb in ((c + 1, r), (c, r + 1)):
            if lvl.get(nb, 0) >= 2:
                (x1, y1), (x2, y2) = pos[(c, r)], pos[nb]
                out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                           f'stroke="#484f58" stroke-width="0.8" class="c" style="animation-delay:{c*0.025+0.6:.2f}s"/>')

    # stars, grouped by week column for a left-to-right reveal
    by_col = {}
    for c, r, d in cells:
        x, y = pos[(c, r)]
        l = d["level"]
        tip = f'<title>{d["date"]}: {d["count"]} contribution{"s" if d["count"] != 1 else ""}</title>'
        if l == 0:
            s = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.9" fill="{DIM}" opacity=".35">{tip}</circle>'
        elif l < 4:
            rad, op = {1: (1.5, .45), 2: (2.2, .7), 3: (3.0, .95)}[l]
            s = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{FG}" opacity="{op}">{tip}</circle>'
        else:
            delay = (c * 7 + r) % 9 * 0.45
            s = (f'<g class="hot" style="animation-delay:{delay:.2f}s">'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{ACC}" opacity=".12"/>'
                 f'<path d="M{x-6:.1f} {y:.1f}H{x+6:.1f}M{x:.1f} {y-6:.1f}V{y+6:.1f}" stroke="{ACC}" stroke-width=".8" opacity=".7"/>'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{ACC}">{tip}</circle></g>')
        by_col.setdefault(c, []).append(s)
    for c in sorted(by_col):
        out.append(f'<g class="col" style="animation-delay:{c*0.025:.3f}s">{"".join(by_col[c])}</g>')

    # month labels
    months, seen = [], set()
    for c, r, d in cells:
        date = dt.date.fromisoformat(d["date"])
        key = (date.year, date.month)
        if date.day <= 7 and key not in seen and c < ncols - 1:
            seen.add(key)
            months.append(f'<text x="{gx + c*pitch - 3:.1f}" y="{gy - 18}" font-size="11" fill="{DIM}">{date.strftime("%b").lower()}</text>')
    days_lbl = "".join(
        f'<text x="{gx - 22}" y="{gy + r*vpitch + 4:.1f}" font-size="10" fill="{DIM}" text-anchor="end">{n}</text>'
        for r, n in ((1, "mon"), (3, "wed"), (5, "fri")))

    lx = W - 268
    legend = (f'<text x="{lx}" y="{H-22}" font-size="11" fill="{DIM}">less</text>'
              f'<circle cx="{lx+46}" cy="{H-26}" r="0.9" fill="{DIM}" opacity=".5"/>'
              f'<circle cx="{lx+64}" cy="{H-26}" r="1.5" fill="{FG}" opacity=".45"/>'
              f'<circle cx="{lx+82}" cy="{H-26}" r="2.2" fill="{FG}" opacity=".7"/>'
              f'<circle cx="{lx+100}" cy="{H-26}" r="3" fill="{FG}" opacity=".95"/>'
              f'<circle cx="{lx+120}" cy="{H-26}" r="3.2" fill="{ACC}"/>'
              f'<text x="{lx+134}" y="{H-22}" font-size="11" fill="{DIM}">more</text>')

    style = """
    text { font-family: %s; }
    .col { animation: in .6s ease-out both; }
    .c { animation: in 1s ease-out both; }
    @keyframes in { from { opacity: 0 } to { opacity: 1 } }
    .hot { animation: hot 4s ease-in-out infinite; }
    @keyframes hot { 0%%,100%% { opacity: 1 } 50%% { opacity: .35 } }
    .cursor { animation: blink 1.1s step-end infinite; }
    @keyframes blink { 50%% { opacity: 0 } }
    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
    """ % MONO + STAR_CSS

    grid = (gx - 34, gy - 34, gx + (ncols - 1) * pitch + 10, gy + 6 * vpitch + 10)
    sky = starfield(W, H, 70, 17, keep_out=[grid, (30, 46, 560, 74), (W - 480, 48, W - 30, 74),
                                            (30, H - 38, 260, H), (W - 285, H - 42, W - 30, H)])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{user}: {total} contributions in the last year as a star map">
  <style>{style}</style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <line x1="0" y1="34" x2="{W}" y2="34" stroke="{LINE}"/>
  <circle cx="22" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="40" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="58" cy="17" r="5" fill="none" stroke="{DIM}"/>
  <text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">{user}@github: ~/contributions</text>
  {sky}
  <text x="40" y="66" font-size="14"><tspan fill="{ACC}">$</tspan><tspan fill="{FG}"> git log --since="1 year ago" | starmap</tspan></text>
  <text x="{W-40}" y="66" font-size="12" fill="{DIM}" text-anchor="end">{total} contributions  ·  longest streak {longest}d  ·  current {current}d</text>
  {"".join(months)}
  {days_lbl}
  {"".join(out)}
  <text x="40" y="{H-22}" font-size="11" fill="{DIM}">updated {dt.date.today().isoformat()} <tspan class="cursor" fill="{FG}">█</tspan></text>
  {legend}
</svg>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "karloks2005"))
    ap.add_argument("--input", help="JSON list of {date,count,level} instead of the API")
    ap.add_argument("--out", required=True)
    ap.add_argument("--accent", default=None, help="accent colour, e.g. #ff7b72")
    a = ap.parse_args()
    if a.accent:
        globals()["ACC"] = a.accent
    if a.input:
        with open(a.input) as f:
            days = json.load(f)
    else:
        days = fetch(a.user, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        f.write(render(days, a.user))


if __name__ == "__main__":
    main()
