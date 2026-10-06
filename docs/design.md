# Design System: Local Guide Booking System

This file is the single source of truth for how the app looks. It does not change the UI contract in `docs/PRD.md` section 9 (element ids, `data-testid` values, status text) — every selector listed there must still exist with the same value. This file only says how those elements should be styled, laid out and written.

Owned by work item B-08 (`docs/TASKS.md`). Do not restyle in B-02 through B-07; those items use default/unstyled HTML on purpose so the service-layer logic stays the reviewable focus of those PRs.

## 0. Why this doc exists

The brief is: a small-scale, trust-based local service marketplace used on a phone in direct sun as often as on a laptop. Two roles see almost entirely different screens (a guide's console vs a traveler's search-and-book flow), and the whole product lives or dies on one thing — making booking status (PENDING / CONFIRMED / CANCELLED) impossible to misread at a glance. That's the design problem. Everything below serves it.

Explicitly reject the generic-AI-app look: no warm-cream-plus-terracotta SaaS palette, no identical rounded cards with one grey shadow, no tracked-out ALL-CAPS eyebrows, no '→' on every button, no bento grid for its own sake. If a future pass starts resembling those defaults, that is the signal to revise, not ship.

## 1. Design plan (token system)

### 1.1 Color

Grounded in the subject: local, on-the-ground, outdoors, trust between two strangers meeting in person. Not a generic SaaS blue.

| Token | Hex | Role |
|---|---|---|
| `--color-ink` | `#1C2521` | Primary text, headings |
| `--color-paper` | `#FAF8F3` | App background (warm off-white, not stark white, not the AI-cliché cream) |
| `--color-trail` | `#2F5D4C` | Primary brand/action color — deep forest green, evokes "guide," grounded and trustworthy, not a SaaS blue or violet |
| `--color-clay` | `#B5542C` | Single accent for one deliberate emphasis point per screen (never paired with trail as a second CTA color) |
| `--color-line` | `#DDD6C8` | Borders, dividers, input outlines |
| `--color-surface` | `#FFFFFF` | Cards, inputs, elevated panels on top of paper |

Status colors (semantic, never decorative — used only on status pills and timeline dots):

| Status | Token | Hex |
|---|---|---|
| PENDING | `--status-pending` | `#9A6B13` (amber-brown, not yellow — passes contrast on paper) |
| CONFIRMED | `--status-confirmed` | `--color-trail` `#2F5D4C` |
| CANCELLED | `--status-cancelled` | `#8A4A42` (muted brick red, not alarm-red — a cancelled booking is a fact, not an error) |

Rule: status is never conveyed by color alone (ui-ux-pro-max `color-not-only`). Every status pill carries its own text (PENDING/CONFIRMED/CANCELLED) plus a distinct icon shape (circle outline / filled check / slash), so it still reads correctly for colorblind users and in the Selenium `data-testid="booking-status"` text assertion either way.

Dark mode: out of scope for v1 (not in PRD scope). Token names are semantic so it can be added later without a rewrite — do not hardcode hex values outside `:root`.

### 1.2 Type

Two families, clearly distinct roles, not a generic Inter-everywhere stack:

- **Display/headings:** `Fraunces` (serif, variable, available on Google Fonts) — has warmth and a handmade quality appropriate to a person-to-person service, at moderate weight (500–600), never the ultra-bold "AI poster" weight.
- **Body/UI:** `Inter` — for form labels, body copy, nav, buttons, table/list text. Chosen for legibility at small sizes on a phone in daylight, not as a default-and-forget choice.
- **No monospace anywhere.** There is no code or data-label content here that needs it; adding one would be the ui-ux-pro-max `icon-style-consistent`/style-selection anti-pattern of a tool used for decoration.

Type scale (base 16px, 1.25 ratio, per PRD NFR-08 and ui-ux-pro-max `typography`):

| Token | Size | Family | Use |
|---|---|---|---|
| `--text-display` | 2.0rem (32px) | Fraunces 600 | Page `<h1>` only, one per page |
| `--text-h2` | 1.5rem (24px) | Fraunces 500 | Section headings |
| `--text-h3` | 1.125rem (18px) | Inter 600 | Card titles, list item primary text |
| `--text-body` | 1rem (16px) | Inter 400 | Body copy, form inputs |
| `--text-small` | 0.875rem (14px) | Inter 400 | Meta text, timestamps, helper text |
| `--text-label` | 0.8125rem (13px) | Inter 500 | Form labels (sentence case, never uppercase) |

Line length target: under 80 characters for body copy (frontend-design guidance) — relevant on slot descriptions and booking notes.

### 1.3 Layout

- Grid: single-column content, max-width `640px`, centered, on every screen except the guide's slot table and the public slot list, which use a `960px` max-width two-column-at-desktop layout (list/filters left, map-free detail panel not included — no maps per PRD scope).
- Spacing scale: 4px base — 4, 8, 12, 16, 24, 32, 48, 64. No arbitrary values.
- Mobile-first breakpoints: base (< 640px, the primary target — see brief), `640px` tablet, `1024px` desktop. Never disable pinch-zoom (ui-ux-pro-max `viewport-meta`).
- Touch targets: all buttons and form controls minimum 44×44px with 8px+ spacing between adjacent targets (ui-ux-pro-max `touch-target-size`, `touch-spacing`) — this matters more than usual here since travelers are booking from a phone outdoors.
- Cards: used only where content is genuinely a discrete, scannable unit (a slot row, a booking row). Not used to wrap single pieces of content like a page intro or a lone form — that's the generic "everything is a card" tell.
- Radius: one scale, two values only — `--radius-sm: 6px` (inputs, pills, buttons), `--radius-md: 10px` (cards). No larger, no mixing.
- Shadow: one elevation value, used sparingly — `--shadow-card: 0 1px 2px rgba(28,37,33,0.08), 0 1px 1px rgba(28,37,33,0.04)`. Not the generic `rgba(0,0,0,.1)` soft-blur-everywhere default.

### 1.4 Principles (what makes this not-generic)

1. **Status is the hero, everywhere a booking appears.** Not a hero image, not a gradient headline — the booking status pill is the single most visually confident element on any screen that shows one. This is the one place "spend your boldness" (frontend-design) is spent.
2. **The two roles feel like two different rooms.** Guide screens (console: table-dense, compact, efficient) read differently in rhythm from Traveler screens (search-and-browse: spacious, card-based, unhurried) even though they share one token system. This is achieved through density and layout, never through a second color palette.
3. **Empty and error states have a voice, not a shrug.** Per frontend-design's writing guidance: an empty `/slots` result says what to do next, not "No results found."
4. **No numbered-sequence markers.** Nothing here is a 3-step onboarding flow, so no 01/02/03 eyebrows anywhere, including the booking timeline (which uses chronological dots, not numbers, since items can be cancelled out of a "step" order).
5. **One accent, spent once per screen.** `--color-clay` appears at most once per screen (typically the single primary CTA, e.g. "Request booking"), never as a secondary decoration alongside trail-green buttons.

### 1.5 ASCII layout sketches

Public slot list (`/slots`) — traveler's primary screen, spacious/card-based:

```
┌─────────────────────────────────────────┐
│ nav: logo   Slots  Bookings      [name ▾]│
├─────────────────────────────────────────┤
│  Find a guide                            │
│  [ city______ ]  [ date____ ]  [ Apply ] │
│                                           │
│  ┌───────────────────────────────────┐   │
│  │ Priya S. · Jaipur          ₹1,200 │   │
│  │ Old City walking tour              │   │
│  │ Sat 4 Oct, 9:00–11:00am            │   │
│  └───────────────────────────────────┘   │
│  ┌───────────────────────────────────┐   │
│  │ ... next slot-row card ...        │   │
│  └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

Guide's slot console (`/guide/slots`) — dense, table-like:

```
┌─────────────────────────────────────────┐
│ nav: logo   My slots  Bookings   [name ▾]│
├─────────────────────────────────────────┤
│  My slots                [+ New slot]    │
│  ──────────────────────────────────────  │
│  Old City tour   Sat 9:00   ● available  │
│  River walk      Sun 7:00   ◐ booked     │
│  Fort history     Mon 9:00   ○ inactive   │
└─────────────────────────────────────────┘
```

Booking detail (`/bookings/<id>`) — status is the hero:

```
┌─────────────────────────────────────────┐
│  ← Back to bookings                      │
│                                           │
│   ╭─────────────────────────────────╮    │
│   │        ✓  CONFIRMED             │    │
│   ╰─────────────────────────────────╯    │
│  Old City walking tour with Priya S.     │
│  Sat 4 Oct, 9:00–11:00am · ₹1,200        │
│                                           │
│  [ Cancel booking ]                       │
│                                           │
│  Timeline                                 │
│  ● Requested      Thu 2 Oct, 6:02pm       │
│  ● Confirmed      Thu 2 Oct, 8:15pm       │
└─────────────────────────────────────────┘
```

## 2. Per-screen spec

Every screen below must preserve every id and `data-testid` listed in PRD section 9 exactly. This section adds visual/content direction; it does not add or remove functional elements.

### 2.1 Global shell (all pages)

- Nav bar: `--color-paper` background, `--color-line` 1px bottom border, not a shadow. Logo/wordmark left, links center-right, `data-testid="nav-user"` + role badge far right when logged in.
- Flash messages (`data-testid="flash"`): a slim full-width bar directly under the nav, not a floating toast — toasts are easy to miss outdoors on mobile. `flash-success` uses `--color-trail` left border + pale trail-tint background; `flash-error` uses `--status-cancelled` left border + pale tint. Auto-dismiss never — the person must be able to re-read it.
- 403/404/500 pages (FR-18): centered, `--text-display` heading, one calm sentence explaining what happened in plain language (frontend-design: "errors don't apologize, never vague"), one link back to a sensible place (`/slots` or `/`). No stack traces, no generic "Oops!".

### 2.2 Landing (`/`)

Hero is the real content, not a stock illustration: a live-feeling preview of 2–3 upcoming slots (reuses the slot-row component) under a one-sentence value statement. Two CTAs max: "Browse guides" (trail, primary) and "Become a guide" (text link, not a competing button — only one clay accent on this page and it's not spent here).

### 2.3 Register / Login (`/register`, `/login`)

- Single centered card, max-width 420px. Not split-screen marketing layout — there's no marketing content to fill the other half honestly.
- Role picker (`#role`) on register: two large tappable segmented options (Traveler / Guide), not a plain `<select>` dropdown, since it's a consequential, unchangeable choice (PRD section 2) and deserves visual weight — but keep the underlying `<select id="role">` for form semantics/testability; style it as a custom segmented control bound to it.
- City field (`#city`) appears with a brief animated height expand only when Guide is selected — this is the one acceptable "motion answers a user's action" case (frontend-design section on motion), not decorative.
- Labels are sentence case, sit above the input, always visible (never placeholder-as-label — ui-ux-pro-max `Forms & Feedback`).

### 2.4 Browse slots (`/slots`)

- Filters (`#filter-city`, `#filter-date`, `#apply-filter`) sit in a single inline bar on desktop, stacked full-width on mobile.
- `data-testid="slot-row"` cards: guide name + city on one line (H3 weight), title below, time range and price as `--text-small` meta row. Whole card is the `data-testid="slot-link"` tap target (not just a small "View" link) — satisfies the 44px+ touch target rule on mobile.
- `data-testid="empty-state"`: not "No results." Written in-voice: explain that no guides matched these filters and suggest clearing the date or trying a nearby city. One illustration-free, text-only block — no stock empty-state graphic.

### 2.5 Slot detail (`/slots/<id>`)

- Single column, card-free (it's the primary content of the page, not a unit in a list).
- Booking form (`#note`, `#book-btn`) is visually the primary action: `#book-btn` is the one `--color-clay` moment on this page.
- If unavailable: the book form is replaced (not just disabled) by a plain-language explanation of why, consistent with the error-state voice principle.

### 2.6 Guide: new/list slots (`/guide/slots`, `/guide/slots/new`)

- List is dense and table-like (principle 2), not the spacious card treatment used for the public list — this is a working console, not a browse experience.
- `data-testid="slot-status"` renders as a small icon + word pill (● available / ◐ booked / ○ inactive / past in `--color-line`-muted text), consistent with the status-is-never-color-alone rule.
- New slot form (`#title`, `#start_at`, `#end_at`, `#price_inr`, `#submit-slot`): a single column form, real `<label>` per PRD NFR-08, inline validation message appears directly under the relevant field (ui-ux-pro-max `Forms & Feedback` — errors near field, not just a banner at top).

### 2.7 Bookings list and detail (`/bookings`, `/bookings/<id>`)

- `data-testid="booking-row"`: status pill is the first thing the eye hits — left-aligned, bold, with its icon — before guide/slot name.
- Detail page: large status pill as a standalone element near the top (see 1.5 sketch) — this is principle 1 applied directly.
- Timeline (`data-testid="timeline-item"`): vertical line with dots, not numbered steps (principle 4). Each item: relative action word (Requested / Confirmed / Cancelled), actor, and timestamp in `--text-small`.
- `#confirm-btn` uses `--color-trail` (continues the primary flow); `#cancel-btn` uses an outlined/secondary style in `--status-cancelled` — present but visually subordinate, since cancelling is available but not the page's encouraged action.

## 3. Accessibility and quality floor (non-negotiable, per PRD NFR-08 and ui-ux-pro-max priority 1–2)

- Contrast: all text/background pairs above meet 4.5:1 (verify `--status-pending` amber-brown and `--status-cancelled` brick on `--color-paper` specifically — both were chosen to pass at normal text size, confirm with a contrast checker before shipping).
- Visible focus ring on every interactive element, 2px, `--color-trail`, never removed.
- Every form input has a real `<label for="...">`, matching the ids in PRD section 9.
- `prefers-reduced-motion` disables the city-field expand animation and any future transitions.
- No icon-only buttons without an `aria-label` (nav, confirm/cancel icons if added later).
- No horizontal scroll at any breakpoint; viewport meta never disables zoom.

## 4. Explicitly out of scope for this pass

Matches PRD section 3: no payments UI, no ratings/reviews, no chat, no maps, no image upload, no multi-language, no dark mode (token-ready, not built). Do not add UI for these even as disabled/placeholder elements — PRD section 3 says do not stub them.
