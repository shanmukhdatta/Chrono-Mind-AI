# ChronoMind V2 — Minimal UI design notes

## Goal

A quiet, accessible planning workspace, not an animation-heavy marketing dashboard. The core V2 pages keep their existing API-backed behavior while the shared product shell, typography, palette, buttons and landing page have been redesigned. The `/demo` public route uses static **labeled sample data**, not fabricated backend results.

## Current implementation

- React / Tailwind CSS, with one shared `AppShell` for V2 navigation.
- Palette: `#F8FAFC` page background, white cards, `#0F172A` primary ink, `#475569` secondary text, `#2563EB` action accent.
- Navigation grouped as Workspace, Tools and Settings. Active links are visually distinguished without animated transitions.
- Focus-visible outlines, skip links, mobile menu with Escape close, readable button targets, and static presentation by design.
- Shared CSS removes decorative animations even on older pages; individual business screens retain their functional forms and state management.
- Landing is static rather than scroll-animated. Sample preview is separate from real authenticated V2 data.

## Important boundary

This change updates the **global product visual system** and key navigation/entry screens. It is not a claim that every individual V2 page component was rebuilt from scratch or that a manual WCAG audit was completed. The next acceptance step is manual desktop/mobile keyboard and screen-reader testing.

## Local review

1. Visit `/demo` without Firebase credentials and verify that no API request is presented as a saved record.
2. With a Firebase test login and local PostgreSQL, navigate every V2 route, use forms, approve/reject plans and verify persistence after reload.
3. Check narrow width, keyboard Tab/Shift+Tab and Escape on the menu; check visible errors and labels.
4. Run frontend tests and production build; avoid adding motion-only dependencies without a documented accessibility rationale.
