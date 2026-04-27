# Grailed Price Tracker — Design Brief

## concept

A companion tool for Grailed shoppers. The aesthetic should feel like it belongs next to Grailed — dark, editorial, typographically clean. Not a generic SaaS dashboard. Think: data utility dressed in streetwear.

---

## tone & aesthetic

- **Dark mode only.** Background near-black (`#0a0a0a`), not pure black.
- **Minimal color.** White text, mid-gray secondary text, one accent color for interactive elements and price drops. Grailed uses a warm off-white and green for price drops — we lean into that.
- **Typography-forward.** Grailed uses tight, uppercase labels and clean sans-serif. Emulate that: small all-caps section labels, strong price figures.
- **Dense but breathable.** Item cards are compact but not cramped. The grid should feel like a feed, not a spreadsheet.

---

## color tokens (suggested)

| token | value | use |
|---|---|---|
| `bg-base` | `#0a0a0a` | page background |
| `bg-surface` | `#141414` | cards, panels |
| `bg-elevated` | `#1f1f1f` | hover states, modals |
| `border` | `#2a2a2a` | card borders, dividers |
| `text-primary` | `#f5f5f5` | headings, prices |
| `text-secondary` | `#888888` | labels, metadata |
| `accent` | `#e8ff00` | CTA buttons, active tab indicator (Grailed yellow-green) |
| `drop-positive` | `#22c55e` | price drop badge (green) |
| `sold` | `#ef4444` | SOLD badge |

---

## screens

### 1. main dashboard

**Layout:** Full-width. Sticky top bar. Content area below.

**Top bar (sticky):**
- Left: app wordmark — `GRAILED TRACKER` in tight uppercase
- Right: `Refresh All` button (ghost style, border only) + last-refreshed timestamp in secondary text

**Input section:**
- 3-tab switcher directly below the top bar:
  - `SINGLE LISTING` | `BRAND PAGE` | `MY SAVED ITEMS`
  - Active tab has accent-color bottom border
- Below tabs: URL input field (full width, dark border, placeholder text matching the selected tab) + `TRACK` button in accent color
- For `MY SAVED ITEMS` tab: if not logged in, show a `CONNECT GRAILED ACCOUNT` button instead of the URL input. On click, triggers the Playwright login flow with a "Opening browser to log in…" status message.

**Item grid:**
- Below the input section
- 3-column grid on desktop, 2-column on tablet, 1-column on mobile
- Each cell is an Item Card (see below)
- Empty state: centered illustration or icon + "No items tracked yet. Paste a URL above to start."

---

### 2. item card (collapsed)

Compact card. Roughly square-ish ratio.

```
┌──────────────────────────────┐
│  [product image — top half]  │
│                              │
├──────────────────────────────┤
│  Stone Island Jacket    SOLD │  ← title (truncated 1 line) + optional badge
│  Size M · AW22               │  ← metadata in secondary text
│                              │
│  $420          ↓ 18%         │  ← price (large) + drop badge if >= 10%
│  [sparkline chart]           │  ← mini recharts line, last 10 price points
│                              │
│  [Refresh ↺]                 │  ← small icon button, bottom right
└──────────────────────────────┘
```

**States:**
- **Active:** normal card
- **SOLD:** image is grayscale + 50% opacity, red `SOLD` badge top-right over the image, price shows last known price in secondary text
- **Loading (refresh):** skeleton shimmer over the card
- **Hover:** subtle `bg-elevated` lift, border brightens slightly

**Price drop badge:** pill shape, green background, white text — `↓ 18%`. Only appears when drop is ≥ 10% from first tracked price. If price went up, show nothing (we don't care about increases).

---

### 3. item detail (expanded / modal)

Click anywhere on a card (except the Refresh button) opens a detail view.

**Layout:** Full-screen modal or large slide-over panel from the right. Dark overlay behind.

```
┌─────────────────────────────────────────────────────┐
│  [X close]                                          │
│                                                     │
│  [product image, left ~35%]  │  Title              │
│                              │  Size · Season      │
│                              │  Current: $420      │
│                              │  First tracked: $515│
│                              │  Drop: ↓ 18.6%      │
│                              │  [View on Grailed ↗]│
│                                                     │
│  ─────────────── PRICE HISTORY ─────────────────   │
│                                                     │
│  [Full Recharts LineChart, date on X, price on Y]  │
│  Tooltip on hover showing exact date + price        │
│                                                     │
│  Last refreshed: 2 hours ago · [Refresh now]        │
└─────────────────────────────────────────────────────┘
```

**Chart notes:**
- X axis: dates (formatted as `MMM D`)
- Y axis: price in USD, formatted as `$XXX`
- Line color: accent (`#e8ff00`) or white
- Dot on each data point
- If only 1 price point: show a message "Check back after the next refresh to see price history"
- SOLD items: chart still shows full history, last point labeled "SOLD"

---

### 4. my saved items tab — auth state

**Logged out:**
```
┌──────────────────────────────────────────────────────┐
│  CONNECT YOUR GRAILED ACCOUNT                        │
│                                                      │
│  We'll open a browser window so you can log in.     │
│  Your session is saved locally — we never store     │
│  your credentials.                                   │
│                                                      │
│  [ Connect Grailed Account ]  ← accent button        │
└──────────────────────────────────────────────────────┘
```

**Connecting (browser opened):**
- Button becomes disabled, spinner, text: "Opening browser… log in and close the window when done"

**Logged in:**
- Shows your Grailed username in the tab: `MY SAVED ITEMS (@username)`
- Import button: `IMPORT SAVED ITEMS` — triggers brand page bulk scrape of your hearted listings
- After import: items appear in the grid, tagged with a small heart icon to indicate they came from your saves

---

## component inventory

| component | description |
|---|---|
| `TopBar` | Sticky header with wordmark + Refresh All |
| `TabSwitcher` | 3-tab input mode selector |
| `UrlInput` | Input + Track button, changes placeholder per tab |
| `AuthPrompt` | Connect account CTA for saved items tab |
| `ItemGrid` | Responsive grid wrapper |
| `ItemCard` | Collapsed card with image, price, sparkline, badges |
| `SoldBadge` | Red pill overlay |
| `DropBadge` | Green pill showing % drop |
| `Sparkline` | Mini Recharts line (no axes, no tooltip) |
| `ItemDetail` | Full modal/panel with chart |
| `PriceChart` | Full Recharts LineChart with axes + tooltip |
| `SkeletonCard` | Loading shimmer placeholder |
| `EmptyState` | Empty grid message |

---

## interaction notes

- **Optimistic UI:** when the user clicks Track, immediately show a skeleton card in the grid while the scrape runs in the background
- **Refresh feedback:** the Refresh button on each card spins while the re-scrape is in progress
- **Refresh All:** shows a progress indicator in the top bar ("Refreshing 12 items…")
- **Error state on card:** if a scrape fails, show a small red warning icon on the card with a tooltip: "Last refresh failed — click to retry"
- **Auto-refresh:** no visible indicator needed unless the user is actively on the page during a background refresh; in that case, cards that were just updated show a subtle flash

---

## responsive breakpoints

| breakpoint | grid columns | notes |
|---|---|---|
| mobile (< 640px) | 1 | full-width cards |
| tablet (640–1024px) | 2 | |
| desktop (> 1024px) | 3 | max-width container centered |

---

## what to hand off to the designer

1. These screens need high-fidelity mocks (Figma preferred):
   - Main dashboard — empty state
   - Main dashboard — populated grid (mix of active, sold, drop-badged items)
   - Item card — all 4 states (active, sold, loading, hover)
   - Item detail modal — active item with full chart
   - Item detail modal — sold item with history
   - My Saved Items tab — logged out state
   - My Saved Items tab — connecting state

2. Design system needed:
   - Color tokens (see above)
   - Typography scale (suggest: Inter or Helvetica Neue)
   - Spacing scale (8px base)
   - Button variants: primary (accent fill), ghost (border only), icon-only
   - Badge variants: SOLD, drop %, loading

3. Assets needed from designer:
   - Empty state illustration or icon
   - App favicon / wordmark lockup
   - Any custom icons (refresh, external link, heart)
