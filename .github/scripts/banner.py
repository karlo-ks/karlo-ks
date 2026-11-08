#!/usr/bin/env python3
"""Render the banner (assets/space-banner.svg) and footer (assets/space-footer.svg).

Run:  python .github/scripts/banner.py
"""
import os
from stars import STAR_CSS, starfield

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
BG, FG, DIM, LINE, ACC = "#05070a", "#e6edf3", "#7d8590", "#30363d", "#ff7b72"

def stars(w, h, n, seed, y0=0, keep_out=None):
    return starfield(w, h, n, seed, y0=y0, keep_out=[keep_out] if keep_out else [], margin=4)

STYLE = STAR_CSS + f"""
    text {{ font-family: {MONO}; }}
    .cursor {{ animation: blink 1.1s step-end infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0 }} }}
    .l1 {{ animation: show 1.2s ease-out 0.2s both; }} .l2 {{ animation: show 1.4s ease-out 0.8s both; }}
    .l3 {{ animation: show 1.2s ease-out 1.5s both; }} .l4 {{ animation: show 1.2s ease-out 2.2s both; }}
    @keyframes show {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    .type {{ animation: type .7s steps(6) .4s both; }}
    @keyframes type {{ from {{ width: 0 }} to {{ width: 70px }} }}
    .spin {{ animation: spin 60s linear infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes spin {{ to {{ transform: rotate(360deg) }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
"""

def banner():
    W, H = 1200, 300
    cx, cy, R = 960, 160, 70
    # wireframe planet: meridians as ellipses with varying rx, parallels as horizontal ellipses
    import math
    mer = ""
    N, steps = 6, 36
    for k in range(N):
        ph = k*math.pi/N
        vals = ";".join(f"{R*abs(math.cos(2*math.pi*i/steps/2 + ph)):.1f}" for i in range(steps+1))
        mer += f'<ellipse cx="0" cy="0" rx="{R*abs(math.cos(ph)):.1f}" ry="{R}" fill="none" stroke="{DIM}" stroke-width="0.8" opacity=".55"><animate attributeName="rx" dur="20s" repeatCount="indefinite" values="{vals}"/></ellipse>'

    par = ""
    for t in (-0.6, -0.3, 0, 0.3, 0.6):
        y = R*t; rx = R*(1-t*t)**0.5
        par += f'<ellipse cx="0" cy="{y:.1f}" rx="{rx:.1f}" ry="{rx*0.12:.1f}" fill="none" stroke="{DIM}" stroke-width="0.8" opacity=".55"/>'
    orbit_rx, orbit_ry = 150, 38
    orbit = f"M{-orbit_rx},0 a{orbit_rx},{orbit_ry} 0 1,0 {2*orbit_rx},0 a{orbit_rx},{orbit_ry} 0 1,0 {-2*orbit_rx},0"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="karlo@fer:~$ whoami – Karlo Kajba Šimanić, CS student @ FER Zagreb, AI security">
  <style>{STYLE}</style>
  <defs>
    <clipPath id="front"><rect x="-200" y="0" width="400" height="100"/></clipPath>
    <clipPath id="planetMask"><circle r="{R}"/></clipPath>
  </defs>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <!-- title bar -->
  <line x1="0" y1="34" x2="{W}" y2="34" stroke="{LINE}"/>
  <circle cx="22" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="40" cy="17" r="5" fill="none" stroke="{DIM}"/><circle cx="58" cy="17" r="5" fill="none" stroke="{DIM}"/>
  <text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">karlo@fer: ~/space</text>
  <g>
    {stars(W, H-6, 95, 3, y0=40, keep_out=(40, 60, 620, 270))}
  </g>

  <!-- wireframe planet -->
  <g transform="translate({cx} {cy})">
    <ellipse rx="{orbit_rx}" ry="{orbit_ry}" fill="none" stroke="{LINE}" stroke-dasharray="3 5" transform="rotate(-14)"/>
    <g transform="rotate(-14)"><circle r="3.5" fill="{ACC}">
      <animateMotion dur="14s" repeatCount="indefinite" path="{orbit}"/>
    </circle></g>
    <circle r="{R}" fill="{BG}"/>
    <g transform="rotate(-14)">
      <g clip-path="url(#planetMask)">{par}{mer}</g>
    </g>
    <circle r="{R}" fill="none" stroke="{FG}" stroke-width="1.2"/>
    <g transform="rotate(-14)">
      <ellipse rx="{orbit_rx}" ry="{orbit_ry}" fill="none" stroke="{DIM}" stroke-dasharray="3 5" clip-path="url(#front)"/>
      <g clip-path="url(#front)"><circle r="3.5" fill="{ACC}">
        <animateMotion dur="14s" repeatCount="indefinite" path="{orbit}"/>
      </circle></g>
    </g>
  </g>
  <text x="{cx}" y="{cy+R+60}" text-anchor="middle" font-size="11" fill="{DIM}" opacity=".7">[ orbit: stable ]</text>

  <!-- terminal -->
  <g font-size="18">
    <text class="l1" x="56" y="96"><tspan fill="{ACC}">karlo@fer</tspan><tspan fill="{DIM}">:~$</tspan><tspan fill="{FG}"> whoami</tspan></text>
    <text class="l2" x="56" y="146" font-size="40" font-weight="700" fill="{FG}">Karlo Kajba Šimanić</text>
    <text class="l3" x="56" y="184" fill="{DIM}">CS student @ FER Zagreb  //  exploring AI security</text>
    <text class="l4" x="56" y="236"><tspan fill="{ACC}">karlo@fer</tspan><tspan fill="{DIM}">:~$ </tspan><tspan class="cursor" fill="{FG}">█</tspan></text>
  </g>
</svg>'''

def footer():
    W, H = 1200, 110
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="end of transmission">
  <style>{STYLE}</style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <g>
    {stars(W, 70, 45, 21, y0=8, keep_out=(380, 25, 820, 65)) if False else stars(W, 62, 45, 21, y0=8, keep_out=(380, 25, 820, 60))}
  </g>
  <path d="M40 {H+20} Q600 30 1160 {H+20}" fill="none" stroke="{DIM}" stroke-width="1"/>
  <path d="M40 {H+20} Q600 30 1160 {H+20}" fill="none" stroke="{LINE}" stroke-width="1" stroke-dasharray="2 6" transform="translate(0 12)"/>
  <text x="{W/2}" y="50" text-anchor="middle" font-size="14" fill="{DIM}">// end of transmission <tspan class="cursor" fill="{FG}">█</tspan></text>
</svg>'''

open(os.path.join(out, "space-banner.svg"), "w").write(banner())
open(os.path.join(out, "space-footer.svg"), "w").write(footer())
