"""agent-design-taste: design-taste gate for AI-built UIs.

Audits an HTML document against a set of anti-AI-slop design checks
(positive taste vocabulary + negative anti-patterns, shipped as a gate),
scores it 0-100, and reports PASS / NEEDS_WORK / SLOPPY.

Pattern (learned, not copied): pbakaus/impeccable — taste is a steer
vocabulary + a review vocabulary + an audit gate, packaged so an agent can
consume it; google/elephant-goldfish-model — design/review knowledge as an
installable skill. Different medium from our slop-guard (which lints
*captions*): here we lint the *UI* agents generate.

Stdlib only. No network, no API keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Check catalog
# ---------------------------------------------------------------------------

AI_PHRASES_EN = [
    "delve", "tapestry", "unleash", "revolutionize", "cutting-edge",
    "game-changer", "game changer", "seamless", "robust solution",
    "in today's fast-paced", "unlock the power", "elevate your",
    "supercharge", "harness the power",
]
AI_PHRASES_FA = [
    "در دنیای امروز", "در عصر حاضر", "با پیشرفت تکنولوژی",
]
CLICHE_HEADINGS_EN = [
    "features", "why choose us", "testimonials", "faq",
    "our services", "get in touch", "about us",
]
CLICHE_HEADINGS_FA = ["ویژگی‌ها", "چرا ما", "نظرات مشتریان", "سوالات متداول", "درباره ما"]
GENERIC_BUTTONS_EN = [
    "get started", "learn more", "sign up now", "try for free",
    "click here", "submit", "read more",
]
GENERIC_BUTTONS_FA = ["شروع کنید", "بیشتر بدانید", "همین حالا ثبت‌نام کنید", "کلیک کنید"]
PLACEHOLDER_HOSTS = [
    "picsum.photos", "placehold.co", "placeholder.com",
    "loremflickr.com", "source.unsplash.com", "dummyimage.com",
]
GRADIENT_SLOP = [
    "from-purple", "from-indigo", "from-blue-600", "to-pink",
    "to-purple", "via-purple", "135deg, #667eea", "#667eea, #764ba2",
    "linear-gradient(135deg", "#a855f7", "#6366f1",
]
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]",
    re.UNICODE,
)
PLACEHOLDER_TITLES = {"untitled", "document", "title", "new page", "صفحه جدید", "عنوان"}


@dataclass
class Finding:
    check: str
    status: str  # "pass" | "warn" | "fail"
    detail: str


@dataclass
class AuditResult:
    score: int
    verdict: str  # "PASS" | "NEEDS_WORK" | "SLOPPY"
    findings: list = field(default_factory=list)

    def to_dict(self):
        return {
            "score": self.score,
            "verdict": self.verdict,
            "findings": [
                {"check": f.check, "status": f.status, "detail": f.detail}
                for f in self.findings
            ],
        }


class _Doc(HTMLParser):
    """Collects everything the checks need in one parse."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta = []
        self.html_lang = None
        self.h1 = 0
        self.headings: list[tuple[str, str]] = []  # (tag, text)
        self._cur_heading = None
        self._cur_heading_tag = None
        self.imgs: list[dict] = []
        self.text_nodes: list[str] = []
        self._in_script_style = False
        self.inline_style_count = 0
        self.buttons: list[str] = []
        self._cur_button = None
        self.css_vars = 0
        self.semantic_tags: set[str] = set()
        self.links_external_css = 0
        self.font_links = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._in_script_style = True
        if tag == "title":
            self.in_title = True
        if tag == "html" and "lang" in a:
            self.html_lang = a["lang"].strip()
        if tag == "meta":
            self.meta.append(a)
        if tag == "img":
            self.imgs.append(a)
        if tag in ("h1", "h2", "h3", "h4"):
            if tag == "h1":
                self.h1 += 1
            self._cur_heading = []
            self._cur_heading_tag = tag
        if tag in ("a", "button"):
            self._cur_button = []
        if "style" in a:
            self.inline_style_count += 1
        if tag == "link" and "stylesheet" in (a.get("rel") or ""):
            self.links_external_css += 1
            href = a.get("href", "")
            if "fonts.googleapis" in href or "fontshare" in href:
                self.font_links += 1
        if tag in ("header", "main", "footer", "nav", "section", "article", "aside"):
            self.semantic_tags.add(tag)
        if tag == "style":
            pass  # css vars counted in handle_data below

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._in_script_style = False
        if tag == "title":
            self.in_title = False
        if self._cur_heading_tag == tag and self._cur_heading is not None:
            self.headings.append((tag, "".join(self._cur_heading).strip()))
            self._cur_heading = None
            self._cur_heading_tag = None
        if tag in ("a", "button") and self._cur_button is not None:
            self.buttons.append("".join(self._cur_button).strip())
            self._cur_button = None

    def handle_data(self, data):
        if self._in_script_style:
            # still mine <style> blocks for css variables
            self.css_vars += len(re.findall(r"--[\w-]+\s*:", data))
            return
        if self.in_title:
            self.title_parts.append(data)
            return
        if self._cur_heading is not None:
            self._cur_heading.append(data)
            return
        if self._cur_button is not None:
            self._cur_button.append(data)
            return
        self.text_nodes.append(data)


def _all_text(doc: _Doc) -> str:
    return "\n".join(doc.text_nodes)


def audit_html(source: str) -> AuditResult:
    """Run every check on an HTML string; return scored result."""
    doc = _Doc()
    doc.feed(source)
    text = _all_text(doc)
    text_low = text.lower()
    findings: list[Finding] = []
    score = 100

    def add(check, status, detail, penalty=0):
        nonlocal score
        findings.append(Finding(check, status, detail))
        score = max(0, score - penalty)

    # --- document basics ---------------------------------------------------
    title = "".join(doc.title_parts).strip()
    if not title:
        add("title_tag", "fail", "no <title> tag", 10)
    elif title.lower() in PLACEHOLDER_TITLES:
        add("title_tag", "fail", f"placeholder title: '{title}'", 10)
    elif len(title) < 8:
        add("title_tag", "warn", f"title very short ({len(title)} chars)", 4)
    else:
        add("title_tag", "pass", f"title present ({len(title)} chars)")

    if not doc.html_lang:
        add("lang_attr", "warn", "<html> has no lang attribute", 4)
    else:
        add("lang_attr", "pass", f"lang='{doc.html_lang}'")

    viewport = any(
        m.get("name", "").lower() == "viewport" for m in doc.meta
    )
    if not viewport:
        add("viewport_meta", "fail", "no <meta name='viewport'> — not mobile-ready", 10)
    else:
        add("viewport_meta", "pass", "viewport meta present")

    # --- structure ---------------------------------------------------------
    if doc.h1 == 0:
        add("heading_structure", "fail", "no <h1> found", 8)
    elif doc.h1 > 1:
        add("heading_structure", "warn", f"{doc.h1} <h1> tags (should be 1)", 4)
    else:
        add("heading_structure", "pass", "single <h1>")

    if len(doc.semantic_tags) >= 3:
        add("semantic_html", "pass", f"semantic tags: {sorted(doc.semantic_tags)}")
    elif doc.semantic_tags:
        add("semantic_html", "warn", f"only {sorted(doc.semantic_tags)} semantic tags", 3)
    else:
        add("semantic_html", "warn", "no semantic tags (header/main/nav/section…)", 5)

    # --- images -------------------------------------------------------------
    bad_alt = [i for i in doc.imgs if not (i.get("alt") or "").strip()]
    if doc.imgs and bad_alt:
        add("img_alt", "fail", f"{len(bad_alt)}/{len(doc.imgs)} <img> without alt text", 8)
    elif doc.imgs:
        add("img_alt", "pass", f"{len(doc.imgs)} images all have alt text")
    else:
        add("img_alt", "pass", "no images")

    ph_hits = []
    for i in doc.imgs:
        src = (i.get("src") or "").lower()
        for host in PLACEHOLDER_HOSTS:
            if host in src:
                ph_hits.append(src)
                break
    if ph_hits:
        add("placeholder_images", "fail", f"placeholder image host(s): {ph_hits[:3]}", 8)
    else:
        add("placeholder_images", "pass", "no placeholder image hosts")

    # --- taste / anti-slop ---------------------------------------------------
    grad_hits = [g for g in GRADIENT_SLOP if g.lower() in source.lower()]
    if grad_hits:
        add("generic_gradient", "warn", f"AI-slop gradient signature: {grad_hits[:2]}", 5)
    else:
        add("generic_gradient", "pass", "no slop-gradient signature")

    emojis = set(EMOJI_RE.findall(text))
    if emojis:
        shown = "".join(sorted(emojis)[:6])
        add("emoji_in_ui", "warn", f"{len(emojis)} emoji char(s) in UI copy: {shown} — use SVG icons", 5)
    else:
        add("emoji_in_ui", "pass", "no emojis in UI copy")

    cliche = []
    for tag, h in doc.headings:
        hl = h.lower()
        if hl in CLICHE_HEADINGS_EN or h in CLICHE_HEADINGS_FA:
            cliche.append(h)
    if cliche:
        add("cliche_headings", "warn", f"generic section headings: {cliche[:3]}", 5)
    else:
        add("cliche_headings", "pass", "no cliché section headings")

    ai_hits = [p for p in AI_PHRASES_EN + AI_PHRASES_FA if p.lower() in text_low]
    if ai_hits:
        add("ai_phrases", "warn", f"AI-giveaway phrasing: {ai_hits[:3]}", 6)
    else:
        add("ai_phrases", "pass", "no AI-giveaway phrasing")

    gb_hits = []
    for b in doc.buttons:
        bl = b.lower()
        for g in GENERIC_BUTTONS_EN + GENERIC_BUTTONS_FA:
            if bl == g.lower():
                gb_hits.append(b)
                break
    if gb_hits:
        add("generic_buttons", "warn", f"stock button copy: {gb_hits[:3]} — name the outcome", 5)
    else:
        add("generic_buttons", "pass", "button copy is specific")

    if "lorem" in text_low:
        add("lorem", "fail", "lorem ipsum filler text present", 8)
    else:
        add("lorem", "pass", "no lorem ipsum")

    if doc.inline_style_count > 10:
        add("inline_styles", "warn", f"{doc.inline_style_count} inline style= attributes — move to CSS", 4)
    else:
        add("inline_styles", "pass", f"{doc.inline_style_count} inline styles (ok)")

    # --- positive taste signals (bonus vocabulary) ---------------------------
    if doc.css_vars >= 3:
        add("design_tokens", "pass", f"{doc.css_vars} CSS variables — design tokens in use")
    else:
        add("design_tokens", "warn", "no CSS variables — consider design tokens", 2)

    if doc.links_external_css > 0 or doc.font_links > 0:
        add("external_css", "pass", "external stylesheet linked")
    else:
        add("external_css", "warn", "no external stylesheet", 2)

    verdict = "PASS" if score >= 80 else ("NEEDS_WORK" if score >= 60 else "SLOPPY")
    return AuditResult(score=score, verdict=verdict, findings=findings)


def exit_code_for(verdict: str) -> int:
    return {"PASS": 0, "NEEDS_WORK": 1, "SLOPPY": 2}[verdict]


def format_report(result: AuditResult, name: str = "<input>") -> str:
    lines = [f"agent-design-taste · {name}", f"Score: {result.score}/100 — {result.verdict}", ""]
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
    for f in result.findings:
        lines.append(f"{icon[f.status]} {f.check}: {f.detail}")
    return "\n".join(lines)
