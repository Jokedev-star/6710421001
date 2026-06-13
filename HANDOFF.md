# SET50 Thailand Dashboard — Handoff Document

> **Last updated:** 2026-06-13
> **Repo:** `github.com/Jokedev-star/6710421001` (formerly `DSDS`)
> **Live app:** `https://6710421001.streamlit.app/`
> **Platform:** Streamlit Community Cloud (auto-deploys on push to `main`)

---

## Project Overview

A Streamlit dashboard for the SET50 Thailand stock index. It displays major shareholder data, ownership charts, an interactive relationship graph (vis.js), and top gainers/losers with market cap distribution.

---

## File Structure

```
├── app.py                  # Main Streamlit app (~617 lines, single file)
├── shareholder_data.json   # Pre-fetched SET API data (50 stocks, 10 holders each)
├── fetch_all_data.py       # Script to re-fetch shareholder data from SET.or.th
├── requirements.txt        # Python dependencies
├── .gitignore              # Ignores __pycache__, *.pyc, debug/temp files
└── .devcontainer/          # Codespaces dev container config
```

---

## App Architecture (`app.py`)

### Two Tabs

1. **Shareholder Data** (tab1)
   - Searchable/sortable table of top 10 shareholders per SET50 company
   - Ownership distribution bar chart (top 5 holders per company)
   - **Shareholder Relationship Graph** — interactive vis.js network graph with filters
   - Node detail panel (select a node to see holder/company info)

2. **Top Gainers / Losers** (tab2)
   - Horizontal bar charts for top 5 gainers and losers by % change
   - Market cap distribution pie chart (top 15)

### Key Functions

| Function | Purpose |
|----------|---------|
| `load_all_stocks_summary(tickers)` | Fetches live price/volume/marketcap from Yahoo Finance. Cached 1 hour. |
| `load_shareholder_data()` | Loads `shareholder_data.json`. Cached 24 hours. |
| `classify_holder_type(name)` | Heuristic classification: government, nvdr, fund, institution, company, individual, unknown. Handles both Thai and English names. |
| `get_shareholders_for_symbol(symbol, sh_data)` | Extracts top 10 shareholders for a symbol from loaded data. |
| `make_shareholder_graph_html(nodes, edges)` | Generates HTML/JS fragment for vis-network graph. Returns raw HTML string. |
| `build_graph_data(symbol, rows, top_n, min_pct, holder_types)` | Builds nodes/edges arrays for vis.js. Supports "ALL" mode (all 50 companies) or single-company mode. |

### Graph Implementation Details

- **Library:** vis-network v10.0.2 via jsdelivr CDN (UMD standalone build)
  - JS: `https://cdn.jsdelivr.net/npm/vis-network@10.0.2/standalone/umd/vis-network.min.js`
  - CSS: `https://cdn.jsdelivr.net/npm/vis-network@10.0.2/dist/dist/vis-network.min.css`
- **Rendering:** Uses `st.iframe(html, height=650)` — renders HTML in an iframe that executes JavaScript natively
- **Node IDs:** Companies use `COMPANY_{symbol}`, holders use `HOLDER_{hash(name) % 10^9}`
- **Edge IDs:** `E_{symbol}_{holder_id}` — deduplicated via `seen_edges` set
- **Node dedup:** Holders deduplicated via `seen_holders` dict (same holder across multiple companies becomes one node)
- **Physics:** Barnes-Hut solver with stabilization (150 iterations)
- **Interactivity:** Hover tooltips, click selection, zoom, drag, keyboard navigation

### Graph Filters (UI controls above the graph)

| Filter | Widget | Default | Range |
|--------|--------|---------|-------|
| Company | selectbox | ALL | ALL or any SET50 stock |
| Top N shareholders | slider | 5 | 3–10 |
| Min ownership % | slider | 0.0 | 0.0–20.0 (step 0.5) |
| Holder type | selectbox | All | All, government, nvdr, fund, institution, company, individual |

### Holder Type Color Scheme

| Type | Color | Hex |
|------|-------|-----|
| company (SET50) | Blue | `#1a73e8` |
| government | Red | `#e74c3c` |
| nvdr | Purple | `#9b59b6` |
| fund | Green | `#27ae60` |
| institution | Orange | `#f39c12` |
| company (holder) | Teal | `#1abc9c` |
| individual | Pink | `#e91e63` |
| unknown | Gray | `#7f8c8d` |

---

## Data Sources

| Data | Source | Method |
|------|--------|--------|
| Shareholders | `https://www.set.or.th/api/set/stock/{symbol}/shareholder` | cloudscraper (bypasses Cloudflare) |
| Stock prices | Yahoo Finance via `yfinance` | `yf.Ticker(sym).info` |

### How to Re-fetch Shareholder Data

```bash
python fetch_all_data.py
```
- Takes ~3-5 minutes (50 stocks with random delays to avoid rate limiting)
- Outputs `shareholder_data.json` with timestamp
- Uses cloudscraper with retry logic (3 attempts per stock)

---

## Dependencies (`requirements.txt`)

```
streamlit
yfinance
pandas
numpy
plotly
pyvis
cloudscraper
```

> Note: `pyvis` is listed but not currently used in `app.py` (was used in an earlier iteration). Can be removed.

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deployment

- **Platform:** Streamlit Community Cloud
- **URL:** `https://6710421001.streamlit.app/`
- **Auto-deploy:** Pushes to `main` branch trigger automatic redeployment
- **Custom subdomain:** Configured in Streamlit Cloud dashboard settings

```bash
git add <files>
git commit -m "description"
git push origin main
# Streamlit Cloud auto-deploys within ~1-2 minutes
```

---

## Recent Commit History

| Commit | Description |
|--------|-------------|
| `42fa59e` | Add debug and temp files to .gitignore |
| `21e1fbb` | Fix shareholder graph rendering and add filters |
| `9637e54` | Trigger Streamlit rebuild |
| `84ec4f4` | Switch from deprecated `st.components.v1.html` to `st.html()`, add error handling |
| `9f40176` | Update vis-network CDN to v10.0.2, remove filters, show all 50 stocks |
| `dc5a00d` | Redesign graph with All mode, filters, detail panel, dark theme |

---

## Known Issues & Gotchas

1. **`st.html()` does NOT execute JavaScript** — Streamlit's `st.html()` uses DOMPurify which strips `<script>` tags. Always use `st.iframe()` for embedded JS. This was the root cause of the graph not rendering.

2. **`st.components.v1.html` is deprecated** — Streamlit deprecated it after 2026-06-01 with `st.iframe()` as the replacement.

3. **Duplicate node/edge IDs crash vis.js** — The `build_graph_data` function uses `hash(name) % 10^9` for holder IDs. Hash collisions or duplicate shareholder entries can produce duplicate IDs. Always deduplicate with `seen_holders` (nodes) and `seen_edges` (edges) sets.

4. **Data staleness** — `shareholder_data.json` was fetched 2026-06-09. Book close dates vary per stock; some may be >1 year old. The app shows a warning note for stale data.

5. **CDN choice matters** — cdnjs.cloudflare.com had reliability issues. jsdelivr (`cdn.jsdelivr.net`) is more reliable from Streamlit Cloud.

6. **Yahoo Finance rate limits** — `load_all_stocks_summary()` fetches 50 stocks sequentially. Cached for 1 hour via `@st.cache_data(ttl=3600)`. If Yahoo blocks requests, stock data will be empty.

7. **SET API requires cloudscraper** — Direct `requests` calls get blocked by Cloudflare. `fetch_all_data.py` visits the SET homepage first to get cookies, then calls the API.

---

## Potential Improvements

- [ ] Add date range selector for historical shareholder data
- [ ] Add export functionality (CSV download for filtered table)
- [ ] Add cross-holding detection (company A holds company B and vice versa)
- [ ] Add sector grouping/coloring for SET50 companies
- [ ] Schedule automatic data refresh (currently manual via `fetch_all_data.py`)
- [ ] Remove unused `pyvis` from requirements.txt
- [ ] Add caching for graph HTML to improve re-render performance
