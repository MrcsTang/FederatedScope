"""Contribution signal helpers for governance simulation."""


def _clip(value, lower, upper):
    return max(lower, min(upper, value))


def validation_gain_signal(before, after, scale=1.0):
    """Map validation improvement to a contribution signal in [0, 1]."""
    raw_gain = after - before
    return _clip(0.5 + scale * raw_gain, 0.0, 1.0)
