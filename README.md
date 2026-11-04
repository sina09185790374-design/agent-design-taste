# Agent Design Taste 🎨

Score any **AI-built HTML page** for design slop before it ships — 16 checks, 0–100 score, CI-friendly exit codes.

Born in a real workflow: coding agents now ship landing pages for small businesses (ours included), and the same 6 slop signatures keep appearing — purple hero gradients, "Get Started" buttons, emoji icons, lorem-ipsum filler, picsum images, `delve`-flavored copy. This gate catches them *before* the page is presented as done. Pattern learned from the Nov-2026 taste wave (pbakaus/impeccable — #2 on GitHub Trending — and google/elephant-goldfish-model): **taste is a steer vocabulary + a review vocabulary + an audit gate, shipped as a skill**, not more generation. Same idea as our slop-guard (which lints *captions*); this one lints the *UI*. Stdlib-only Python, no API keys, no network.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB) ![License](https://img.shields.io/badge/license-MIT-green) ![Deps](https://img.shields.io/badge/deps-stdlib%20only-brightgreen)

## The 16 checks

| Check | What it catches |
|---|---|
| `title_tag` | missing or placeholder `<title>` (Document, Untitled…) |
| `lang_attr` | `<html>` without `lang` |
| `viewport_meta` | no viewport meta — not mobile-ready |
| `heading_structure` | zero or multiple `<h1>` |
| `semantic_html` | div soup instead of header/nav/main/section/footer |
| `img_alt` | `<img>` without alt text |
| `placeholder_images` | picsum / placehold / dummyimage filler |
| `generic_gradient` | purple-indigo slop gradient signatures |
| `emoji_in_ui` | emojis as UI icons instead of SVG |
| `cliche_headings` | Features / Testimonials / FAQ (EN+FA) template headings |
| `ai_phrases` | delve, tapestry, unleash, «در دنیای امروز»… |
| `generic_buttons` | Get Started / Learn More / شروع کنید stock copy |
| `lorem` | lorem ipsum filler |
| `inline_styles` | 10+ inline `style=` attributes |
| `design_tokens` | bonus: CSS variables in use |
| `external_css` | bonus: external stylesheet linked |

## Quick start

```bash
python3 main.py page.html              # audit a file
python3 main.py --demo                 # built-in good vs sloppy samples
python3 main.py page.html --json       # machine-readable (for CI / agents)
```

Sample output:

```
agent-design-taste · demo-bad.html
Score: 42/100 — SLOPPY

❌ title_tag: placeholder title: 'Document'
❌ viewport_meta: no <meta name='viewport'> — not mobile-ready
❌ img_alt: 2/2 <img> without alt text
❌ placeholder_images: placeholder image host(s): ['https://picsum.photos/800/400']
❌ lorem: lorem ipsum filler text present
⚠️ generic_gradient: AI-slop gradient signature: ['#667eea, #764ba2']
⚠️ emoji_in_ui: 3 emoji char(s) in UI copy: 🚀✨🎨 — use SVG icons
⚠️ cliche_headings: generic section headings: ['Features', 'Testimonials', 'FAQ']
⚠️ ai_phrases: AI-giveaway phrasing: ["In today's fast-paced", 'robust solution', 'delve']
⚠️ generic_buttons: stock button copy: ['Get Started', 'Learn More'] — name the outcome
...
```

**Exit codes:** `0` PASS · `1` NEEDS_WORK · `2` SLOPPY — gate any agent-generated UI on this before it ships.

## The taste skill

Read [`TASTE.md`](TASTE.md) into the agent *before* it generates UI: the steer vocabulary (what to aim for), the review vocabulary (what to catch), and a critique prompt for design review. The audit is the enforceable half of the skill.

## Tests

```bash
python3 -m unittest discover -s tests -v   # 27 tests
```

## فارسی 🇮🇷

صفحات HTML که ایجنت‌ها می‌سازن رو قبل از تحویل از ۱۶ فیلتر «سلیقه طراحی» رد می‌کنه و نمره ۰ تا ۱۰۰ می‌ده: تگ title و lang و viewport، ساختار هدینگ‌ها، متن جایگزین تصاویر، تشخیص تصاویر placeholder (picsum و…)، گرادیان‌های کلیشه‌ای بنفشِ خروجی هوش مصنوعی، ایموجی به‌جای آیکون، هدینگ‌های قالبی (Features/نظرات مشتریان…)، عبارت‌های لو‌دهنده (delve و «در دنیای امروز»…)، متن‌های دکمه قالبی (Get Started/شروع کنید)، lorem ipsum، استایل‌های inline اضافه، و امتیاز مثبت برای design token و فایل CSS خارجی. فایل `TASTE.md` هم یه «مهارت» آماده‌ست که قبل از تولید UI به ایجنت می‌دی: واژگان سلیقه + چک‌لیست بازبینی + پرامپت نقد طراحی. فقط کتابخانه استاندارد پایتون، بدون وابستگی.

الگو از موج taste نوامبر ۲۰۲۶ (الگو، نه کد): سلیقه = واژگان هدایت + واژگان بازبینی + گیت کیفیت، به‌صورت مهارت قابل نصب.
