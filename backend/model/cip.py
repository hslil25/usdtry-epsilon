"""
cip.py — Covered Interest Parity forward calculation.

F_theoretical = Spot × (1 + r_TRY)^t / (1 + r_USD)^t

Convention: compound interest (discrete annual compounding).
t = days / 365
"""


def cip_forward(spot: float, r_try: float, r_usd: float, days: int) -> float:
    """
    Compute CIP-implied theoretical forward rate.

    Args:
        spot:  current USD/TRY spot rate
        r_try: CBRT policy rate as decimal (e.g. 0.40 for 40%)
        r_usd: Fed funds rate as decimal (e.g. 0.0364 for 3.64%)
        days:  days to maturity

    Returns:
        F_theoretical using discrete annual compounding
    """
    t = days / 365.0
    return spot * ((1 + r_try) ** t) / ((1 + r_usd) ** t)


def implied_annual_depreciation(forward: float, spot: float, days: int) -> float:
    """
    Annualised depreciation implied by a forward rate.
    Returns a percentage (e.g. 18.5 for 18.5% p.a.).
    """
    t = days / 365.0
    if t <= 0 or spot <= 0:
        return 0.0
    return ((forward / spot) - 1) / t * 100
