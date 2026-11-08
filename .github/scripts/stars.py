"""Shared shimmering star background used by every card on the profile.

Every star is animated: about a third twinkle strongly, the rest glow softly, each with its own
duration and phase so the sky never pulses in sync. Include STAR_CSS in the card's <style>.
"""
import random

STAR_CSS = """
    .tw { animation: tw 4s ease-in-out infinite; }
    @keyframes tw { 0%,100% { opacity: 1 } 50% { opacity: .15 } }
    .gl { opacity: var(--o); animation: gl 5s ease-in-out infinite; }
    @keyframes gl { 0%,100% { opacity: var(--o) } 50% { opacity: calc(var(--o) * .35) } }
"""


def starfield(w, h, n, seed, y0=40, keep_out=(), skip=None, fg="#e6edf3", margin=6):
    """Return n star <circle>s inside (margin..w-margin, y0..h-margin).

    keep_out: boxes (x1, y1, x2, y2) to leave empty; skip: optional f(x, y) -> True to leave empty.
    """
    r = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < n * 200:
        tries += 1
        x, y = r.uniform(margin, w - margin), r.uniform(y0, h - margin)
        if any(a < x < c and b < y < d for a, b, c, d in keep_out) or (skip and skip(x, y)):
            continue
        rad = r.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2])
        cls = "tw" if r.random() < 0.33 else "gl"
        out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{rad + (.2 if cls == "tw" else 0)}" fill="{fg}" '
                   f'style="animation-delay:-{r.uniform(0, 6):.2f}s;animation-duration:{r.uniform(2.5, 6.5):.1f}s;'
                   f'--o:{r.uniform(.35, .9):.2f}"/>')
    return "".join(out)
