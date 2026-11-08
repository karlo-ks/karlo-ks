#!/usr/bin/env python3
"""Render the neofetch-style ~/about card (assets/about.svg).

Edit INFO below and run:  python .github/scripts/about_card.py
"""
import html
import os
import random

INFO = [
    ("education", "FER Zagreb · Computing, 4th year"),
    ("role", "QA Specialist @ Njuškalo"),
    ("focus", "AI agent security · jailbreaks"),
    ("building", "Infradeck"),
    ("learning", "AI agent security · prompt injection"),
    ("uptime", "coding since 2018"),
    ("open_to", "work · collaboration · open source"),
    ("languages", "Croatian · English"),
    ("interests", "engineering of all kinds · cars · motorcycles · boats · watches"),
    ("location", "Zagreb, HR"),
]
USER, HOST = "karlo", "fer"

BG, FG, DIM, LINE, ACC = "#05070a", "#e6edf3", "#7d8590", "#30363d", "#ff7b72"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

# Meteor shower (left side): bigger, glowing meteors streaming down-left from one radiant point,
# like a real shower. Clipped to the left half so they never cross the neofetch text.
SHOWER_RADIANT = (470, 34)
SHOWER_CLIP = (24, 36, 476, None)  # x1, y1, x2, y2 (y2 filled in at render time)


def meteor_shower(H: int) -> tuple[str, str]:
    """Return (svg, css) for the meteor shower."""
    import math
    r = random.Random(42)
    rx0, ry0 = SHOWER_RADIANT
    svg, css = [], []
    n = 21
    for i in range(n):
        ang = math.radians(r.uniform(128, 152))          # direction of travel (down-left)
        ux, uy = math.cos(ang), math.sin(ang)
        ux, uy = ux, abs(uy)
        start_d = r.uniform(20, 330)                     # how far from the radiant it lights up
        sx, sy = rx0 + ux * start_d, ry0 + uy * start_d
        dist = r.uniform(200, 320)
        tail = r.uniform(120, 190)
        width = r.uniform(1.8, 2.8)
        head = width + r.uniform(.4, 1.0)
        dur = r.uniform(3.6, 6.8)                        # cycle length
        fly = r.uniform(.9, 1.5)                         # time the meteor is visible
        delay = r.uniform(0, 6)
        col = ACC if i % 4 == 1 else FG
        tx, ty = -ux * tail, -uy * tail
        cls = f"sh{i}"
        pct = fly / dur * 100
        svg.append(
            f'<defs><linearGradient id="g{cls}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{tx:.1f}" y2="{ty:.1f}">'
            f'<stop offset="0" stop-color="{col}" stop-opacity=".95"/><stop offset=".35" stop-color="{col}" stop-opacity=".4"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<g transform="translate({sx:.1f} {sy:.1f})"><g class="{cls}">'
            f'<line x1="0" y1="0" x2="{tx:.1f}" y2="{ty:.1f}" stroke="url(#g{cls})" stroke-width="{width:.1f}" stroke-linecap="round"/>'
            f'<circle r="{head * 3.2:.1f}" fill="{col}" opacity=".12"/>'
            f'<circle r="{head:.1f}" fill="{col}"/></g></g>')
        css.append(
            f".{cls} {{ opacity: 0; animation: {cls} {dur:.2f}s cubic-bezier(.3,0,.7,1) {delay:.2f}s infinite; }}"
            f"@keyframes {cls} {{ 0% {{ transform: translate(0,0); opacity: 0 }} {pct * .12:.2f}% {{ opacity: 1 }}"
            f" {pct * .7:.2f}% {{ opacity: 1 }} {pct:.2f}% {{ transform: translate({ux * dist:.1f}px,{uy * dist:.1f}px); opacity: 0 }}"
            f" 100% {{ transform: translate({ux * dist:.1f}px,{uy * dist:.1f}px); opacity: 0 }} }}")
    x1, y1, x2, _ = SHOWER_CLIP
    clip = f'<clipPath id="showerClip"><rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{H - 36 - y1}"/></clipPath>'
    return f'<defs>{clip}</defs><g clip-path="url(#showerClip)">{"".join(svg)}</g>', "\n    ".join(css)


def starfield(w, h, n, seed, keep_out):
    """Sparse star background like the banner; keeps text areas clear."""
    r = random.Random(seed)
    out = []
    while len(out) < n:
        x, y = r.uniform(6, w - 6), r.uniform(40, h - 6)
        if any(a < x < c and b < y < d for a, b, c, d in keep_out):
            continue
        rad = r.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2])
        # every star shimmers: a third twinkle strongly, the rest glow softly, all out of sync
        cls = "tw" if r.random() < 0.33 else "gl"
        out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{rad + (.2 if cls == "tw" else 0)}" fill="{FG}" '
                   f'style="animation-delay:-{r.uniform(0, 6):.2f}s;animation-duration:{r.uniform(2.5, 6.5):.1f}s;'
                   f'--o:{r.uniform(.35, .9):.2f}"/>')
    return "".join(out)


def shooting_star(x, y, dx, dy, cls):
    """A meteor that streaks from (x, y) by (dx, dy); its tail points back along the path."""
    n = (dx * dx + dy * dy) ** .5
    tx, ty = -dx / n * 110, -dy / n * 110
    return (f'<defs><linearGradient id="t{cls}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{tx:.1f}" y2="{ty:.1f}">'
            f'<stop offset="0" stop-color="{FG}" stop-opacity=".9"/><stop offset="1" stop-color="{FG}" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<g transform="translate({x} {y})"><g class="{cls}">'
            f'<line x1="0" y1="0" x2="{tx:.1f}" y2="{ty:.1f}" stroke="url(#t{cls})" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle r="1.8" fill="{FG}"/></g></g>')


def render() -> str:
    e = html.escape
    W = 1200
    top = 104
    lh = 22
    rows = 1 + 1 + len(INFO) + 1  # header, rule, info, palette
    H = top + rows * lh + 40
    key_w = max(len(k) for k, _ in INFO) + 2

    style = f"""
    text {{ font-family: {MONO}; white-space: pre; }}
    .f {{ animation: f .9s ease-out both; }}
    @keyframes f {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    .tw {{ animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: .15 }} }}
    .gl {{ opacity: var(--o); animation: gl 5s ease-in-out infinite; }}
    @keyframes gl {{ 0%,100% {{ opacity: var(--o) }} 50% {{ opacity: calc(var(--o) * .35) }} }}
    .cursor {{ animation: blink 1.1s step-end infinite; }}
    .m1 {{ animation: m1 9s linear 2s infinite; opacity: 0; }}
    .m2 {{ animation: m2 13s linear 6s infinite; opacity: 0; }}
    @keyframes m1 {{ 0% {{ transform: translate(0, 0); opacity: 0 }} 1% {{ opacity: 1 }}
      9% {{ transform: translate(-460px, 44px); opacity: 0 }} 100% {{ transform: translate(-460px, 44px); opacity: 0 }} }}
    @keyframes m2 {{ 0% {{ transform: translate(0, 0); opacity: 0 }} 1% {{ opacity: 1 }}
      7% {{ transform: translate(-260px, 62px); opacity: 0 }} 100% {{ transform: translate(-260px, 62px); opacity: 0 }} }}
    @keyframes blink {{ 50% {{ opacity: 0 }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    """

    out = []
    # info (right)
    x = 500
    y = top
    delay = .4
    out.append(f'<text class="f" style="animation-delay:{delay}s" x="{x}" y="{y}" font-size="17" font-weight="700">'
               f'<tspan fill="{ACC}">{USER}</tspan><tspan fill="{DIM}">@</tspan><tspan fill="{ACC}">{HOST}</tspan></text>')
    y += lh
    out.append(f'<text class="f" style="animation-delay:{delay}s" x="{x}" y="{y}" font-size="15" fill="{LINE}">{"-" * 46}</text>')
    for k, v in INFO:
        y += lh
        delay += .12
        out.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" font-size="15">'
                   f'<tspan fill="{ACC}">{e(k)}</tspan><tspan fill="{DIM}">:{" " * (key_w - len(k) - 1)}</tspan>'
                   f'<tspan fill="{FG}">{e(v)}</tspan></text>')
    y += lh + 6
    delay += .15
    palette = ["#05070a", "#161b22", "#30363d", "#7d8590", "#e6edf3", "#ffa198", "#ff7b72", "#da3633"]
    blocks = "".join(f'<rect x="{x + i * 30}" y="{y - 13}" width="30" height="16" fill="{c}"'
                     f'{" stroke=" + chr(34) + LINE + chr(34) if i == 0 else ""}/>' for i, c in enumerate(palette))
    out.append(f'<g class="f" style="animation-delay:{delay:.2f}s">{blocks}</g>')

    prompt_y = H - 22
    shower_svg, shower_css = meteor_shower(H)
    style = style.replace("@media (prefers-reduced-motion", shower_css + "\n    @media (prefers-reduced-motion", 1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="about {USER}: {e("; ".join(f"{k}: {v}" for k, v in INFO))}">
  <style>{style}</style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <line x1="0" y1="34" x2="{W}" y2="34" stroke="{LINE}"/>
  <circle cx="22" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="40" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="58" cy="17" r="5" fill="none" stroke="{DIM}"/>
  <text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">{USER}@{HOST}: ~/about</text>
  <g>{starfield(W, H, 120, 9, [(30, 44, 230, 76), (490, 80, 1160, top + (len(INFO) + 2) * lh + 14), (30, H - 44, 90, H)])}</g>
  {shower_svg}
  {shooting_star(1185, 44, -460, 44, "m1")}
  {shooting_star(470, 48, -260, 62, "m2")}
  <text x="40" y="66" font-size="14"><tspan fill="{ACC}">$</tspan><tspan fill="{FG}"> neofetch --about</tspan></text>
  {"".join(out)}
  <text class="f" style="animation-delay:{delay + .3:.2f}s" x="40" y="{prompt_y}" font-size="14"><tspan fill="{ACC}">$</tspan><tspan fill="{FG}"> </tspan><tspan class="cursor" fill="{FG}">█</tspan></text>
</svg>'''


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    with open(os.path.join(root, "assets", "about.svg"), "w") as f:
        f.write(render())
