"""Sharp math: de-vig, fair odds, EV, Kelly, closing line value.

De-vig methods (what the sharp crowd uses as of 2026):
  power (default)  - handles favorite/longshot bias without overcorrecting
  shin             - preferred for sharp consensus and futures
  multiplicative   - simple, underrates longshots
  additive         - equal margin off each side
"""
import os

DEVIG = os.getenv("UNK_DEVIG_METHOD", "power")
KELLY_FRACTION = float(os.getenv("UNK_KELLY_FRACTION", "0.25"))
KELLY_CAP = float(os.getenv("UNK_KELLY_CAP", "0.05"))  # never suggest more than this share of bankroll
BANKROLL_UNITS = float(os.getenv("UNK_BANKROLL_UNITS", "100"))


def to_decimal(american):
    a = float(american)
    return 1 + (a / 100 if a > 0 else 100 / -a)


def implied(american):
    return 1 / to_decimal(american)


def to_american(p):
    if not 0 < p < 1:
        raise ValueError(f"probability out of range: {p}")
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


def _bisect(f, lo, hi, iters=100):
    for _ in range(iters):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def devig(prices, method=None):
    """American prices for every side of one market -> fair probabilities summing to 1."""
    method = method or DEVIG
    q = [implied(p) for p in prices]
    book = sum(q)
    if method == "multiplicative":
        return [x / book for x in q]
    if method == "additive":
        return [x - (book - 1) / len(q) for x in q]
    if method == "power":
        k = _bisect(lambda k: sum(x ** k for x in q) - 1, 1.0, 10.0)
        return [x ** k for x in q]
    if method == "shin":
        n = len(q)

        def fair(z):
            return [((z * z + 4 * (1 - z) * x * x / book) ** 0.5 - z) / (2 * (1 - z)) for x in q]
        z = _bisect(lambda z: sum(fair(z)) - 1, 0.0, 0.4) if n > 1 else 0.0
        return fair(z)
    raise ValueError(f"unknown devig method {method!r}")


def ev(price, fair_p):
    """Expected return per unit staked."""
    return fair_p * to_decimal(price) - 1


def kelly(price, fair_p, fraction=None):
    """Fractional Kelly stake as a share of bankroll (0 when there is no edge)."""
    b = to_decimal(price) - 1
    full = (b * fair_p - (1 - fair_p)) / b
    return max(0.0, min(full * (fraction if fraction is not None else KELLY_FRACTION), KELLY_CAP))


def kelly_units(price, fair_p):
    return round(kelly(price, fair_p) * BANKROLL_UNITS, 2)


def clv(bet_price, close_fair_p):
    """Closing line value: your price's EV measured against the de-vigged closing probability."""
    return ev(bet_price, close_fair_p)
