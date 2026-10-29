"""Rubric weight auto-normalisation (SYS-F-005)."""
from decimal import ROUND_FLOOR, Decimal

CENT = Decimal("0.01")
HUNDRED = Decimal("100.00")


def normalize_weights(raw_weights):
    """Scale positive raw weights so they sum to exactly 100.00 (largest-remainder rounding to 2 dp)."""
    weights = [Decimal(str(w)) for w in raw_weights]
    if not weights:
        raise ValueError("At least one rubric component is required.")
    if any(w <= 0 for w in weights):
        raise ValueError("Every rubric weight must be greater than zero.")

    total = sum(weights)
    exact = [w / total * HUNDRED for w in weights]
    floored = [e.quantize(CENT, rounding=ROUND_FLOOR) for e in exact]
    leftover_cents = int((HUNDRED - sum(floored)) / CENT)

    order = sorted(range(len(weights)), key=lambda i: exact[i] - floored[i], reverse=True)
    for i in order[:leftover_cents]:
        floored[i] += CENT
    return floored
