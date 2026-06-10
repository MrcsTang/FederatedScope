"""Retention and welfare accounting for governance simulation."""


def clip_probability(value):
    return min(1.0, max(0.0, float(value)))


def diagnose_retention_update(state, decision, signal, cfg):
    """Return next participation probability and exit event."""
    if not cfg.retention_enabled:
        return state.participation_prob, False

    protection_value = cfg.retention_protection_weight * (
        cfg.retention_exit_compensation_weight *
        decision.exit_compensation +
        cfg.retention_relationship_weight * state.relationship_score
    )
    risk_pressure = (
        cfg.retention_risk_weight * state.gamma * max(0.0, 0.5 - signal)
    )
    cost_pressure = cfg.retention_cost_weight * state.cost_k
    participation_delta = cfg.retention_eta * (
        protection_value - risk_pressure - cost_pressure
    )
    next_prob = clip_probability(state.participation_prob +
                                 participation_delta)
    next_prob = max(cfg.min_participation_prob, next_prob)
    exit_event = next_prob < cfg.exit_threshold
    return next_prob, exit_event


def compute_welfare(state, decision, signal, effort_after, cfg):
    """Compute gross and net welfare for one client-round."""
    performance_value = cfg.welfare_signal_weight * signal * effort_after
    retention_value = cfg.welfare_retention_weight * state.participation_prob
    effort_cost = cfg.welfare_cost_weight * state.cost_k * effort_after
    governance_transfer = (
        decision.payment_now +
        decision.payment_deferred +
        decision.exit_compensation
    )
    welfare = performance_value + retention_value - effort_cost
    net_welfare = welfare - governance_transfer
    return welfare, net_welfare
