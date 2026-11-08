#!/usr/bin/env python3
"""Render terminal-style cards for featured projects and update the README.

Projects are listed in .github/featured.json, e.g.:
    [
      "my-repo",                                   # repo of the profile owner
      "some-org/other-repo",                       # any public repo
      {"repo": "my-app", "description": "Custom text", "note": "team lead", "language": "Go"}
    ]

Each card is written to assets/projects/<name>.svg and the README section between
<!-- FEATURED:START --> and <!-- FEATURED:END --> is regenerated with links.

Usage (in GitHub Actions):
    GITHUB_TOKEN=... python featured_projects.py --user karloks2005
A repo that is private or does not exist yet is shown as a "coming soon" card
(needs "description"; optional "language"), and becomes a normal card once public.
Optional "note" is a short label shown in the card's title bar.
Optional "logo" is a path to an .svg/.png in this repo (e.g. assets/logos/x.svg);
Logos are embedded exactly as they are (original colours, no recolouring).
Optional "title" is the exact project name to display (capitalisation kept);
without it the repository name from GitHub is used as-is.

Preview with local data:
    python featured_projects.py --input repos.json --outdir preview/ --no-readme
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import textwrap
import urllib.request

BG, FG, DIM, LINE = "#05070a", "#e6edf3", "#7d8590", "#30363d"
ACC = "#ff7b72"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name nameWithOwner description url homepageUrl
    stargazerCount forkCount pushedAt
    primaryLanguage { name }
  }
}"""


def fetch(full: str, token: str):
    owner, name = full.split("/", 1)
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"owner": owner, "name": name}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "featured-projects"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return (data.get("data") or {}).get("repository")  # None if private / missing


def ago(iso: str) -> str:
    then = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (dt.datetime.now(dt.timezone.utc) - then).days
    if days < 1:
        return "today"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def logo_svg(path: str, x: float, y: float, size: float) -> str:
    """Inline a logo file into the card (external images don't load inside <img> SVGs)."""
    import base64
    if path.lower().endswith(".svg"):
        src = open(path).read()
        src = re.sub(r"<\?xml[^>]*>|<!DOCTYPE[^>]*>", "", src).strip()
        # place the logo's own <svg> at x/y with a fixed size; its design and colours stay untouched
        src = re.sub(r"<svg\b", f'<svg x="{x}" y="{y}" width="{size}" height="{size}"', src, count=1)
        src = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"(?=[^>]*\bx=)', r"\1", src, count=2)
        return src
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="data:{mime};base64,{data}"/>'


def card(repo: dict, description: str | None, note: str | None = None, soon: bool = False,
         display: str | None = None, logo: str | None = None) -> str:
    W, H = 580, 170
    e = html.escape
    desc = description if description is not None else (repo.get("description") or "no description yet")
    wrap = 50 if logo else 58
    lines = textwrap.wrap(desc, wrap)[:2]
    if len(textwrap.wrap(desc, wrap)) > 2:
        lines[-1] = lines[-1][:wrap - 3].rstrip() + "..."
    lang = (repo.get("primaryLanguage") or {}).get("name") or "—"
    name = display or repo["name"]  # exact project name, keeps its capitalisation
    title = name if len(name) <= 26 else name[:25] + "…"
    note_svg = (f'<text x="{W-18}" y="19" text-anchor="end" font-size="11" fill="{ACC}">{e(note)}</text>'
                if note else "")
    if soon:
        footer = ((f'<text x="24" y="{H-13}" font-size="12" fill="{DIM}"><tspan fill="{ACC}">●</tspan> {e(lang)}</text>'
                   if lang != "—" else f'<text x="24" y="{H-13}" font-size="12" fill="{DIM}">private repo</text>') +
                  f'<text x="{W-24}" y="{H-13}" font-size="12" fill="{ACC}" text-anchor="end">'
                  f'<tspan class="tw">●</tspan> status: coming soon</text>')
    else:
        footer = (f'<text x="24" y="{H-13}" font-size="12" fill="{DIM}"><tspan fill="{ACC}">●</tspan> {e(lang)}'
                  f'    ★ {repo["stargazerCount"]}    ⑂ {repo["forkCount"]}</text>'
                  f'<text x="{W-24}" y="{H-13}" font-size="12" fill="{DIM}" text-anchor="end">updated {ago(repo["pushedAt"])}</text>')
    if logo:
        lx, ly = W - 66, 66
        deco = (f'<circle cx="{lx}" cy="{ly}" r="28" fill="none" stroke="{LINE}"/>'
                f'<circle class="tw" cx="{lx+26}" cy="{ly-12}" r="1.6" fill="{FG}"/>'
                f'<circle cx="{lx-34}" cy="{ly+22}" r=".9" fill="{FG}" opacity=".5"/>'
                + logo_svg(logo, lx - 15, ly - 15, 30))
    else:
        deco = (f'<circle cx="{W-34}" cy="58" r="1.1" fill="{FG}" opacity=".6"/>'
                f'<circle class="tw" cx="{W-58}" cy="74" r="1.4" fill="{FG}"/>'
                f'<circle cx="{W-24}" cy="88" r=".8" fill="{FG}" opacity=".4"/>')
    desc_svg = "".join(
        f'<text x="24" y="{100 + i*19}" font-size="13" fill="{DIM}">{e(l)}</text>' for i, l in enumerate(lines))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{e(name)}: {e(desc)}">
  <style>
    text {{ font-family: {MONO}; }}
    .in {{ animation: in .9s ease-out .2s both; }}
    @keyframes in {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    .tw {{ animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity: .9 }} 50% {{ opacity: .2 }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <line x1="0" y1="30" x2="{W}" y2="30" stroke="{LINE}"/>
  <circle cx="18" cy="15" r="4.5" fill="none" stroke="{DIM}"/><circle cx="34" cy="15" r="4.5" fill="none" stroke="{DIM}"/><circle cx="50" cy="15" r="4.5" fill="none" stroke="{DIM}"/>
  <text x="{W/2}" y="19" text-anchor="middle" font-size="11" fill="{DIM}">~/projects/{e(title)}</text>
  {note_svg}
  {deco}
  <g class="in">
    <text x="24" y="74" font-size="21" font-weight="700"><tspan fill="{ACC}">❯ </tspan><tspan fill="{FG}">{e(title)}</tspan></text>
    {desc_svg}
    <line x1="24" y1="{H-34}" x2="{W-24}" y2="{H-34}" stroke="{LINE}" stroke-dasharray="2 4"/>
    {footer}
  </g>
</svg>'''


def readme_block(entries) -> str:
    def cell(e):
        img = f'<img src="./assets/projects/{e["name"]}.svg" alt="{html.escape(e["title"])}" width="49%"/>'
        return f'<a href="{e["url"]}">{img}</a>' if e["url"] else img
    cells = [cell(e) for e in entries]
    rows = ["<p>\n  " + "\n  ".join(cells[i:i + 2]) + "\n</p>" for i in range(0, len(cells), 2)]
    return "<!-- FEATURED:START -->\n" + "\n".join(rows) + "\n<!-- FEATURED:END -->"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "karloks2005"))
    ap.add_argument("--config", default=".github/featured.json")
    ap.add_argument("--input", help="JSON list of repository objects instead of the API (preview)")
    ap.add_argument("--outdir", default="assets/projects")
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--no-readme", action="store_true")
    ap.add_argument("--accent", default=None)
    a = ap.parse_args()
    if a.accent:
        globals()["ACC"] = a.accent

    with open(a.config) as f:
        config = [i if isinstance(i, dict) else {"repo": i} for i in json.load(f)]
    preview = {}
    if a.input:  # preview: {"owner/name": repo-object}
        with open(a.input) as f:
            preview = json.load(f)

    items = []  # (repo, description, note, soon, title, logo)
    for item in config:
        full = item["repo"] if "/" in item["repo"] else f'{a.user}/{item["repo"]}'
        repo = preview.get(full) if a.input else fetch(full, os.environ["GITHUB_TOKEN"])
        if repo:
            items.append((repo, item.get("description"), item.get("note"), False, item.get("title"), item.get("logo")))
        elif item.get("description"):
            # private or not created yet: show a "coming soon" card until it goes public
            stub = {"name": full.split("/", 1)[1], "url": None,
                    "primaryLanguage": {"name": item.get("language", "—")}}
            items.append((stub, item["description"], item.get("note"), True, item.get("title"), item.get("logo")))
        else:
            print(f"warning: {full} is not accessible and has no description, skipping")

    os.makedirs(a.outdir, exist_ok=True)
    keep = set()
    entries = []
    for repo, desc, note, soon, display, logo in items:
        fname = f'{repo["name"]}.svg'
        keep.add(fname)
        with open(os.path.join(a.outdir, fname), "w") as f:
            f.write(card(repo, desc, note, soon, display, logo))
        entries.append({"name": repo["name"], "title": display or repo["name"], "url": repo["url"]})
    for old in os.listdir(a.outdir):  # remove cards of projects no longer featured
        if old.endswith(".svg") and old not in keep:
            os.remove(os.path.join(a.outdir, old))

    if not a.no_readme:
        with open(a.readme) as f:
            text = f.read()
        new = re.sub(r"<!-- FEATURED:START -->.*?<!-- FEATURED:END -->", lambda _: readme_block(entries),
                     text, flags=re.S)
        with open(a.readme, "w") as f:
            f.write(new)


if __name__ == "__main__":
    main()
