#!/usr/bin/env python3
"""Calculate Clopper-Pearson 95% Confidence Intervals for Gate Metrics.

Zero-dependency implementation: uses exact closed-form power expressions for k=0 and k=n,
with scipy.stats.beta fallback if available, or numerical bisection on incomplete beta.
"""

import math
from typing import Tuple


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Calculate exact Clopper-Pearson binomial confidence interval."""
    if n == 0:
        return (0.0, 0.0)
    if k == 0:
        return (0.0, 1.0 - (alpha) ** (1.0 / n))
    elif k == n:
        return ((alpha) ** (1.0 / n), 1.0)

    try:
        from scipy.stats import beta
        lower = float(beta.ppf(alpha / 2.0, k, n - k + 1))
        upper = float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
        return (lower, upper)
    except ImportError:
        # High precision regularized incomplete beta bisection fallback
        def betacf(a: float, b: float, x: float) -> float:
            # Continued fraction for incomplete beta
            max_it = 100
            eps = 3e-10
            qab = a + b
            qap = a + 1.0
            qam = a - 1.0
            c = 1.0
            d = 1.0 - qab * x / qap
            if abs(d) < 1e-30:
                d = 1e-30
            d = 1.0 / d
            h = d
            for m in range(1, max_it + 1):
                m2 = 2 * m
                aa = m * (b - m) * x / ((qam + m2) * (a + m2))
                d = 1.0 + aa * d
                if abs(d) < 1e-30:
                    d = 1e-30
                c = 1.0 + aa / c
                if abs(c) < 1e-30:
                    c = 1e-30
                d = 1.0 / d
                h *= d * c
                aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
                d = 1.0 + aa * d
                if abs(d) < 1e-30:
                    d = 1e-30
                c = 1.0 + aa / c
                if abs(c) < 1e-30:
                    c = 1e-30
                d = 1.0 / d
                del_h = d * c
                h *= del_h
                if abs(del_h - 1.0) < eps:
                    break
            return h

        def betai(a: float, b: float, x: float) -> float:
            if x <= 0.0:
                return 0.0
            if x >= 1.0:
                return 1.0
            lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
            bt = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta)
            if x < (a + 1.0) / (a + b + 2.0):
                return bt * betacf(a, b, x) / a
            else:
                return 1.0 - bt * betacf(b, a, 1.0 - x) / b

        # Bisect for lower
        lo, hi = 0.0, float(k) / n
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if betai(k, n - k + 1, mid) < alpha / 2.0:
                lo = mid
            else:
                hi = mid
        lower = lo

        # Bisect for upper
        lo, hi = float(k) / n, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if betai(k + 1, n - k, mid) < 1.0 - alpha / 2.0:
                lo = mid
            else:
                hi = mid
        upper = hi
        return (lower, upper)


def main() -> None:
    cases = [
        ("G4 (False Acceptance Rate)", 0, 31),
        ("G5a (Critical UCR)", 0, 69),
        ("G5b (Non-Critical UCR)", 0, 27),
        ("G6 (Regression vs E1)", 0, 35),
    ]

    print("==========================================================")
    print("CLOPPER-PEARSON 95% CONFIDENCE INTERVALS (Exact Binomial)")
    print("==========================================================")
    for name, k, n in cases:
        low, high = clopper_pearson(k, n, alpha=0.05)
        print(f"{name}: {k}/{n} -> CI95 = [{low * 100:.2f}%, {high * 100:.2f}%]")


if __name__ == "__main__":
    main()
