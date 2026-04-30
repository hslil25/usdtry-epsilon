#!/usr/bin/env python3
"""
diagnose.py — run before writing viop.py.
Confirms borsapy column names and yfinance USDTRY=X availability.

Usage:
  python3 diagnose.py
"""
import sys
import traceback
import os


def check_env():
    print("\n=== .env ===")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        r_try = os.getenv("R_TRY", "NOT SET")
        r_usd_fb = os.getenv("R_USD_FALLBACK", "NOT SET")
        fred_key = os.getenv("FRED_API_KEY", "NOT SET")
        print(f"R_TRY             = {r_try}")
        print(f"R_USD_FALLBACK    = {r_usd_fb}")
        is_real = fred_key and fred_key not in ("NOT SET", "your_fred_api_key_here")
        print(f"FRED_API_KEY      = {'SET (' + fred_key[:8] + '...)' if is_real else 'NOT SET or example value'}")
    except ImportError:
        print("python-dotenv not installed — pip3 install python-dotenv")


def check_borsapy():
    print("\n=== borsapy ===")
    try:
        import borsapy
        print(f"borsapy version: {getattr(borsapy, '__version__', 'unknown')}")
        from borsapy.viop import VIOP
        print("VIOP class imported OK")

        v = VIOP()
        df = v.currency_futures          # property, not a method call
        print(f"\nDataFrame shape: {df.shape}")
        print(f"ALL column names: {list(df.columns)}")
        print(f"\nAll rows:")
        print(df.to_string())
        print(f"\nDtypes:\n{df.dtypes}")
        print(f"\nUSDTRY rows only:")
        usd = df[df["code"].str.contains("USDTRY", na=False)]
        print(usd[["code", "price"]].to_string())

    except ImportError as e:
        print(f"ERROR: cannot import borsapy: {e}")
        print("Install with: pip3 install borsapy")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()


def check_yfinance():
    print("\n=== yfinance ===")
    try:
        import yfinance as yf
        print(f"yfinance version: {yf.__version__}")

        print("\nFetching USDTRY=X spot...")
        ticker = yf.Ticker("USDTRY=X")
        try:
            price = ticker.fast_info.last_price
            print(f"fast_info.last_price: {price:.4f}")
        except Exception as e:
            print(f"fast_info error: {e}")

        hist = ticker.history(period="3d")
        if hist.empty:
            print("ERROR: history returned empty for USDTRY=X")
        else:
            print(f"History (last 3d):\n{hist[['Close']].to_string()}")

        print("\nFetching ^IRX (USD short rate proxy)...")
        irx = yf.Ticker("^IRX").history(period="3d")
        if irx.empty:
            print("^IRX empty")
        else:
            print(f"^IRX: {irx['Close'].iloc[-1]:.2f}% annualised")

    except ImportError as e:
        print(f"ERROR: cannot import yfinance: {e}")
        print("Install with: pip3 install yfinance")


def check_fred():
    print("\n=== FRED (Fed funds rate) ===")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key or api_key == "your_fred_api_key_here":
        print("FRED_API_KEY not set — will use R_USD_FALLBACK from .env")
        return

    try:
        import requests
        params = {
            "series_id": "FEDFUNDS",
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 3,
        }
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params=params, timeout=10
        )
        r.raise_for_status()
        obs = r.json().get("observations", [])
        for o in obs:
            print(f"FEDFUNDS {o['date']}: {o['value']}%  (decimal: {float(o['value'])/100:.4f})")
    except Exception as e:
        print(f"ERROR fetching FRED: {e}")
        traceback.print_exc()


def check_endpoint():
    print("\n=== /snapshot endpoint ===")
    try:
        import urllib.request, json
        with urllib.request.urlopen("http://localhost:8000/snapshot", timeout=5) as r:
            data = json.loads(r.read())
        print(f"fetched_at: {data['fetched_at']}")
        print(f"spot: {data['market']['spot']}")
        print(f"r_try: {data['market']['r_try']} ({data['market']['r_try_source']})")
        print(f"r_usd: {data['market']['r_usd']} ({data['market']['r_usd_source']})")
        print(f"errors: {data['errors']}")
        for e in data['epsilon']:
            print(f"  {e['tenor']}: ε={e['epsilon']:+.4f}  signal={e['signal']}"
                  f"{'  ⚠EXTRAP' if e.get('extrapolated') else ''}")
    except Exception as e:
        print(f"Backend not reachable: {e}")
        print("Start it with: python3 -m uvicorn backend.main:app --port 8000")


if __name__ == "__main__":
    print("=" * 60)
    print("USD/TRY ε Dashboard — Data Source Diagnostics")
    print("=" * 60)
    check_env()
    check_borsapy()
    check_yfinance()
    check_fred()
    check_endpoint()
    print("\n=== Done ===")
