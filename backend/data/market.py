"""
market.py — fetch spot USD/TRY and interest rates.

Sources:
  Spot:  yfinance  USDTRY=X
  r_TRY: manual fallback from .env (R_TRY=0.40)
         (^BIST not reliably available on Yahoo Finance)
  r_USD: FRED FEDFUNDS (requires FRED_API_KEY) or
         .env R_USD_FALLBACK (default 0.0364 = 3.64%)
"""

import os
import logging
from typing import Optional, Tuple
import requests

logger = logging.getLogger(__name__)


def _load_env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        logger.warning("Cannot parse %s=%r as float, using default %s", key, val, default)
        return default


def get_spot() -> Tuple[float, str]:
    """
    Return (spot_rate, source_label) for USD/TRY.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker("USDTRY=X")
        fi = ticker.fast_info
        price = fi.last_price
        if price and price > 0:
            return round(float(price), 4), "yfinance"
    except Exception as e:
        logger.warning("yfinance fast_info failed: %s", e)

    # Fallback: history
    try:
        import yfinance as yf
        hist = yf.Ticker("USDTRY=X").history(period="2d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 4), "yfinance-history"
    except Exception as e:
        logger.warning("yfinance history fallback failed: %s", e)

    raise RuntimeError("Cannot fetch USD/TRY spot from yfinance")


def get_r_try() -> Tuple[float, str]:
    """
    Return (r_try_decimal, source_label).
    Always uses manual fallback from R_TRY env var.
    Returns (rate, 'manual') always — CBRT rate is not available via yfinance.
    """
    rate = _load_env_float("R_TRY", 0.40)
    return rate, "manual"


def get_r_usd() -> Tuple[float, str]:
    """
    Return (r_usd_decimal, source_label).
    Primary: FRED FEDFUNDS API.
    Fallback: R_USD_FALLBACK env var (default 0.0364 = 3.64%).
    """
    api_key = os.getenv("FRED_API_KEY", "")
    if api_key and api_key != "your_fred_api_key_here":
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": "FEDFUNDS",
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            }
            r = requests.get(url, params=params, timeout=8)
            r.raise_for_status()
            obs = r.json().get("observations", [])
            if obs:
                # FRED returns percentage — divide by 100
                rate = float(obs[0]["value"]) / 100.0
                return round(rate, 6), f"FRED ({obs[0]['date']})"
        except Exception as e:
            logger.warning("FRED fetch failed: %s — using fallback", e)

    # Fallback
    rate = _load_env_float("R_USD_FALLBACK", 0.0364)
    return rate, "manual-fallback"


def get_all_market_data() -> dict:
    """
    Fetch spot, r_TRY, r_USD. Return dict with values and source labels.
    """
    errors = []
    spot, spot_src = None, "error"
    try:
        spot, spot_src = get_spot()
    except Exception as e:
        errors.append(f"spot: {e}")

    r_try, r_try_src = get_r_try()
    r_usd, r_usd_src = get_r_usd()

    return {
        "spot": spot,
        "spot_source": spot_src,
        "r_try": r_try,
        "r_try_source": r_try_src,
        "r_usd": r_usd,
        "r_usd_source": r_usd_src,
        "errors": errors,
    }
