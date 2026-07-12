"""Payment and protection rules for lightweight governance mechanisms."""

from dataclasses import dataclass

from federatedscope.contrib.governance.governance_state import (
    APPROX_SHAPLEY,
    FORMAL_INSURANCE,
    FORMAL_SAFEGUARD,
    ODRC,
    ODRC_TRIGGERED,
    PAY_BY_VALIDATION_GAIN,
    REPUTATION_ONLY,
    RELATIONAL_CONTRACT,
    SPOT,
)


@dataclass
class PaymentDecision:
    payment_now: float
    payment_deferred: float
    exit_compensation: float
    protected: bool
    relationship_signal: float = 0.0
    formal_triggered: bool = False
    trigger_reason: str = ""


def _low_signal_gap(signal):
    return max(0.0, 0.5 - signal)


def _positive_gain(signal):
    return max(0.0, signal - 0.5)


def _risk_score(state, signal, context, cfg):
    signal_risk = _low_signal_gap(signal)
    participation_risk = max(
        0.0, cfg.trigger_participation_threshold - state.participation_prob
    )
    relationship_risk = max(
        0.0, cfg.trigger_relationship_threshold - state.relationship_score
    )
    collapse_risk = max(
        0.0, cfg.trigger_collapse_active_rate - context["active_rate"]
    )
    specificity_risk = max(0.0, state.gamma)
    cost_risk = max(0.0, state.cost_k - 1.0)
    return (
        signal_risk + participation_risk + relationship_risk +
        collapse_risk + 0.25 * specificity_risk + 0.25 * cost_risk
    )


def _trigger_reason(state, signal, context, cfg):
    reasons = []
    if state.participation_prob < cfg.trigger_participation_threshold:
        reasons.append("low_participation")
    if state.relationship_score < cfg.trigger_relationship_threshold:
        reasons.append("low_relationship")
    if signal < cfg.trigger_signal_threshold:
        reasons.append("low_signal")
    if context["active_rate"] < cfg.trigger_collapse_active_rate:
        reasons.append("active_collapse_risk")
    return "+".join(reasons)


def _triggered_compensation(state, signal, context, cfg):
    reason = _trigger_reason(state, signal, context, cfg)
    if not reason:
        return 0.0, False, ""
    risk = _risk_score(state, signal, context, cfg)
    quasi_rent_proxy = max(signal, state.proxy_signal, 0.0)
    amount = (
        cfg.exit_compensation * cfg.safeguard_strength *
        risk * (1.0 + quasi_rent_proxy)
    )
    amount = min(cfg.triggered_max_compensation, amount)
    return amount, amount > 0.0, reason


def _approx_shapley_payment(state, signal, context, cfg):
    positive = context["positive_margins"].get(state.client_id, 0.0)
    denominator = context["positive_sum"]
    if denominator <= 0:
        return 0.0
    return cfg.approx_shapley_budget * positive / denominator


def apply_mechanism(state, signal, cfg, context=None):
    """Apply one governance mechanism to one client signal."""
    if context is None:
        context = {
            "active_rate": 1.0,
            "positive_margins": {state.client_id: _positive_gain(signal)},
            "positive_sum": _positive_gain(signal),
        }

    if cfg.mechanism == SPOT:
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=0.0,
            protected=False,
            relationship_signal=0.0,
        )

    if cfg.mechanism == FORMAL_SAFEGUARD:
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=cfg.exit_compensation *
            cfg.safeguard_strength * _low_signal_gap(signal),
            protected=True,
            relationship_signal=0.0,
            formal_triggered=_low_signal_gap(signal) > 0.0,
            trigger_reason="low_signal" if _low_signal_gap(signal) > 0.0
            else "",
        )

    if cfg.mechanism == RELATIONAL_CONTRACT:
        rel_reward = cfg.rel_bonus_fraction * signal
        return PaymentDecision(
            payment_now=cfg.now_fraction * rel_reward,
            payment_deferred=(1.0 - cfg.now_fraction) * rel_reward,
            exit_compensation=0.0,
            protected=False,
            relationship_signal=signal,
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
            relationship_signal=signal,
            formal_triggered=formal_part > 0.0,
            trigger_reason="low_signal" if formal_part > 0.0 else "",
        )

    if cfg.mechanism == PAY_BY_VALIDATION_GAIN:
        payment = cfg.pay_gain_fraction * _positive_gain(signal)
        return PaymentDecision(
            payment_now=payment,
            payment_deferred=0.0,
            exit_compensation=0.0,
            protected=False,
            relationship_signal=signal,
        )

    if cfg.mechanism == APPROX_SHAPLEY:
        payment = _approx_shapley_payment(state, signal, context, cfg)
        return PaymentDecision(
            payment_now=payment,
            payment_deferred=0.0,
            exit_compensation=0.0,
            protected=False,
            relationship_signal=signal,
        )

    if cfg.mechanism == REPUTATION_ONLY:
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=0.0,
            protected=False,
            relationship_signal=signal,
        )

    if cfg.mechanism == FORMAL_INSURANCE:
        compensation, triggered, reason = _triggered_compensation(
            state, signal, context, cfg
        )
        return PaymentDecision(
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=compensation,
            protected=triggered,
            relationship_signal=0.0,
            formal_triggered=triggered,
            trigger_reason=reason,
        )

    if cfg.mechanism == ODRC_TRIGGERED:
        rel_reward = cfg.odrc_triggered_rel_bonus_fraction * signal
        compensation, triggered, reason = _triggered_compensation(
            state, signal, context, cfg
        )
        return PaymentDecision(
            payment_now=cfg.now_fraction * rel_reward,
            payment_deferred=(1.0 - cfg.now_fraction) * rel_reward,
            exit_compensation=compensation,
            protected=triggered,
            relationship_signal=signal,
            formal_triggered=triggered,
            trigger_reason=reason,
        )

    raise ValueError("Unknown governance mechanism: {}".format(cfg.mechanism))
