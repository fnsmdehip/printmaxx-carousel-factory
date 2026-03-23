#!/usr/bin/env python3
"""
PRINTMAXX Carousel Factory (CS022-inspired, compliance-first)
=============================================================

Generates 1 carousel/day per persona into:
- CONTENT/social/carousels/ (markdown script + caption)
- output/carousels/ (HTML preview decks)

No posting. No account automation. Designed for human review + manual publishing.
"""

from __future__ import annotations

import json
import random
import re
import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent
PERSONAS_JSON = BASE_DIR / "OPS" / "PERSONAS.json"
STATE_DIR = BASE_DIR / "OPS" / "_state"
STATE_FILE = STATE_DIR / "carousel_factory.json"

OUT_CONTENT_DIR = BASE_DIR / "CONTENT" / "social" / "carousels"
OUT_PREVIEW_DIR = BASE_DIR / "output" / "carousels"


@dataclass(frozen=True)
class CarouselTemplate:
    template_id: str
    title: str
    bullets: List[str]
    cta_title: str
    cta_lines: List[str]
    caption: str
    niches: Tuple[str, ...] = ("general",)


TEMPLATES: Tuple[CarouselTemplate, ...] = (
    CarouselTemplate(
        template_id="PMX_CAR_001",
        title="5 cold email fixes that stop you looking spammy",
        bullets=[
            "Subject: 3-6 words. No hype. No emojis.",
            "1 ask per email. If you need 3 asks, write 3 emails.",
            "Lead with a real observation (not a compliment).",
            "1 proof link max (demo page or portfolio).",
            "Close with a yes/no question.",
        ],
        cta_title="Want the templates?",
        cta_lines=[
            "I keep a full pack of subject lines + bodies.",
            "Link in bio.",
        ],
        caption="Cold email is simple: observation + offer + low-friction ask. Save this.",
        niches=("general", "ai_productivity", "outbound", "cold_outreach"),
    ),
    CarouselTemplate(
        template_id="PMX_CAR_002",
        title="5 website changes that boost conversions fast",
        bullets=[
            "Put your phone number above the fold (tap-to-call).",
            "Make the primary CTA a single verb (Book, Call, Get Quote).",
            "Add 3 proof points near CTA (reviews, logos, years, stats).",
            "Cut your homepage copy in half. Keep only what earns the click.",
            "Fix mobile first. If it’s clumsy on a phone, it’s broken.",
        ],
        cta_title="If you want a before/after demo",
        cta_lines=[
            "I build fast replacement pages as examples.",
            "Link in bio.",
        ],
        caption="Most websites don’t have a traffic problem. They have a friction problem.",
        niches=("general", "ai_productivity", "local_biz"),
    ),
    CarouselTemplate(
        template_id="PMX_CAR_003",
        title="5 automations that buy you time every week",
        bullets=[
            "Auto-capture tasks: any idea -> inbox (1 tap).",
            "Auto-sort receipts into a ledger folder (daily).",
            "Auto-generate weekly review from your logs (Friday).",
            "Auto-queue drafts: content written but never shipped is wasted.",
            "Auto-backup: snapshots before you mutate data.",
        ],
        cta_title="Systems > motivation",
        cta_lines=[
            "I’m a virtual creator focused on boring-but-effective ops.",
            "Save this and build one automation today.",
        ],
        caption="If your system needs motivation, it’s not a system yet.",
        niches=("general", "ai_productivity"),
    ),
    CarouselTemplate(
        template_id="PMX_FAITH_001",
        title="5 ways to make prayer a daily habit (without willpower)",
        bullets=[
            "Pick a time anchor: right after brushing teeth.",
            "Keep it short: 3 minutes counts.",
            "Write 1 line after: what you’re grateful for.",
            "Use a trigger: before you unlock your phone.",
            "Track it: streaks are feedback, not guilt.",
        ],
        cta_title="Start small, stay consistent",
        cta_lines=[
            "No performance. Just show up.",
            "Save this and try it tomorrow.",
        ],
        caption="Consistency beats intensity. Three minutes daily will change you.",
        niches=("faith",),
    ),
    CarouselTemplate(
        template_id="PMX_FAITH_002",
        title="5 ways to stop doomscrolling at night",
        bullets=[
            "Charge your phone outside the bedroom.",
            "Set a hard cutoff: 30 minutes before sleep.",
            "Replace the habit: a page of Proverbs or a short journal.",
            "Lower friction: keep your book on the pillow.",
            "Make it visible: track nights you win.",
        ],
        cta_title="Your next morning starts tonight",
        cta_lines=[
            "Sleep is a multiplier.",
            "Save this and run it for 7 days.",
        ],
        caption="Most people don’t have a discipline problem. They have a phone-in-bed problem.",
        niches=("faith", "fitness", "ai_productivity"),
    ),
    CarouselTemplate(
        template_id="PMX_FIT_001",
        title="5 training rules that actually change your body",
        bullets=[
            "Train 3x/week. Don’t miss. That’s the whole game.",
            "Track your lifts. Add weight or reps weekly.",
            "Sleep 7+ hours. Recovery is not optional.",
            "Protein daily. Keep it simple and repeatable.",
            "Walk every day. It’s free fat loss.",
        ],
        cta_title="Consistency wins",
        cta_lines=[
            "No secret program. Just the boring basics.",
            "Save this and start Monday.",
        ],
        caption="If you can’t do it for 12 weeks, it won’t work for 12 months.",
        niches=("fitness",),
    ),
    CarouselTemplate(
        template_id="PMX_FIT_002",
        title="5 fat loss mistakes that keep you stuck",
        bullets=[
            "You’re not tracking anything, so you’re guessing.",
            "Your weekends erase your weekdays.",
            "You cut too hard and burn out in 6 days.",
            "You ‘reward’ workouts with extra food.",
            "You’re under-walking and overthinking.",
        ],
        cta_title="Make it boring",
        cta_lines=[
            "Small deficit. Daily steps. Repeat.",
            "Save this and fix one mistake today.",
        ],
        caption="Fat loss is math + patience. Pick the plan you can repeat.",
        niches=("fitness",),
    ),
)


def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "carousel"


def _load_personas() -> List[Dict[str, object]]:
    if not PERSONAS_JSON.exists():
        return []
    try:
        payload = json.loads(PERSONAS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    personas = payload.get("personas", [])
    return personas if isinstance(personas, list) else []


def _load_state() -> Dict[str, object]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {"version": 1, "last_by_persona": {}}
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.setdefault("version", 1)
            payload.setdefault("last_by_persona", {})
            return payload
    except Exception:
        pass
    return {"version": 1, "last_by_persona": {}}


def _save_state(state: Dict[str, object]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_markdown(persona: Dict[str, object], tpl: CarouselTemplate) -> str:
    pid = str(persona.get("id", "persona")).strip()
    display = str(persona.get("display_name", pid)).strip()
    disclosure = persona.get("disclosure", {}) if isinstance(persona.get("disclosure"), dict) else {}
    bio_line = str(disclosure.get("bio_line", "Virtual creator (AI).")).strip()
    periodic = str(disclosure.get("periodic_in_content_line", "")).strip()
    ctas = persona.get("cta_defaults", {}) if isinstance(persona.get("cta_defaults"), dict) else {}
    cta_primary = str(ctas.get("primary", "Link in bio.")).strip()
    cta_secondary = str(ctas.get("secondary", "Save this.")).strip()

    lines: List[str] = []
    lines.append(f"# Carousel: {tpl.title}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- persona_id: `{pid}`")
    lines.append(f"- persona: `{display}`")
    lines.append("- format: `carousel` (CS022-inspired)")
    lines.append("- platforms: `IG` / `X` (adapt)")
    lines.append("- compliance: disclosure included (AI/virtual)")
    lines.append("")
    lines.append("## Slide Plan (9:16 / 4:5 friendly)")
    lines.append("")
    lines.append("### Slide 1 (Hook)")
    lines.append(f"**{tpl.title}**")
    lines.append("")
    lines.append(f"*Small text:* {bio_line}")
    lines.append("")
    lines.append("### Slides 2-6 (Value)")
    for i, b in enumerate(tpl.bullets, 2):
        lines.append(f"**Slide {i}:** {b}")
    lines.append("")
    lines.append("### Slide 7 (CTA)")
    lines.append(f"**{tpl.cta_title}**")
    for l in tpl.cta_lines:
        lines.append(f"- {l}")
    lines.append("")
    lines.append("### Slide 8 (Disclosure)")
    lines.append("- Disclosure: This account is a virtual/AI creator.")
    lines.append("- If any post includes affiliate links or paid partnerships, disclose clearly in-content.")
    lines.append("")
    lines.append("## Caption (IG)")
    lines.append(tpl.caption)
    lines.append("")
    lines.append(f"{cta_secondary}")
    lines.append("")
    lines.append(f"{cta_primary}")
    lines.append("")
    if periodic:
        lines.append("## Optional periodic in-content disclosure")
        lines.append(periodic)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _build_preview_html(persona: Dict[str, object], tpl: CarouselTemplate) -> str:
    disclosure = persona.get("disclosure", {}) if isinstance(persona.get("disclosure"), dict) else {}
    bio_line = str(disclosure.get("bio_line", "Virtual creator (AI).")).strip()
    title = tpl.title

    slides: List[Tuple[str, List[str]]] = []
    slides.append((title, [bio_line]))
    for b in tpl.bullets:
        slides.append(("", [b]))
    slides.append((tpl.cta_title, tpl.cta_lines))
    slides.append(("Disclosure", ["Virtual/AI creator.", "Disclose affiliates/sponsorships in-content when present."]))

    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    slide_divs = []
    for idx, (h, items) in enumerate(slides, 1):
        body = "".join(f"<li>{esc(x)}</li>" for x in items)
        header = f"<div class='h'>{esc(h)}</div>" if h else ""
        slide_divs.append(
            f"<section class=\"slide\"><div class=\"num\">{idx}/{len(slides)}</div>{header}<ul>{body}</ul></section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Carousel Preview</title>
  <style>
    body {{ margin:0; padding:24px; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#0b0c10; color:#e8e8ee; }}
    .deck {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:16px; }}
    .slide {{ position:relative; background: radial-gradient(1200px 600px at 10% 10%, rgba(0,255,136,0.12), transparent 60%), #11131a; border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 16px; min-height: 360px; }}
    .num {{ position:absolute; top:12px; right:14px; font-size:12px; opacity:0.6; }}
    .h {{ font-weight:800; letter-spacing:-0.02em; font-size:18px; margin: 4px 0 10px; }}
    ul {{ margin:0; padding-left: 16px; line-height:1.45; }}
    li {{ margin: 10px 0; }}
    .note {{ margin-top: 18px; font-size: 12px; opacity:0.75; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  </style>
</head>
<body>
  <div class="deck">
    {''.join(slide_divs)}
  </div>
  <div class="note">Preview only. Export images using your preferred workflow (Remotion/Canva/etc.).</div>
</body>
</html>
"""


def tick(*, seed: int | None = None) -> int:
    personas = _load_personas()
    if not personas:
        print("carousel_factory: no personas found")
        return 0

    OUT_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    state = _load_state()
    last_by = state.get("last_by_persona", {})
    if not isinstance(last_by, dict):
        last_by = {}
        state["last_by_persona"] = last_by

    today = date.today().isoformat()
    rng = random.Random(seed)

    generated = 0
    for persona in personas:
        pid = str(persona.get("id", "")).strip()
        if not pid:
            continue
        niche = str(persona.get("niche", "general")).strip() or "general"
        last_day = str(last_by.get(pid, "")).strip()
        if last_day == today:
            continue

        candidates = [t for t in TEMPLATES if niche in t.niches or "general" in t.niches]
        tpl = rng.choice(candidates or list(TEMPLATES))
        cid = _now_id()
        slug = _slugify(f"{pid}_{tpl.template_id}_{cid}")

        md = _build_markdown(persona, tpl)
        md_path = OUT_CONTENT_DIR / f"{slug}.md"
        md_path.write_text(md, encoding="utf-8")

        html = _build_preview_html(persona, tpl)
        html_dir = OUT_PREVIEW_DIR / slug
        html_dir.mkdir(parents=True, exist_ok=True)
        (html_dir / "index.html").write_text(html, encoding="utf-8")

        last_by[pid] = today
        generated += 1

    _save_state(state)
    print(f"carousel_factory: generated={generated} (1/day/persona)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tick", action="store_true", help="Generate daily carousels where missing.")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.tick:
        return tick(seed=args.seed)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
