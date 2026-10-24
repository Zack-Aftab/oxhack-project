# Triage — Design System ("Soft glass")

Single source of truth for the visual language of the Triage app. The patient mobile prototype (`PhoneC.dc.html`) is the reference implementation; the hospital desktop app must use the same tokens, type, materials and motion so both feel like one product.

Placeholder names: the product is called "Triage" and the wordmark is a black rounded square with a white plus and a blue dot. Replace when a real name exists.

---

## 1. Principles

1. **Time is the hero.** The biggest number on any screen is a duration or a clock time. Everything else is secondary.
2. **Calm, not clinical-cold.** Light grey ground, black ink, one blue. No gradients as decoration, no illustration, no emoji.
3. **Glass is a material, not a theme.** Frosted surfaces only for things that float over content: pills, controls, docks, overlays, toasts. Content cards may be glass; backgrounds and large areas never are.
4. **Never colour alone.** Every colour signal is paired with a word (e.g. "Moderate · needs imaging", "Recommended").
5. **Red means 999.** Red appears only on emergency surfaces (call-999 flows) and destructive actions (Cancel). Severity uses yellow → orange → deep orange, never red.
6. **Estimates, not diagnoses.** Any inferred clinical statement carries the qualifier "estimate, not a diagnosis" or "approximate".

---

## 2. Colour tokens

### Core
| Token | Value | Use |
|---|---|---|
| `--ink` | `#0B0B0C` | Primary text, filled buttons, "now" markers, chart emphasis |
| `--ink-2` | `#3A3A3F` | Body copy on light surfaces |
| `--muted` | `#6E6E73` | Secondary text, labels |
| `--muted-2` | `#8A8A90` | Tertiary text, eyebrow labels, two-tone headline lead-in |
| `--hairline` | `#D9D9DE` | Dividers, rail lines, slider thumb outline companions |
| `--hairline-2` | `#C9C9CE` | Dashed borders (unavailable / demo controls) |
| `--chevron` | `#B5B5BA` | Disclosure chevrons, "/10" denominators |
| `--dot-off` | `#E2E2E6` | Empty dot-matrix cells, inactive track |
| `--dot-past` | `#A3A3A9` | Past-time chart columns |
| `--ground` | `#F2F2F4` | Page background |
| `--ground-tint` | `#E2EBF8` | Radial tint at top of ground (`radial-gradient(90% 40% at 50% 0%, #E2EBF8 0%, transparent 70%)`) |
| `--surface` | `#FFFFFF` | Solid white insets inside glass cards |

### Accent
| Token | Value | Use |
|---|---|---|
| `--accent` | `#005EB8` | Links, selected state, wait segment of journey bar, "when you arrive" marker, recommended badge, success ticks |
| `--accent-soft` | `#7FAEE0` | Predicted/future chart columns, secondary bar segments, busyness bars |
| `--accent-rgb` | `0,94,184` | For rgba() tints: `rgba(0,94,184,.06)` row selection, `.12` glass button ring, `.16` phrase highlight, `.45–.55` glows |

### Severity (never red)
| Token | Value | Label |
|---|---|---|
| `--sev-1` | `#E9B949` | Minor |
| `--sev-2` | `#F28C28` | Moderate · needs imaging or assessment |
| `--sev-3` | `#D9661F` | Needs seeing soon |
| `--sev-2-bg` | `#FDEBD9` | Chip background for Moderate |
| `--sev-2-fg` | `#8A4410` | Chip text for Moderate |

### Emergency (999 surfaces only)
| Token | Value | Use |
|---|---|---|
| `--emergency` | `#D12E2E` | Call-999 button, flagged phrases, status dot |
| `--emergency-text` | `#B3261E` | Status line text |
| Wash | `radial-gradient(120% 55% at 50% 0%, rgba(209,46,46,.34), rgba(209,46,46,.14) 40%, transparent 62%)` | Top-of-screen wash, breathing (`edgeC` 2.6s) |

### X-ray window (dark inset)
| Token | Value |
|---|---|
| `--xray-bg` | `radial-gradient(110% 80% at 45% 50%, #14181E 0%, #06080B 75%)` |
| `--xray-bone` | `#EEF2F6` at 50–85% opacity, with a 2.2px blurred duplicate at 55% for glow |
| Scan lines | `repeating-linear-gradient(to bottom, rgba(255,255,255,.035) 0 1px, transparent 1px 3px)` |
| Grain | SVG `feTurbulence` fractalNoise, baseFrequency .9, alpha .18, layer opacity .5 |

---

## 3. Typography

Font: **Inter** (Google Fonts, weights 400/500/600/700/800). Fallback `system-ui, sans-serif`. Global `letter-spacing: -0.01em`, `-webkit-font-smoothing: antialiased`. Durations and clock times always `font-variant-numeric: tabular-nums`.

| Role | Size / line | Weight | Tracking | Notes |
|---|---|---|---|---|
| Display (mobile) | 40 / 44 | 700 | -.035em | Two-tone: first line `--muted-2`, second `--ink` |
| Display (desktop) | 48 / 52 | 700 | -.035em | Same two-tone rule |
| H1 | 34 / 38 | 700 | -.035em | Screen titles |
| H2 | 30 / 34 | 700 | -.035em | Hospital name over hero |
| Hero number (large) | 40–48 / 1 | 700–800 | -.04em | Or dot-matrix numerals (see §6) |
| Hero number (small) | 26 / 26 | 700 | -.03em | Secondary list rows |
| Clock time | 22 / 1 | 700 | -.03em | Journey tile |
| Card title | 19 / 24 | 700 | -.02em | |
| Row value | 16 / 22 | 600 | | |
| Body | 15 / 21 | 500 | | `color: --muted` for supporting copy |
| Body quote | 17 / 26 | 500 | -.01em | Patient's own words |
| Caption | 12.5–13 / 17 | 500 | | |
| Small caption | 11.5–12 / 16 | 500–600 | | |
| Eyebrow | 11 / 1 | 600 | .04–.06em | UPPERCASE, `--muted-2` |
| Axis label | 9.5 / 1 | 600 | | Chart axes |

Desktop scales: keep mobile sizes for body/captions; scale display and hero numbers up one step. Max line length for body copy ~65ch.

---

## 4. Spacing, radius, elevation

**Spacing scale (px):** 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 32, 40. Mobile page gutter 20. Desktop page gutter 32, column gap 24, card padding 20.

**Radius:**
| Token | px | Use |
|---|---|---|
| `--r-pill` | 999 | Buttons, chips, pills, dock |
| `--r-card-lg` | 26 | Primary glass cards |
| `--r-card` | 22–24 | Standard glass cards |
| `--r-inset` | 16 | White insets, chart frames, X-ray window, selected rows |
| `--r-tile` | 14–16 | Demo-control box, small tiles |
| `--r-badge` | 10 | App mark |

**Elevation (shadows):**
| Token | Value |
|---|---|
| `--shadow-glass` | `0 1px 0 rgba(255,255,255,.9) inset, 0 8px 24px rgba(20,30,50,.06)` |
| `--shadow-glass-lg` | `0 1px 0 rgba(255,255,255,.9) inset, 0 16px 40px rgba(20,30,50,.1)` |
| `--shadow-dock` | `0 1px 0 rgba(255,255,255,.9) inset, 0 14px 36px rgba(20,30,50,.1)` |
| `--shadow-button` | `0 12px 30px rgba(0,0,0,.2)` |
| `--shadow-mic` | `0 10px 28px rgba(0,0,0,.25), 0 0 0 6px rgba(0,94,184,.12)` |
| `--glow-accent` | `0 0 14–18px rgba(0,94,184,.45–.55)` (wait bar, blue action circle) |
| `--shadow-white-inset` | `0 2px 8px rgba(0,0,0,.06)` |

---

## 5. Materials

### Glass (default surface for cards and controls)
```css
background: rgba(255,255,255,.62);
backdrop-filter: blur(24px);          /* add saturate(160%) on primary cards */
-webkit-backdrop-filter: blur(24px);
border: 1px solid rgba(255,255,255,.85);
box-shadow: var(--shadow-glass);
```
Primary/recommended cards use `rgba(255,255,255,.72)`, `saturate(160%)`, border `.9`, `--shadow-glass-lg`. Overlays on photos use `.7` with `blur(12px)`.

### Ink (primary action)
`background: --ink; color: #fff; border-radius: pill; height 60 (mobile) / 48 (desktop)`. Trailing 44px blue circle (`--accent`, `--glow-accent`) holding the arrow/tick icon; label left-aligned with 24px padding.

### White inset
`background: #fff; border-radius: 16; box-shadow: --shadow-white-inset`. Used inside glass cards for comparisons (wait now → when you arrive) and the pain face.

### Dark inset (X-ray window)
See §2. Only for imaging-style graphics. Never for general dark-mode surfaces.

### Fade mask
Bottom docks sit on `linear-gradient(to top, --ground 50–55%, transparent)` so scrolling content fades behind the CTA.

---

## 6. Components

### App header
Height 40 content, top padding 58 on mobile (status bar), 10 bottom. Left: 30×30 mark (`--ink`, radius 10, white plus 16px stroke 2.6, blue 10px dot at top-right with 2px `--ground` border) + "Triage" 15/700. No right-side controls on patient; desktop adds nav/profile on the right.

### Buttons
- **Primary**: Ink material. Active: `scale(.98)`.
- **Glass pill**: 36–44 high, 13–13.5/600, glass material, icon 12–14px leading.
- **Round glass icon button**: 40×40 (back), 56×56 (dock secondary), icon 18–22 stroke 1.5–2.2.
- **Mic**: 80×80 `--ink` circle, `--shadow-mic`, white mic glyph 32, 1.5px blue ring animating `pulseC`.
- **Text link**: 13/600 `--accent`, min-height 32, no underline.
- **Emergency**: `--emergency` pill, 66 high, 19/700, white 44px trailing circle with red phone glyph, two ripple rings (`rippleC`).
- **Destructive**: glass pill with `--emergency` text.

### Chips / tags
Height 30–36, pill, 13–14/600. Variants: white with `--hairline` border (needs: X-ray, Fracture assessment); severity chip (`--sev-2-bg`/`--sev-2-fg` with 8px dot); recommended badge (`--accent` fill, white, tick, `--glow-accent`).

### Segmented travel modes
Glass pills 44 high with icon 18, label 13/600 and sub-label 10.5. Active: `--ink` fill, white text, sub-label `rgba(255,255,255,.7)`. Disabled: opacity .5, sub-label is the reason ("Not advised").

### Journey bar
Height 12 (primary) / 8 (secondary), 3px gap, pill ends. Travel segment `--ink`; wait segment `--accent` + `--glow-accent` (primary) or `--accent-soft` (secondary). All bars on one screen share a scale (width = minutes / max total). Labels under each segment: bold minutes + "drive/bus/walk" / "wait". Enter with `growC` (scaleX from left), staggered .15s.

### Wait comparison
White inset, two columns: "Wait now" (`--muted-2` eyebrow, 16/600 value) → arrow (`--chevron`) → "When you arrive · 18:20" (`--accent` eyebrow, 16/700 `--accent` value, delta in 11/600 `--muted`).

### Journey tile (leave / arrive / seen)
Grid `1fr 1px 1fr 1px 1fr`, 1px `--hairline` dividers. Each column: 16px line icon (home-with-arrow, hospital building, stethoscope in `--accent`), clock 22/700 tabular. Below: dashed `--ink` line for travel, 8px `--accent` glow bar for wait, 12px stops; a 28px white disc with the mode icon travels along the dashed segment (`driveC`, 3s alternate). Labels row: bold title + `--muted` detail.

### Dot-matrix numerals
3×5 grid per digit, 7px dots, 3px gap, 5px between digits. On = `--ink`, off = `--dot-off`. Count up over 700ms with cubic ease-out. Use for the single hero duration on a screen; elsewhere use Inter.

### Dot-matrix chart (expected queue)
13 columns (15-min slots), 8 rows of 7px dots, 3–4px gaps. Past = `--dot-past`, now = `--ink`, future = `--accent-soft`, arrival column = `--accent`. Axis labels every 4th column. Legend row of 7px dots + 11.5/500 labels.

### Busyness bar chart
16 rounded bars (pill radius), 5px gap, heights 8–60px, baseline 1px `--hairline`. Bars `--accent-soft`, current hour `--ink`. Header: title 15/700 + right note 11.5/500. "Live:" line with 10px `--ink` dot and 1.5px pulsing ring (`pulseC`). Enter with `riseC` (scaleY from bottom).

### Intake record (triage note)
Glass card; rows are full-width buttons with a 22px left rail: 18px `--ink` tick circle (white 3.2-stroke tick, `tickC` staggered .3s) joined by a 1px `--hairline` line. Row: eyebrow (11/600 .04em uppercase `--muted-2`), value 16/600, support 12.5/500 `--muted`, optional "From “phrase”" 12/500 `--accent`. The last row's tick is `--accent`. Rows write in with `writeC` staggered .3s.

### Source-phrase highlighting
In the transcript, each phrase that produced a field is a `<mark>`: `text-decoration: underline; text-decoration-color: --accent; thickness 1.5px; underline-offset 4px; radius 4px; padding 1px 2px`. Selected field's phrase gets `background: rgba(0,94,184,.16)`. On 999 screens the same style with `--emergency` and `rgba(209,46,46,.12)`.

### Pain slider (Wong-Baker)
Track 8px, gradient `--sev-1 → --sev-2 55% → --sev-3`. Thumb 20px white, 2.5px `--ink` border. 44px white disc above the thumb holds a 36px line-drawn face (1.5 stroke, circle `--chevron`): mouth `M -8 5 Q 0 (5 + k) 8 5` where `k = 6 − (pain−1)×1.4`; brows tilt inward by `max(0,(pain−4)×.8)`; eyes shrink to r .9 at ≥9. Descriptor text per band: 1–2 Barely noticeable · 3–4 Noticeable but manageable · 5–6 Hard to ignore · 7–8 Hard to think about anything else · 9–10 Unbearable. Ten invisible 40px tap zones.

### Severity scale
Three 28×4 pills (`--sev-1/2/3`), active one ringed `0 0 0 2px #fff, 0 0 0 3px --sev-2`, legend "Minor · Moderate · See soon" 10.5/500.

### X-ray window
Height 124, radius 16, `--xray-bg`. Bones (radius, ulna, four carpal blocks, five metacarpals, phalanges with a 2-bone angled thumb) as `--xray-bone` shapes + blurred duplicate. Orange radial glow (`--sev-2` .55→0) and a pulsing 1.2px ellipse over the wrist only. Grain + scan lines on top. Caption below: "Right wrist · approximate area" (11.5/500 `--muted`) and "Tap to change" (`--accent` 600). No fracture line, no labels inside.

### Voice listening state
170px stage: outer glass ring (`rgba(255,255,255,.35)`, 1px white border, `--shadow-glass-lg`), blurred conic orb (`#D9E8FA → --accent 25% → #9CC3EE 50% → #fff 70% → --accent`, blur 16, opacity .8, `orbC` 9s rotate), 96px core (`radial-gradient` white→blue tint, `coreC` 3.6s breathe), blue halo (`breatheC`). Below: 56px travelling sine wave (`--accent` 2px over `--chevron` 1.5px, `waveX` 2.6s linear, amplitude `ampC` 3.6s), edge-faded. "Listening" 14/600 with 8px `--accent` dot (`blinkC`).

### Dock
Glass pill, 10px padding, 14px gap: [56 round "Aa"] [80 mic] [56 round camera]. Labels row 11/500 `--muted-2`: Type · Tap to finish · Photo.

### Toast (live update)
Glass `.78`, radius 22, 36px `--accent` glowing circle with arrow icon, title 14/700, detail 12/500 `--muted`, 30px dismiss. Enters `dropC` from top.

### Unavailable row
Dashed 1px `--hairline-2` border, radius 20, `--muted` text, reason in 12/500 ("Can't treat this · no X-ray on site").

### Safety line
Always visible on the first screen: 6px `--emergency` dot + "Emergency? **Call 999**. Unsure? **NHS 111**." 12.5/500 `--muted`, bold links in `--ink`.

### Demo control
Dashed `--hairline-2` box, radius 14, "Demo control" 12/700 `--muted` + description, iOS-style 46×28 switch.

---

## 7. Motion

| Name | Keyframes | Duration / easing | Use |
|---|---|---|---|
| `popC` | opacity 0→1, translateY 10→0 | .4–.45s ease-out, stagger .05–.08s | Card/section entry |
| `writeC` | opacity 0→1, translateX −6→0 | .4s ease-out, stagger .3s | Intake rows |
| `tickC` | scale .3→1.2→1 | .4–.5s ease-out | Ticks, success |
| `growC` | scaleX 0→1 (origin left) | .6s cubic-bezier(.2,.7,.2,1) | Bars |
| `riseC` | scaleY 0→1 (origin bottom) | .5s cubic-bezier(.2,.7,.2,1) | Column charts |
| `dropC` | opacity 0→1, translateY −16→0, scale .97→1 | .45s cubic-bezier(.2,.8,.2,1) | Toast |
| `pulseC` | scale 1→1.7, opacity .6→0 | 1.6–2.2s ease-out ∞ | Live dots, mic ring |
| `pulseO` | scale .8→2.1, opacity .7→0 | 1.8–2s ease-out ∞ | Severity pulse on graphics |
| `blinkC` | opacity 1→.25→1 | 1.4s ∞ | Listening dot |
| `orbC` / `coreC` / `breatheC` / `ampC` | rotate+scale / scale 1→1.06 / scale+opacity / scaleY .7→1.05 | 9s linear / 3.6s ease-in-out ∞ | Voice orb and wave |
| `waveX` | translateX 0→−160px | 2.6s linear ∞ | Wave travel |
| `driveC` | left 0→27% | 3s cubic-bezier(.4,0,.2,1) alternate ∞ | Journey marker |
| `rippleC` | scale 1→1.18, opacity .55→0 | 2.2s ease-out ∞, second ring offset 1.1s | 999 button |
| `edgeC` | opacity .55→1→.55 | 2.6s ease-in-out ∞ | 999 red wash breathing |
| `flashX` | background accent tint → transparent | 1.6s ease-out | Value changed (seen time) |

Count-up numbers: 700ms, `1 − (1−p)³`. Honour `prefers-reduced-motion`: all infinite animations become static (`[data-motion]{animation:none}`), entry animations may remain.

---

## 8. Iconography
Line icons, 24 viewBox, stroke 1.5–2.2 (1.5 for refined controls, 2.2–2.6 for ticks and small glyphs), round caps and joins, `currentColor`. Sizes 12 / 14 / 16 / 18 / 22. No filled icon sets, no icon-in-circle tiles as a grid pattern (circles are reserved for action buttons and ticks).

---

## 9. Accessibility
- Touch targets ≥ 44px; desktop click targets ≥ 32px.
- Body text ≥ 4.5:1 on its surface; `--muted` on `--ground`/glass passes; never use `--chevron` for text other than denominators.
- Colour always paired with a word (badge text, severity label, legend).
- Red only for emergency and destructive.
- Numbers tabular; times in 24h `HH:MM`; durations as "55 min".

---

## 10. Desktop (hospital view) guidance
- Same tokens, same glass/ink materials, Inter. Ground stays `--ground` with the top radial tint; max content width 1440, 12-column grid, 24px gutters.
- Header becomes a 64px glass bar: mark + "Triage" left, hospital name centre, status ("Simulated data" tag, live dot) and profile right.
- Hero numbers remain the dominant element in each card (incoming patients, current wait, predicted wait at +30/+60).
- Reuse the dot-matrix chart for predicted queue, the busyness bar chart for the day view, the journey bar for per-patient ETA, and the intake record for each inbound patient's triage note (Where / What / How bad / How it happened / Likely need) with the X-ray window where imaging is implied.
- Inbound patient cards use the recommended-card pattern: 26 radius glass, eyebrow status, name, hero ETA, journey bar, wait comparison.
- Tables: 48px rows, 1px `--hairline` dividers, no zebra, numbers right-aligned tabular; row hover `rgba(0,94,184,.06)`.
- Emergency (999-flagged) items use the same restrained red rules: red wash only inside the flagged card's header area, red text only on the status line.
