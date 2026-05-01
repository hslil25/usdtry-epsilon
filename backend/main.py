"""
main.py — FastAPI backend for USD/TRY ε dashboard.

Single endpoint: GET /snapshot
  Fetches all data fresh, computes ε, returns JSON.
  Partial failures return null for that tenor rather than 500.
"""

import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

app = FastAPI(title="USD/TRY ε Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/snapshot")
def snapshot():
    """
    Fetch all market data and compute ε decomposition.
    Returns partial results on data source failures.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    errors = []

    # --- Market data ---
    market = {}
    try:
        from backend.data.market import get_all_market_data
        market = get_all_market_data()
        errors.extend(market.pop("errors", []))
    except Exception as e:
        logger.error("market data fetch failed: %s", e)
        errors.append(f"market: {e}")

    spot = market.get("spot")
    r_try = market.get("r_try")
    r_usd = market.get("r_usd")

    # --- VIOP futures ---
    viop_raw = []
    viop_tenors = {}
    viop_error = None
    try:
        from backend.data.viop import get_viop_snapshot
        viop = get_viop_snapshot()
        viop_raw = viop["raw_contracts"]
        viop_tenors = viop["tenors"]
    except Exception as e:
        logger.error("VIOP fetch failed: %s", e)
        viop_error = str(e)
        errors.append(f"viop: {e}")

    # --- ε computation ---
    epsilon_results = []
    contract_epsilon = []
    if spot and r_try is not None and r_usd is not None:
        try:
            from backend.model.epsilon import compute_epsilon_snapshot, compute_contract_epsilon
            if viop_tenors:
                epsilon_results = compute_epsilon_snapshot(spot, r_try, r_usd, viop_tenors)
            if viop_raw:
                contract_epsilon = compute_contract_epsilon(spot, r_try, r_usd, viop_raw)
        except Exception as e:
            logger.error("epsilon computation failed: %s", e)
            errors.append(f"epsilon: {e}")

    return {
        "fetched_at": fetched_at,
        "market": {
            "spot": spot,
            "spot_source": market.get("spot_source"),
            "r_try": r_try,
            "r_try_source": market.get("r_try_source"),
            "r_usd": r_usd,
            "r_usd_source": market.get("r_usd_source"),
            "interest_differential": (
                round((1 + r_try) / (1 + r_usd) - 1, 6) if r_try and r_usd else None
            ),
            "spot_history": market.get("spot_history", []),
            "weekly_change_pct": market.get("weekly_change_pct"),
        },
        "epsilon": epsilon_results,
        "contract_epsilon": contract_epsilon,
        "viop_contracts": viop_raw,
        "errors": errors,
        "viop_error": viop_error,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
