# WCAG 2.1 AA Accessibility & Safe-Zone Checklist (`SocialMediaShortVideo`)

| Check ID | Criterion | Implementation in `docs/index.html` & Remotion Engine | Status |
|---|---|---|---|
| `A11Y-01` | 1.4.3 Contrast (Minimum) | Dark (`#070b14` surface, `#f8fafc` text) and Light (`#f8fafc` surface, `#0f172a` text) themes exceed 4.5:1 via `--pui-*` tokens | PASS |
| `A11Y-02` | 2.1.1 Keyboard & Focus Visible | `:focus-visible` 3px cyan outline on all `.nav-pill`, `.action-btn`, `.copy-btn`, and `.step-check` controls | PASS |
| `A11Y-03` | 2.3.3 Animation from Interactions | `@media (prefers-reduced-motion: reduce)` disables smooth scroll and CSS transitions | PASS |
| `A11Y-04` | 2.5.5 Target Size (Mobile Ergonomics) | Primary `.copy-btn` touch targets enforce `min-height: 44px` (`--pui-touch-min`) | PASS |
| `A11Y-05` | 4.1.2 Name, Role, Value | Progress bar uses `role="progressbar"` with `aria-valuemin`, `aria-valuemax`, and live `aria-valuenow` updates | PASS |
