# Taste vocabulary for coding agents — steer, review, audit

A small installable skill for any agent that writes HTML/CSS. Pattern:
steer vocabulary (what to aim for) + review vocabulary (what to catch) +
an audit gate (`main.py`). Agents read this file before generating UI.

## STEER — the positive vocabulary

Prefer these. They are the design equivalent of strong hooks in a caption.

1. **Name the outcome.** Buttons and CTAs name what happens next:
   «مشاوره رایگان اسمبل» beats «شروع کنید» / "Get Started".
2. **One idea per screen.** One `<h1>`, one primary action, one message.
3. **Real numbers.** Prices, hours, counts — concrete facts signal a real business.
4. **Design tokens.** CSS variables (`--brand`, `--ink`, `--gap`) over magic hex codes.
5. **Semantic bones.** `header / nav / main / section / footer` — real landmarks, not div soup.
6. **Restraint with type.** One font family, two sizes of emphasis max.
7. **Whitespace is design.** Crowding is the cheapest form of slop.

## REVIEW — the anti-patterns (catch before shipping)

| Anti-pattern | Why it reads as AI slop |
|---|---|
| Purple/indigo hero gradient (`#667eea→#764ba2`, `from-purple-600 to-pink-500`) | the default "make it pretty" move |
| Emojis as UI icons (🚀✨🎨) | use SVG; emojis are decoration, not iconography |
| Section headings: Features / Testimonials / FAQ / Why Choose Us (ویژگی‌ها / نظرات مشتریان…) | template copy, not the business's voice |
| Lorem ipsum, picsum/placehold images | unfinished work presented as finished |
| Buttons: Get Started / Learn More / شروع کنید | stock copy that says nothing |
| `delve`, `tapestry`, `unleash`, `revolutionize`, `cutting-edge`, «در دنیای امروز» | AI-giveaway phrasing |
| No `lang`, no viewport, `<title>Document</title>` | shipping without the basics |
| `<img>` without `alt` | accessibility is part of taste |
| 10+ inline `style=` attributes | design that can't be maintained |

## AUDIT — the gate

Run `python3 main.py page.html` before the UI is presented as done.
Exit codes: `0` PASS · `1` NEEDS_WORK · `2` SLOPPY. A SLOPPY verdict means
the agent did not finish the job — rebuild, don't argue.

## Critique prompt (drop into the agent's workflow)

> Review this UI as a senior designer, not as a teammate. Flag every
> item from the REVIEW table above with a line reference. Then name the
> single highest-leverage fix. Do not praise. Do not redesign from
> scratch — taste is subtraction, not addition.
