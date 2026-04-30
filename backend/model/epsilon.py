"""
epsilon.py — ε decomposition and signal classification.

ε = F_actual - F_theoretical
  ε < 0    → carry compression  (corridor credible, market below CIP)
  ε ≈ 0    → neutral
  ε > 0    → break premium     (market pricing devaluation beyond rates)
  ε >> 0   → acute stress

Signal thresholds are calibrated relative to the spot rate.
"""

from backend.model.cip import cip_forward, implied_annual_depreciation


def classify_epsilon(eps: float, spot: float) -> str:
    """
    Classify ε signal. Uses spot-relative thresholds to remain
    scale-invariant across different exchange rate regimes.
    """
    pct = abs(eps) / spot * 100  # ε as % of spot
    if eps < -0.001 * spot:
        return "compression"      # carry compressed below CIP
    elif eps < 0.005 * spot:
        return "neutral"          # ε ≈ 0 (within ~0.5% of spot)
    elif eps < 0.02 * spot:
        return "break-premium"    # moderate devaluation premium
    else:
        return "acute-stress"     # ε >> 0, significant stress signal


def compute_epsilon_snapshot(
    spot: float,
    r_try: float,
    r_usd: float,
    viop_tenors: dict,
) -> list[dict]:
    """
    Compute ε for each available tenor.

    Args:
        spot:        USD/TRY spot
        r_try:       CBRT rate as decimal
        r_usd:       Fed funds rate as decimal
        viop_tenors: dict from viop.interpolate_tenors()

    Returns:
        List of dicts, one per tenor, sorted by days.
    """
    results = []
    tenor_order = ["1M", "3M", "6M", "12M"]

    for label in tenor_order:
        tenor_data = viop_tenors.get(label)
        if tenor_data is None:
            results.append({"tenor": label, "error": "no data"})
            continue

        days = tenor_data["days"]
        f_actual = tenor_data["price"]
        extrapolated = tenor_data.get("extrapolated", False)
        bracket = tenor_data.get("bracket", [])

        f_theoretical = cip_forward(spot, r_try, r_usd, days)
        eps = f_actual - f_theoretical
        signal = classify_epsilon(eps, spot)

        dep_market = implied_annual_depreciation(f_actual, spot, days)
        dep_cip = implied_annual_depreciation(f_theoretical, spot, days)

        results.append({
            "tenor": label,
            "days": days,
            "f_actual": round(f_actual, 4),
            "f_theoretical": round(f_theoretical, 4),
            "epsilon": round(eps, 4),
            "signal": signal,
            "dep_market_pct": round(dep_market, 2),
            "dep_cip_pct": round(dep_cip, 2),
            "extrapolated": extrapolated,
            "bracket": bracket,
        })

    return results
