"""
viop.py — fetch VIOP USD/TRY currency futures via borsapy
         and interpolate to standard tenors (1M, 3M, 6M, 12M).

borsapy 0.8.7 API:
  VIOP().currency_futures  →  DataFrame with columns:
    code, contract, price, change, volume_tl, volume_qty, category
  Contract codes: F_USDTRY{MMYY}  (e.g. F_USDTRY0526 = May 2026)
                  TM_F_USDTRY{DDMMYY}  (weekly contracts)
"""

import logging
import re
from datetime import date, timedelta
import math
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Standard tenors in days
TENORS = {"1M": 30, "3M": 91, "6M": 182, "12M": 365}

# Minimum days to expiry to be considered liquid
MIN_DAYS = 5


def _last_friday(year: int, month: int) -> date:
    """Return the last Friday of a given month."""
    # Start from the last day of the month and walk back
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    days_back = (last_day.weekday() - 4) % 7  # 4 = Friday
    return last_day - timedelta(days=days_back)


def _parse_monthly_expiry(code: str) -> Optional[date]:
    """Parse F_USDTRY{MMYY} → expiry date (last Friday of that month)."""
    m = re.match(r"F_USDTRY(\d{2})(\d{2})$", code)
    if not m:
        return None
    month, year_2d = int(m.group(1)), int(m.group(2))
    year = 2000 + year_2d
    if not (1 <= month <= 12):
        return None
    return _last_friday(year, month)


def _parse_weekly_expiry(code: str) -> Optional[date]:
    """Parse TM_F_USDTRY{DDMMYY} → exact expiry date."""
    m = re.match(r"TM_F_USDTRY(\d{2})(\d{2})(\d{2})$", code)
    if not m:
        return None
    day, month, year_2d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    year = 2000 + year_2d
    try:
        return date(year, month, day)
    except ValueError:
        return None


def fetch_raw_contracts(today: Optional[date] = None) -> pd.DataFrame:
    """
    Fetch all VIOP currency futures and return a clean DataFrame
    with only USDTRY contracts that have >= MIN_DAYS to expiry.

    Returned columns: symbol, price, expiry, days_to_expiry
    """
    today = today or date.today()

    try:
        from borsapy.viop import VIOP
        raw = VIOP().currency_futures
    except Exception as e:
        raise RuntimeError(f"borsapy fetch failed: {e}") from e

    if raw is None or raw.empty:
        raise RuntimeError("borsapy returned empty DataFrame")

    # Defensive column detection
    logger.info("borsapy columns: %s", list(raw.columns))
    logger.debug("\n%s", raw.to_string())

    # Identify price column
    price_candidates = ["price", "last", "close", "settlement", "Son", "Fiyat", "SonFiyat", "uzlasma"]
    price_col = next((c for c in price_candidates if c in raw.columns), None)

    # Identify symbol/code column
    code_candidates = ["code", "symbol", "Sembol", "kod", "Kod"]
    code_col = next((c for c in code_candidates if c in raw.columns), None)

    if price_col is None or code_col is None:
        msg = (
            f"Cannot identify required columns.\n"
            f"  Available: {list(raw.columns)}\n"
            f"  Tried price cols: {price_candidates}\n"
            f"  Tried code cols: {code_candidates}"
        )
        logger.error(msg)
        raise RuntimeError(msg)

    records = []
    for _, row in raw.iterrows():
        code = str(row[code_col]).strip()
        try:
            price = float(row[price_col])
        except (ValueError, TypeError):
            continue

        if price <= 0:
            continue

        # Only USDTRY contracts
        if "USDTRY" not in code:
            continue

        expiry = _parse_monthly_expiry(code) or _parse_weekly_expiry(code)
        if expiry is None:
            logger.debug("Skipping unrecognized code: %s", code)
            continue

        days = (expiry - today).days
        if days < MIN_DAYS:
            logger.info("Skipping %s — only %d days to expiry", code, days)
            continue

        records.append({
            "symbol": code,
            "price": price,
            "expiry": expiry,
            "days_to_expiry": days,
        })

    if not records:
        raise RuntimeError("No valid USDTRY futures contracts found after filtering")

    df = pd.DataFrame(records).sort_values("days_to_expiry").reset_index(drop=True)
    logger.info("Valid USDTRY contracts:\n%s", df.to_string())
    return df


def _log_linear_interp(t: float, t1: float, f1: float, t2: float, f2: float) -> float:
    """Log-linear interpolation between two (time, forward) pairs."""
    return math.exp(math.log(f1) + (t - t1) / (t2 - t1) * (math.log(f2) - math.log(f1)))


def interpolate_tenors(
    contracts: pd.DataFrame, today: Optional[date] = None
) -> dict:
    """
    Given raw contracts DataFrame, interpolate to standard tenors.

    Returns dict keyed by tenor label:
      {
        "1M": {
          "days": 30,
          "price": <interpolated forward>,
          "extrapolated": False,
          "bracket": [{"symbol":..., "price":..., "days":...}, ...]
        },
        ...
      }
    """
    today = today or date.today()
    result = {}

    for label, target_days in TENORS.items():
        below = contracts[contracts["days_to_expiry"] <= target_days]
        above = contracts[contracts["days_to_expiry"] > target_days]

        extrapolated = False

        if above.empty:
            # Extrapolate from the two furthest contracts
            if len(contracts) < 2:
                result[label] = None
                continue
            c1 = contracts.iloc[-2]
            c2 = contracts.iloc[-1]
            price = _log_linear_interp(
                target_days,
                c1["days_to_expiry"], c1["price"],
                c2["days_to_expiry"], c2["price"],
            )
            extrapolated = True
            bracket = [
                {"symbol": c1["symbol"], "price": c1["price"], "days": int(c1["days_to_expiry"])},
                {"symbol": c2["symbol"], "price": c2["price"], "days": int(c2["days_to_expiry"])},
            ]
        elif below.empty:
            # Target is before all contracts — use nearest contract as proxy
            c = above.iloc[0]
            price = c["price"]
            bracket = [{"symbol": c["symbol"], "price": c["price"], "days": int(c["days_to_expiry"])}]
        else:
            c1 = below.iloc[-1]   # nearest below
            c2 = above.iloc[0]    # nearest above
            if c1["days_to_expiry"] == c2["days_to_expiry"]:
                price = c1["price"]
            else:
                price = _log_linear_interp(
                    target_days,
                    c1["days_to_expiry"], c1["price"],
                    c2["days_to_expiry"], c2["price"],
                )
            bracket = [
                {"symbol": c1["symbol"], "price": c1["price"], "days": int(c1["days_to_expiry"])},
                {"symbol": c2["symbol"], "price": c2["price"], "days": int(c2["days_to_expiry"])},
            ]

        result[label] = {
            "days": target_days,
            "price": round(price, 4),
            "extrapolated": extrapolated,
            "bracket": bracket,
        }

    return result


def get_viop_snapshot() -> dict:
    """
    Main entry point: fetch contracts, interpolate, return snapshot dict.
    Raises RuntimeError on failure.
    """
    contracts = fetch_raw_contracts()
    tenors = interpolate_tenors(contracts)
    raw_list = contracts.to_dict(orient="records")
    # Make dates JSON-serialisable
    for r in raw_list:
        r["expiry"] = r["expiry"].isoformat()
    return {"tenors": tenors, "raw_contracts": raw_list}
