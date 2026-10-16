---
name: Mission-Critical Financial Forensics
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#ffb3ad'
  on-secondary: '#68000a'
  secondary-container: '#a40217'
  on-secondary-container: '#ffaea8'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#ffdad7'
  secondary-fixed-dim: '#ffb3ad'
  on-secondary-fixed: '#410004'
  on-secondary-fixed-variant: '#930013'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 1.375rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: '600'
    lineHeight: 1.375rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-md:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.25rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.125rem
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: -0.01em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.04em
  data-metric:
    fontFamily: JetBrains Mono
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.03em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-mobile: 0.5rem
  margin: 1rem
  margin-mobile: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes a high-precision, mission-critical interface engineered for senior anti-money laundering (AML) investigators, forensic analysts, and compliance directors. The aesthetic balances analytical rigor with enterprise ergonomics: quiet, deep surfaces reduce retinal fatigue across 10-hour analytical shifts, while razor-sharp structural dividers and deliberate status signals guide rapid threat identification.

The style operates at the intersection of **technical minimalism** and **analytical modernism**. It eschews decorative whimsy, heavy skeuomorphism, and distracting ambient glow in favor of structured modularity, surgical visual hierarchy, and instant cognitive triage. The design commands authority, audit-ready defensibility, and quiet confidence—positioning evidence, temporal trails, and transaction networks at the absolute center of focus.

## Colors

The palette employs a deep-slate dark mode architecture engineered for sustained focus, exceptional contrast ratios (WCAG AAA for primary data), and strict status discrimination.

### Palette Hierarchy & Roles
- **Canvas Base & Tiers**: Background canvas anchored at deep navy (`#0B1120`), stepping to panel surfaces (`#0F172A`), container modules (`#131E32`), and elevated overlays/tooltips (`#1E293B`).
- **Interactive Blue (`#3B82F6` / `#2563EB`)**: Exclusively reserved for interactive controls, selected table rows, active tabs, primary actions, and confirmed user focus states.
- **Risk Severity Spectrum**:
  - *Critical / High Risk*: Crimson red (`#EF4444`, dark fill `#450A0A`, border `#991B1B`). Reserved for flagged sanctions, shell corporation rings, and transaction bursts.
  - *Medium Risk / Warning*: Alert amber (`#F59E0B`, dark fill `#451A03`, border `#B45309`). Applied to structurer heuristics and velocity spikes.
  - *Low Risk / Clean*: Emerald green (`#10B981`, dark fill `#064E3B`, border `#047857`). Used for cleared entities, confirmed KYC verifications, and verified ledgers.
- **Structural Outlines**: Crisp boundary definitions (`#1E293B` for low-prominence separations, `#334155` for active panel divisions, `#475569` for hover boundaries). Never blur or feather partition lines.

## Typography

Typography is strictly decoupled into semantic roles:
- **Inter** governs interface comprehension, hierarchical labels, context summaries, and analytical reports. It provides clean geometric proportions, distinct letterforms, and high legibility at micro scales.
- **JetBrains Mono** governs all quantitative, temporal, and forensic data: transaction hashes, monetary balances, SWIFT/BIC codes, timestamps, risk scores, and IP/device addresses. Tabular alignment prevents layout shifting during dynamic stream updates and maintains vertical scanning accuracy across data tables.

All uppercase analytical tags (`label-sm`, `label-md`) use tabular numbers with subtle letter spacing to prevent visual crowding in dense evidence sidebars.

## Layout & Spacing

The layout is built as a mission-control command workstation utilizing a dense, paneled CSS Grid / Flexbox architecture. Instead of generic marketing whitespace, every square rem optimizes vertical scanability and lateral comparisons across case dossiers.

### Layout Model
- **Workbench Canvas**: Fixed 100vh viewport application shell with zero global body scrolling. Individual panels contain distinct virtualized scroll regions.
- **Three-Tier Multi-Split Layout**:
  - Left Panel (260px–320px): Global navigation, active case lists, live triage streams.
  - Center Canvas (Variable / Flex-1): Interactive graph visualizer, chronological timeline, or dense evidence matrix.
  - Right Panel (340px–420px): Target dossier, risk breakdown, entity relationship graph controls, audit trail log.
- **Responsive Adaptations**:
  - *Large Workstation (≥1600px)*: Full 3-panel split view unlocked simultaneously.
  - *Desktop (1200px–1599px)*: Right inspector collapses into a sliding contextual drawer over the center stage.
  - *Compact/Tablet (≤1199px)*: Switch to tabbed workstation modes (Queue / Graph / Dossier).

## Elevation & Depth

Visual hierarchy does not rely on soft, floating drop shadows or blurred atmospheric lights. Depth is achieved entirely through **tonal layering** paired with **crisp, low-contrast 1px boundaries**.

### Layering Architecture
- **Layer 0 (Canvas Base - `#0B1120`)**: Deep structural frame, window header bars, background behind active panels.
- **Layer 1 (Surface Panels - `#0F172A`)**: Base workspace areas, pinned data tables, graph background zones. Framed by 1px solid borders in `#1E293B`.
- **Layer 2 (Embedded Containers - `#131E32`)**: Card units, summary tiles, metric scorecards, table header bands. Bordered by 1px solid `#334155`.
- **Layer 3 (Overlays & Menus - `#1E293B`)**: Contextual popovers, investigation dropdown menus, node inspect tooltips, floating graph control bars. Framed with 1px solid `#475569` and a tight technical shadow: `0 4px 12px rgba(0, 0, 0, 0.45)`.

This mechanical depth preserves high information contrast and prevents visually distracting bleed when dense data tables intersect with graph visualization canvases.

## Shapes

The design system enforces a compact shape language with subtle corner smoothing (`roundedness: 1` = `0.25rem` / `4px`). This maintains maximum usable surface area within high-density grids and reinforces an intentional, instrumentation-grade feel.

- **Micro Controls & Badges**: 2px corner radius for status pills, risk chips, and metric tags.
- **Inputs & Buttons**: 4px (`0.25rem`) corner radius.
- **Panels & Dossier Cards**: 4px–6px maximum corner radius; never pill-shaped.
- **Circular Indicators**: Full circles (`rounded-full`) are strictly preserved for status pings, entity avatar nodes on network graphs, and radio selectors.

## Components

### Buttons
- **Primary Action**: Solid interactive blue (`#2563EB`), hover `#3B82F6`, active `#1D4ED8`. Font: Inter 13px Semi-bold. Padding: 6px 12px. Border radius: 4px. No drop shadows.
- **Secondary / Panel Control**: Surface container `#1E293B`, 1px solid border `#334155`, text `#E2E8F0`. Hover: background `#334155`, border `#475569`.
- **Destructive / Flag Action**: Base dark fill `#450A0A`, 1px solid border `#DC2626`, text `#FCA5A5`. Hover: background `#7F1D1D`, text `#FFFFFF`.
- **Ghost Action**: Transparent background, text `#94A3B8`. Hover: background `#1E293B`, text `#F8FAFC`.

### Data Tables & Cell Density
- Column headers: JetBrains Mono 11px uppercase, tracking `0.05em`, background `#0F172A`, bottom border 1px solid `#334155`, text `#64748B`.
- Row height: Fixed 32px or 36px (compact workstation density). Alternating rows: base `#0F172A` and `#0D1527`.
- Hover row state: Background `#1E293B`, active selection highlighted with a 2px left border strip in `#3B82F6`.
- Numerical and temporal columns always align right; text aligns left.

### Risk Badges & Status Chips
- Pill-shaped micro-containers (height: 20px, horizontal padding: 6px, radius: 3px).
- Typography: JetBrains Mono 11px Bold with uppercase rendering.
- **Critical Risk**: Background `rgba(239, 68, 68, 0.12)`, border 1px solid `#EF4444`, text `#F87171`.
- **Medium Risk**: Background `rgba(245, 158, 11, 0.12)`, border 1px solid `#F59E0B`, text `#FBBF24`.
- **Verified / Low Risk**: Background `rgba(16, 185, 129, 0.12)`, border 1px solid `#10B981`, text `#34D399`.

### Input Fields & Search Bars
- Background: `#0B1120`, border: 1px solid `#334155`, text: `#F8FAFC`.
- Focus state: Border 1px solid `#3B82F6`, zero outer glow rings to keep grid lines razor-sharp.
- Filter chips and query builders integrate monospaced operators (`AND`, `OR`, `NOT`, `EQUALS`) styled in `#60A5FA`.

### Network Graph Nodes & Edge Connectors
- Node containers: Hexagonal or circular icons with double-ring borders indicating entity type (Individual, Shell Corp, Offshore Bank, Crypto Wallet).
- Edge paths: Vector strokes styled by volume weight; normal connections `#334155` (1px solid), suspicious transaction paths `#EF4444` (1.5px dashed or animated particle flow).
- Hover state: Immediate tooltip popover (`#1E293B`, 1px solid `#475569`) revealing cumulative transaction volume and temporal velocity in monospaced data format.