"""Effort scheduling rules for governance simulation."""


def _clip(value, lower, upper):
    return max(lower, min(upper, value))


def update_effort(state, decision, cfg):
    """Map realized reward into the next local update step count."""
    realized_reward = (
        cfg.base_payment + decision.payment_now +
        cfg.delta * state.relationship_score
    )
    outside_option = state.gamma * realized_reward
    cost_penalty = cfg.effort_cost_weight * state.cost_k * state.effort
    raw_effort = state.effort + cfg.effort_eta * (
        realized_reward - outside_option - cost_penalty
    )
    return int(_clip(round(raw_effort), cfg.min_effort, cfg.max_effort))
