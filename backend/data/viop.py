"""
viop.py — fetch VIOP USD/TRY currency futures via borsapy
         and interpolate to standard tenors (1M, 3M, 6M, 12M).

borsapy 0.8.7 API:
  VIOP().currency_futures  →  DataFrame with columns:
    code, contract, price, change, volume_tl, volume_qty, category
  Contract codes: F_USDTRY{MMYY}  (e.g. F_USDTRY0526 = May 2026)
                  TM_F_USDTRY{DDMMYY}  (weekly contracts with exact date)

Expiry convention (verified against Borsa Istanbul exchange calendar):
  Monthly contracts → last business day of the contract month.
  "Business day" = Monday–Friday, excluding Turkish public holidays AND
  the arife (eve) of Ramazan/Kurban Bayramı, which the exchange also closes.
  Weekly contracts → the exact date embedded in the code.
"""

import logging
import re
from datetime import date, timedelta
import math
from functools import lru_cache
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

TENORS = {"1M": 30, "3M": 91, "6M": 182, "12M": 365}
MIN_DAYS = 5


@lru_cache(maxsize=16)
def _turkish_market_holidays(year: int):
    """
    Return a set of dates that are non-trading days in Turkey for the given year.
    Includes official public holidays plus the arife (eve) of Bayram periods,
    on which the exchange is closed.
    """
    import holidays as hd
    tr = hd.Turkey(years=year)
    extras = {}
    bayram_keywords = ["Kurban", "Ramazan", "Eid"]
    for d, name in list(tr.items()):
        if any(k in name for k in bayram_keywords):
            arife = d - timedelta(days=1)
            if arife.weekday() < 5 and arife not in tr:
                extras[arife] = f"{name} Arife"
    tr.update(extras)
    return tr


def _last_business_day(year: int, month: int) -> date:
    """
    Return the last business day of a given month, respecting
    Turkish public holidays and Bayram arife closures.
    Matches Borsa Istanbul VIOP contract expiry dates.
    """
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)

    holidays = _turkish_market_holidays(year)
    d = last
    while d.weekday() >= 5 or d in holidays:
        d -= timedelta(days=1)
    return d


def _parse_monthly_expiry(code: str) -> Optional[date]:
    """Parse F_USDTRY{MMYY} → last business day of that month."""
    m = re.match(r"F_USDTRY(\d{2})(\d{2})$", code)
    if not m:
        return None
    month, year_2d = int(m.group(1)), int(m.group(2))
    year = 2000 + year_2d
    if not (1 <= month <= 12):
        return None
    return _last_business_day(year, month)


def _parse_weekly_expiry(code: str) -> Optional[date]:
    """Parse TM_F_USDTRY{DDMMYY} → exact expiry date embedded in code."""
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

    logger.info("borsapy columns: %s", list(raw.columns))

    price_candidates = ["price", "last", "close", "settlement", "Son", "Fiyat", "SonFiyat", "uzlasma"]
    price_col = next((c for c in price_candidates if c in raw.columns), None)

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

        if price <= 0 or "USDTRY" not in code:
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
    return math.exp(math.log(f1) + (t - t1) / (t2 - t1) * (math.log(f2) - math.log(f1)))


def interpolate_tenors(contracts: pd.DataFrame, today: Optional[date] = None) -> dict:
    """
    Interpolate to standard tenors (1M, 3M, 6M, 12M) using log-linear method.
    Extrapolates from the two furthest contracts when no contract exists beyond
    the target tenor, and flags the result as EXTRAPOLATED.
    """
    today = today or date.today()
    result = {}

    for label, target_days in TENORS.items():
        below = contracts[contracts["days_to_expiry"] <= target_days]
        above = contracts[contracts["days_to_expiry"] > target_days]
        extrapolated = False

        if above.empty:
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
            c = above.iloc[0]
            price = c["price"]
            bracket = [{"symbol": c["symbol"], "price": c["price"], "days": int(c["days_to_expiry"])}]
        else:
            c1 = below.iloc[-1]
            c2 = above.iloc[0]
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
    contracts = fetch_raw_contracts()
    tenors = interpolate_tenors(contracts)
    raw_list = contracts.to_dict(orient="records")
    for r in raw_list:
        r["expiry"] = r["expiry"].isoformat()
    return {"tenors": tenors, "raw_contracts": raw_list}
