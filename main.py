#!/usr/bin/env python3
"""CLI for agent-design-taste: audit HTML files for AI-design-slop.

Usage:
    python3 main.py page.html             # audit a file
    python3 main.py --demo                # audit built-in good vs sloppy samples
    python3 main.py page.html --json      # machine-readable output (CI / agents)

Exit codes: 0 PASS · 1 NEEDS_WORK · 2 SLOPPY — gate any agent-generated UI
on this before it ships.
"""

from __future__ import annotations

import argparse
import json
import sys

from agent_design_taste import (
    audit_html,
    exit_code_for,
    format_report,
)

DEMO_GOOD = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>خدمات کامپیوتری سینا — تعمیر، اسمبل، نصب بازی</title>
<link rel="stylesheet" href="style.css">
<style>:root{--brand:#0d6efd;--ink:#1a1a2e;--paper:#fafafa;--gap:1.5rem;}</style>
</head>
<body>
<header><nav><a href="#services">خدمات</a><a href="#prices">قیمت‌ها</a></nav></header>
<main>
<h1>خدمات کامپیوتری سینا در اراک</h1>
<section id="services">
<h2>چه کارهایی انجام می‌دهیم</h2>
<p>تعمیر تخصصی لپ‌تاپ، اسمبل کیس گیمینگ، نصب ویندوز و بازی کنسول. ۵ سال سابقه در خیابان رودکی اراک.</p>
<button>مشاوره رایگان اسمبل</button>
</section>
<section id="prices">
<h2>قیمت‌های امروز</h2>
<p>نصب ویندوز از ۱۵۰ هزار تومان. فاکتور رسمی صادر می‌شود.</p>
<img src="shop-front.jpg" alt="نمای ورودی مغازه خدمات کامپیوتری سینا">
</section>
</main>
<footer><p>ساعت کاری ۸ تا ۹ شب · تلفن 09185790374</p></footer>
</body>
</html>
"""

DEMO_BAD = """<!DOCTYPE html>
<html>
<head>
<title>Document</title>
<style>.hero{background:linear-gradient(135deg,#667eea,#764ba2);}</style>
</head>
<body>
<div class="hero">
<h1>Welcome</h1>
<h1>Features</h1>
<p>In today's fast-paced world, our robust solution will revolutionize your workflow 🚀✨. Seamless integration guaranteed.</p>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
<button>Get Started</button><button>Learn More</button>
</div>
<div>
<h2>Features</h2><h2>Testimonials</h2><h2>FAQ</h2>
<img src="https://picsum.photos/800/400">
<img src="https://placehold.co/600x400">
</div>
<div style="color:red" style="margin:0"><p>delve into the tapestry of innovation 🎨</p></div>
</body>
</html>
"""


def _audit_source(name: str, source: str, as_json: bool) -> int:
    result = audit_html(source)
    if as_json:
        payload = {"file": name, **result.to_dict()}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report(result, name))
    return exit_code_for(result.verdict)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Design-taste gate for AI-built UIs (stdlib only)."
    )
    ap.add_argument("files", nargs="*", help="HTML files to audit")
    ap.add_argument("--demo", action="store_true", help="audit built-in good vs sloppy samples")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="machine-readable output for CI/agents")
    args = ap.parse_args(argv)

    if args.demo:
        code = 0
        code = max(code, _audit_source("demo-good.html", DEMO_GOOD, args.as_json))
        code = max(code, _audit_source("demo-bad.html", DEMO_BAD, args.as_json))
        return code

    if not args.files:
        ap.error("give HTML files or --demo")
    worst = 0
    for path in args.files:
        try:
            with open(path, encoding="utf-8") as fh:
                source = fh.read()
        except OSError as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 3
        worst = max(worst, _audit_source(path, source, args.as_json))
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
