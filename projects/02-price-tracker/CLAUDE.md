# Grailed Price Tracker — CLAUDE.md

## what we're building

A price tracker for Grailed listings. The user can:
- Paste a single Grailed listing URL to track it
- Paste a brand/designer page URL to bulk-add all visible listings
- Import their saved/hearted items (requires Grailed login)

Each tracked item stores price history. The frontend charts price drops over time and marks sold/removed listings.

---

## stack

| layer | tech | package manager |
|---|---|---|
| frontend | Next.js 15 + TypeScript + Tailwind + Recharts | `pnpm` |
| backend | FastAPI (Python 3.11+) | `uv` |
| scraper | Playwright for Python, headless Chromium | — |
| storage | SQLite (local file) | — |

**Hard rules:**
- NEVER use `pip install` or `npm install` — always `uv add` and `pnpm add`
- NEVER use `npm run` — always `pnpm`
- Backend runs via: `uv run uvicorn app.main:app --reload --app-dir backend`
- Frontend runs via: `pnpm dev` inside `frontend/`

---

## repo layout

```
02-price-tracker/
├── CLAUDE.md
├── PROMPT.md
├── README.md
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py          # FastAPI routes only — thin, no business logic
│       ├── db.py            # SQLite init
│       ├── models.py        # Pydantic request/response models
│       ├── repository.py    # PriceRepository — all DB queries
│       ├── service.py       # PriceService — orchestration / business logic
│       ├── scheduler.py     # APScheduler background refresh job
│       ├── auth.py          # Grailed session (storageState)
│       └── scraper/
│           ├── __init__.py
│           ├── base.py      # ScraperStrategy ABC
│           ├── listing.py   # Single listing strategy
│           ├── brand_page.py  # Brand/designer page strategy
│           └── saved_items.py # Saved/hearted items strategy
└── frontend/
    ├── package.json
    └── src/
        └── app/
```

---

## build order — follow this exactly

### phase 0: fetch docs with context7 (do this first, before writing any code)
Use the `context7` MCP to pull current docs for each library before writing code that uses it:
- **FastAPI** — fetch before writing `main.py` and `models.py`
- **Playwright for Python** — fetch before writing `scraper.py` and `auth.py`
- **Recharts** — fetch before writing any chart components

Run these fetches at the start of the relevant phase, not all at once upfront.

### phase 1: backend foundation
1. Fetch FastAPI + Playwright docs via `context7`
2. `db.py` — init SQLite, create `items` and `price_history` tables
3. `models.py` — Pydantic models for all API requests and responses
4. `repository.py` — `PriceRepository` class: all DB read/write, no business logic
5. `auth.py` — Grailed session logic (storageState read/write, login flow)
6. `scraper/base.py` — `ScraperStrategy` ABC with `scrape(url) -> ScrapeResult`
7. `scraper/listing.py` — single listing strategy (use Playwright MCP for selectors first)
8. `scraper/brand_page.py` — brand page strategy (bulk listing URLs)
9. `scraper/saved_items.py` — saved/hearted items strategy (uses auth session)
10. `service.py` — `PriceService`: orchestrates scraper strategies + repository
11. `scheduler.py` — APScheduler in-process background job (calls `service.refresh_all()` on interval)
12. `main.py` — FastAPI routes only, delegates everything to `PriceService`
13. Smoke-test the backend with curl before touching the frontend

### phase 2: frontend
1. Fetch Recharts docs via `context7`
2. Scaffold with `pnpm create next-app@latest frontend --typescript --tailwind --app --no-src-dir` — say no to everything else
3. `pnpm add recharts`
3. Build in this order: types → API client → components → pages
4. Component order: `ItemCard` → `PriceChart` → `ItemList` → `AddItemForm` → main page

### phase 3: integration
1. Run both servers, test the full add → scrape → chart flow with a real Grailed URL
2. Test auth flow (saved items)
3. Test sold/removed listing detection (see below)

### phase 4: deploy
1. Use the `github` MCP to create a public repo and push
2. Use the `vercel` MCP to deploy the `frontend/` directory only

---

## architecture patterns

### layers (top to bottom)
```
FastAPI routes (main.py)
    ↓
PriceService (service.py)       ← business logic, orchestration
    ↓              ↓
PriceRepository   ScraperService (scraper/)
(repository.py)       ↓
    ↓         ScraperStrategy ABC (base.py)
  SQLite       ├── ListingStrategy
               ├── BrandPageStrategy
               └── SavedItemsStrategy
                        ↓
                    Playwright

APScheduler (scheduler.py) → calls PriceService.refresh_all() on interval
```

**Rules:**
- Routes ONLY call `PriceService` — never touch the DB or scraper directly
- `PriceService` ONLY calls `PriceRepository` and `ScraperStrategy` implementations
- `PriceRepository` ONLY does DB reads/writes — no scraping, no business logic
- Each `ScraperStrategy` handles one input mode and returns a `ScrapeResult`

---

## scraper rules — read before writing scraper/

### before writing any selector code
**Use the Playwright MCP interactively** to open real Grailed pages and find stable selectors. Do not guess or use selectors from memory. Run:
> "Use the playwright MCP to open [grailed listing URL], find the element containing the price, and give me the most stable CSS selector."

Do this for:
- Single listing page (price, title, image)
- Brand/designer page (listing cards)
- A sold listing (what does Grailed actually show? redirect? 404? "SOLD" banner?)

### sold/removed listing detection
Before writing detection logic, use the Playwright MCP to inspect what Grailed actually returns when a listing is gone. Possibilities: HTTP 404, redirect to homepage, page with a "sold" indicator, empty DOM. Implement based on what we observe — not assumptions.

When a listing is gone, set `status = 'sold'` and `sold_at = datetime('now')` in the DB. Never delete the item.

### auth (saved/hearted items)
- Use Playwright `storageState` to persist the Grailed session
- Session file lives at `backend/grailed_session.json` (gitignored)
- On first run (no session file): open a **headed** browser, navigate to `grailed.com/login`, wait for the user to log in manually, then save `storageState`
- On subsequent runs: load `storageState` into a headless context

### scraper extraction order for a listing page
1. Grailed-specific CSS selectors (found via Playwright MCP)
2. `og:price:amount` or `product:price:amount` meta tags
3. Currency regex near a heading as last resort

### error handling
- Catch `PlaywrightTimeoutError` specifically — don't use bare `except`
- On failure: return a clear error message, never crash the server
- Log with context: what URL, what strategy failed

---

## API routes

| method | path | description |
|---|---|---|
| POST | `/items` | `{ "url": "..." }` — scrape + store item |
| GET | `/items` | all items with latest price |
| GET | `/items/{id}/history` | full price history for charting |
| POST | `/items/{id}/refresh` | re-scrape, append new price point |
| POST | `/refresh-all` | re-scrape all active items |
| POST | `/items/bulk` | `{ "urls": [...] }` — bulk add from brand page or saved items |
| GET | `/auth/status` | returns `{ "logged_in": bool }` |
| POST | `/auth/login` | triggers headed browser login flow |

---

## database schema

```sql
CREATE TABLE items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT NOT NULL UNIQUE,
    title      TEXT,
    image_url  TEXT,
    status     TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'sold' | 'removed'
    sold_at    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE price_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    price      REAL NOT NULL,
    scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## naming conventions

| element | convention |
|---|---|
| Python files | `snake_case` |
| Python functions | `snake_case` |
| Python classes | `PascalCase` |
| TS/JS files | `camelCase` |
| React components | `PascalCase` |
| Constants | `SCREAMING_SNAKE_CASE` |
| Env vars | `SCREAMING_SNAKE_CASE` |

---

## commit conventions (conventional commits)

Format: `type(scope): imperative description`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(db): add items and price_history tables
feat(scraper): extract price and title from Grailed listing
feat(auth): persist Grailed session via storageState
fix(scraper): handle sold listing detection
feat(api): add bulk import endpoint
feat(ui): add PriceChart with Recharts line chart
chore(deps): add recharts to frontend
```

---

## product decisions (locked in)

| decision | choice |
|---|---|
| Auto-refresh interval | Every 1 hour via APScheduler |
| Price drop badge threshold | 10%+ drop since first tracked price |
| Brand page depth | First page of listings only (no pagination) |
| Input UX | 3 tabs: Single URL / Brand Page / My Saved Items |

---

## environment variables

```
# backend/.env
DB_PATH=grailed_tracker.db
SESSION_PATH=grailed_session.json

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## gitignore additions needed
```
backend/grailed_session.json
backend/grailed_tracker.db
backend/.venv
frontend/.next
frontend/node_modules
.env
.env.local
```

---

## when something breaks

Invoke the `debugger` subagent with:
- The full error / stack trace
- The target URL
- What scraper strategy was being attempted

Do not try to fix scraper failures by guessing — always inspect with the Playwright MCP first.
