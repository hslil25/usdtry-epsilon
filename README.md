# USD/TRY ε Dashboard

Decomposes VIOP USD/TRY futures forward premiums into:

- **CIP-implied theoretical forward** — what rates alone predict  
- **ε (epsilon)** — the residual devaluation premium the market is pricing in

## What the signals mean

| ε | Signal | Interpretation |
|---|--------|----------------|
| < 0 | compression | Market trades below CIP — corridor credible |
| ≈ 0 | neutral | Market in line with interest rate differentials |
| > 0 | break-premium | Market pricing extra devaluation beyond rates |
| >> 0 | acute-stress | Significant stress; possible credibility crisis |

## Formula

```
F_theoretical = Spot × (1 + r_TRY × t) / (1 + r_USD × t)
ε = F_actual − F_theoretical
```

Simple interest convention (not continuous). `t = days / 365`.

## Data sources

| Data | Source | Key required |
|------|--------|--------------|
| VIOP USD/TRY futures | borsapy | None (free scrape) |
| USD/TRY spot | yfinance `USDTRY=X` | None |
| r_TRY (CBRT rate) | `.env` `R_TRY` (manual) | None |
| r_USD (Fed funds) | FRED `FEDFUNDS` or `.env` fallback | Optional |

## Setup

```bash
cp .env.example .env
# Edit .env:
#   FRED_API_KEY = <your key from fred.stlouisfed.org>
#   R_TRY = 0.40        # CBRT policy rate as decimal
#   R_USD_FALLBACK = 0.0364   # only used if FRED key absent
```

## Run

```bash
./start.sh
# or manually:
python3 -m uvicorn backend.main:app --port 8000 --reload
cd frontend && ./node_modules/.bin/vite
```

Dashboard → http://localhost:5173  
API → http://localhost:8000/snapshot

## Diagnose

```bash
python3 diagnose.py
```

Prints all borsapy column names, yfinance values, and calls the live `/snapshot` endpoint.

## File structure

```
usdtry-epsilon/
├── backend/
│   ├── main.py              FastAPI — GET /snapshot
│   ├── data/
│   │   ├── viop.py          borsapy fetch + tenor interpolation
│   │   └── market.py        spot (yfinance) + rates
│   └── model/
│       ├── cip.py           CIP forward formula
│       └── epsilon.py       ε decomposition + signal classification
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── api/client.ts
│       └── components/
│           ├── EpsilonCurve.tsx        Panel 1 — ε bar chart
│           ├── ImpliedDepreciation.tsx Panel 2 — depreciation vs corridor
│           └── KeyNumbers.tsx          Panel 3 — rates, raw contracts, timestamps
├── diagnose.py
├── start.sh
└── .env.example
```

## Notes

- `r_TRY` is always manual — shown as **"manual"** badge in the UI. CBRT rate is not reliably available via public APIs.
- FRED key is optional; without it `r_USD` falls back to `R_USD_FALLBACK` (shown as **"manual-fallback"** badge).
- 12M tenor is interpolated between the two furthest contracts; if none exceed 365 days it extrapolates and flags **⚠ EXTRAPOLATED** in the UI.
- Each `/snapshot` request fetches fresh data — no database, no caching.
