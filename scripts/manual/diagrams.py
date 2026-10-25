"""Write the manual's diagrams as SVG, one set per language.

Usage: python scripts/manual/diagrams.py docs/manual/images
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BRAND = "#0f6e5f"
INK = "#1d2327"
MUTED = "#5b6670"
LINE = "#c9d1d6"
TINT = "#eef6f4"
WARN = "#b42318"
WARN_TINT = "#fdecea"
GREY_TINT = "#f3f5f6"
FONT = "font-family=\"'Source Sans 3', 'DejaVu Sans', Arial, sans-serif\""

T = {
    "en": {
        "flow": [
            ("1", "You ask", "a question in the chat"),
            ("2", "The model answers", "as in any chat"),
            ("3", "Shadowseed notes", "open points as seeds"),
            ("4", "You check a source", "and record it"),
            ("5", "The Gate promotes", "the seed"),
            ("6", "A later answer", "uses it when relevant"),
        ],
        "flow_note": "Steps 1–3 happen in every turn. A seed gains influence only through steps 4 and 5.",
        "states": {
            "found": "Found", "recurring": "Recurring", "promoted": "Promoted", "used": "Used",
            "blocked": "Blocked", "dormant": "Dormant", "expired": "Expired",
            "seen_again": "seen again", "source": "verified source", "relevant": "relevant and allowed",
            "contradiction": "contradiction", "resolve": "resolved + new source",
            "quiet": "not seen for a while", "fade": "faded out", "returns": "topic returns",
            "authority": "can influence answers", "no_authority": "no influence",
        },
        "arch": {
            "browser": "Browser", "client": "Web client", "api": "Local web API",
            "api_sub": "127.0.0.1 only", "core": "Conversation engine",
            "core_sub": "detection · intake · recurrence", "gate": "Validation Gate",
            "gate_sub": "the only route to authority", "pou": "Point-of-use check",
            "store": "Workspace", "store_sub": "SQLite + audit ledger",
            "models": "Model adapters", "ollama": "Ollama (local)", "openai": "OpenAI (internet, optional)",
            "computer": "Your computer",
        },
    },
    "nl": {
        "flow": [
            ("1", "Je stelt", "een vraag in de chat"),
            ("2", "Het model antwoordt", "zoals in elke chat"),
            ("3", "Shadowseed noteert", "open punten als seeds"),
            ("4", "Jij controleert", "een bron en legt die vast"),
            ("5", "De Gate promoveert", "de seed"),
            ("6", "Een later antwoord", "gebruikt hem als hij past"),
        ],
        "flow_note": "Stap 1 tot 3 gebeuren bij elke beurt. Invloed krijgt een seed alleen via stap 4 en 5.",
        "states": {
            "found": "Found", "recurring": "Recurring", "promoted": "Promoted", "used": "Used",
            "blocked": "Blocked", "dormant": "Dormant", "expired": "Expired",
            "seen_again": "opnieuw gezien", "source": "gecontroleerde bron", "relevant": "relevant en toegestaan",
            "contradiction": "tegenspraak", "resolve": "opgelost + nieuwe bron",
            "quiet": "een tijd niet gezien", "fade": "vervaagd", "returns": "onderwerp keert terug",
            "authority": "kan antwoorden beïnvloeden", "no_authority": "geen invloed",
        },
        "arch": {
            "browser": "Browser", "client": "Webclient", "api": "Lokale web-API",
            "api_sub": "alleen 127.0.0.1", "core": "Gespreksmotor",
            "core_sub": "detectie · toelating · terugkeer", "gate": "Validation Gate",
            "gate_sub": "enige route naar zeggenschap", "pou": "Controle bij gebruik",
            "store": "Werkmap", "store_sub": "SQLite + auditlogboek",
            "models": "Modeladapters", "ollama": "Ollama (lokaal)", "openai": "OpenAI (internet, optioneel)",
            "computer": "Jouw computer",
        },
    },
}


def text(x, y, s, size=13, weight=400, fill=INK, anchor="middle"):
    return (f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def box(x, y, w, h, fill="#fff", stroke=LINE, r=10, width=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def arrow(x1, y1, x2, y2, color=MUTED, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8"{d} '
            f'marker-end="url(#arrow-{"w" if color == WARN else "m"})"/>')


def svg(w, h, body):
    defs = (
        "<defs>"
        f'<marker id="arrow-m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>'
        f'<marker id="arrow-w" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{WARN}"/></marker>'
        "</defs>"
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'{defs}<rect width="{w}" height="{h}" fill="#fff"/>{"".join(body)}</svg>\n')


def flow(t):
    body = []
    bw, bh, gap = 222, 78, 34
    for i, (num, title, sub) in enumerate(t["flow"]):
        row, col = divmod(i, 3)
        x = 20 + col * (bw + gap)
        y = 20 + row * (bh + 46)
        authority = i in (3, 4)
        body.append(box(x, y, bw, bh, fill=TINT if authority else "#fff", stroke=BRAND if authority else LINE,
                        width=2 if authority else 1.5))
        body.append(f'<circle cx="{x + 24}" cy="{y + 24}" r="13" fill="{BRAND}"/>')
        body.append(text(x + 24, y + 29, num, 13, 700, "#fff"))
        body.append(text(x + 46, y + 30, title, 14.5, 700, INK, "start"))
        body.append(text(x + 46, y + 52, sub, 12.5, 400, MUTED, "start"))
        if col < 2:
            body.append(arrow(x + bw + 4, y + bh / 2, x + bw + gap - 4, y + bh / 2))
    # wrap from step 3 to step 4
    x3 = 20 + 2 * (bw + gap) + bw / 2
    body.append(f'<path d="M{x3},{20 + bh + 4} V{20 + bh + 23} H{20 + bw / 2} V{20 + bh + 42}" fill="none" '
                f'stroke="{MUTED}" stroke-width="1.8" marker-end="url(#arrow-m)"/>')
    body.append(text(385, 20 + 2 * bh + 46 + 30, t["flow_note"], 12.5, 400, MUTED))
    return svg(770, 20 + 2 * bh + 46 + 44, body)


def states(t):
    s = t["states"]
    body = []
    W, H = 150, 48
    pos = {"found": (20, 40), "recurring": (210, 40), "promoted": (440, 40), "used": (630, 40),
           "blocked": (440, 190), "dormant": (20, 190), "expired": (20, 300)}
    for key, (x, y) in pos.items():
        if key == "blocked":
            fill, stroke, color = WARN_TINT, WARN, WARN
        elif key in ("promoted", "used"):
            fill, stroke, color = TINT, BRAND, BRAND
        elif key in ("dormant", "expired"):
            fill, stroke, color = GREY_TINT, LINE, MUTED
        else:
            fill, stroke, color = "#fff", LINE, INK
        body.append(box(x, y, W, H, fill=fill, stroke=stroke, r=24, width=1.8))
        body.append(text(x + W / 2, y + 30, s[key], 15, 700, color))
    body.append(arrow(172, 64, 208, 64))
    body.append(text(190, 30, s["seen_again"], 11.5, 400, MUTED))
    body.append(arrow(362, 64, 438, 64))
    body.append(text(400, 30, s["source"], 11.5, 700, BRAND))
    body.append(arrow(592, 64, 628, 64))
    body.append(text(610, 30, s["relevant"], 11.5, 400, MUTED))
    body.append(arrow(495, 90, 495, 188, WARN))
    body.append(text(487, 145, s["contradiction"], 11.5, 700, WARN, "end"))
    body.append(arrow(545, 188, 545, 90, MUTED, dash=True))
    body.append(text(553, 145, s["resolve"], 11.5, 400, MUTED, "start"))
    body.append(arrow(60, 90, 60, 188))
    body.append(text(68, 145, s["quiet"], 11.5, 400, MUTED, "start"))
    body.append(arrow(150, 188, 262, 92, MUTED, dash=True))
    body.append(text(215, 160, s["returns"], 11.5, 400, MUTED, "start"))
    body.append(arrow(95, 240, 95, 298))
    body.append(text(103, 275, s["fade"], 11.5, 400, MUTED, "start"))
    lx, ly = 440, 290
    body.append(box(lx, ly, 22, 14, fill=TINT, stroke=BRAND, r=7))
    body.append(text(lx + 30, ly + 12, s["authority"], 12, 400, INK, "start"))
    body.append(box(lx, ly + 26, 22, 14, fill="#fff", stroke=LINE, r=7))
    body.append(text(lx + 30, ly + 38, s["no_authority"], 12, 400, INK, "start"))
    return svg(800, 360, body)


def arch(t):
    a = t["arch"]
    body = []
    body.append(f'<rect x="10" y="10" width="760" height="330" rx="14" fill="{GREY_TINT}" stroke="{LINE}"/>')
    body.append(text(26, 34, a["computer"], 12.5, 700, MUTED, "start"))
    body.append(box(30, 60, 150, 70))
    body.append(text(105, 90, a["browser"], 14, 700))
    body.append(text(105, 110, a["client"], 12, 400, MUTED))
    body.append(arrow(184, 95, 226, 95))
    body.append(arrow(226, 105, 184, 105))
    body.append(box(230, 60, 160, 70))
    body.append(text(310, 90, a["api"], 14, 700))
    body.append(text(310, 110, a["api_sub"], 12, 400, MUTED))
    body.append(arrow(394, 95, 436, 95))
    body.append(box(440, 50, 310, 90))
    body.append(text(595, 84, a["core"], 14, 700))
    body.append(text(595, 106, a["core_sub"], 12, 400, MUTED))
    body.append(box(440, 170, 150, 70, fill=TINT, stroke=BRAND, width=2))
    body.append(text(515, 200, a["gate"], 14, 700, BRAND))
    body.append(text(515, 220, a["gate_sub"], 11, 400, MUTED))
    body.append(box(600, 170, 150, 70, fill=TINT, stroke=BRAND, width=2))
    body.append(text(675, 210, a["pou"], 13, 700, BRAND))
    body.append(arrow(515, 144, 515, 168))
    body.append(arrow(675, 144, 675, 168))
    body.append(box(440, 262, 310, 60))
    body.append(text(595, 288, a["store"], 14, 700))
    body.append(text(595, 308, a["store_sub"], 12, 400, MUTED))
    body.append(arrow(515, 244, 515, 260))
    body.append(box(230, 180, 160, 60))
    body.append(text(310, 215, a["models"], 14, 700))
    body.append(arrow(436, 120, 394, 195))
    body.append(box(230, 270, 160, 50, fill="#fff"))
    body.append(text(310, 300, a["ollama"], 13, 600))
    body.append(arrow(310, 244, 310, 268))
    body.append(f'<rect x="20" y="185" width="170" height="50" rx="10" fill="#fff" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    body.append(text(105, 215, a["openai"], 12.5, 600, MUTED))
    body.append(arrow(226, 210, 184, 210, MUTED, dash=True))
    return svg(780, 350, body)


out = Path(sys.argv[1])
for lang, t in T.items():
    d = out / lang
    d.mkdir(parents=True, exist_ok=True)
    (d / "diagram-flow.svg").write_text(flow(t), encoding="utf-8")
    (d / "diagram-states.svg").write_text(states(t), encoding="utf-8")
    (d / "diagram-architecture.svg").write_text(arch(t), encoding="utf-8")
print("ok")
