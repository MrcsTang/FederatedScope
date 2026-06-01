"""Payment and protection rules for lightweight governance mechanisms."""

from dataclasses import dataclass

from federatedscope.contrib.governance.governance_state import (
    FORMAL_SAFEGUARD,
    ODRC,
    RELATIONAL_CONTRACT,
    SPOT,
)


@dataclass
class PaymentDecision:
    payment_now: float
    payment_deferred: float
    exit_compensation: float
    protected: bool


def _low_signal_gap(signal):
    return max(0.0, 0.5 - signal)


def apply_mechanism(state, signal, cfg):
    """Apply one governance mechanism to one client signal."""
    if cfg.mechanism == SPOT:
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=0.0,
            protected=False,
        )

    if cfg.mechanism == FORMAL_SAFEGUARD:
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=cfg.exit_compensation *
            cfg.safeguard_strength * _low_signal_gap(signal),
            protected=True,
        )

    if cfg.mechanism == RELATIONAL_CONTRACT:
        rel_reward = cfg.rel_bonus_fraction * signal
        return PaymentDecision(
            payment_now=cfg.now_fraction * rel_reward,
            payment_deferred=(1.0 - cfg.now_fraction) * rel_reward,
            exit_compensation=0.0,
            protected=False,
        )

    if cfg.mechanism == ODRC:
        rel_reward = cfg.rel_bonus_fraction * signal
        formal_part = (cfg.exit_compensation * cfg.safeguard_strength *
                       _low_signal_gap(signal))
        return PaymentDecision(
            payment_now=cfg.now_fraction * rel_reward,
            payment_deferred=(1.0 - cfg.now_fraction) * rel_reward,
            exit_compensation=formal_part,
            protected=True,
        )

    raise ValueError("Unknown governance mechanism: {}".format(cfg.mechanism))
