"""Effort scheduling rules for governance simulation."""

from dataclasses import dataclass

from federatedscope.contrib.governance.governance_state import ODRC


def _clip(value, lower, upper):
    return max(lower, min(upper, value))


@dataclass
class EffortDiagnostics:
    realized_reward: float
    outside_option: float
    cost_penalty: float
    raw_effort: float
    rounded_effort: int
    clipped_effort: int
    clipped_by_lower: bool
    clipped_by_upper: bool


def diagnose_effort_update(state, decision, cfg):
    """Return the next effort and its economic components."""
    odrc_formal_reward = 0.0
    if cfg.mechanism == ODRC:
        odrc_formal_reward = (
            cfg.odrc_exit_compensation_effort_weight *
            decision.exit_compensation
        )
    realized_reward = (
        cfg.base_payment + decision.payment_now +
        cfg.delta * state.relationship_score +
        odrc_formal_reward
    )
    outside_option = state.gamma * realized_reward
    cost_penalty = cfg.effort_cost_weight * state.cost_k * state.effort
    raw_effort = state.effort + cfg.effort_eta * (
        realized_reward - outside_option - cost_penalty
    )
    rounded_effort = round(raw_effort)
    clipped_effort = int(
        _clip(rounded_effort, cfg.min_effort, cfg.max_effort)
    )
    return EffortDiagnostics(
        realized_reward=realized_reward,
        outside_option=outside_option,
        cost_penalty=cost_penalty,
        raw_effort=raw_effort,
        rounded_effort=int(rounded_effort),
        clipped_effort=clipped_effort,
        clipped_by_lower=rounded_effort < cfg.min_effort,
        clipped_by_upper=rounded_effort > cfg.max_effort,
    )


def update_effort(state, decision, cfg):
    """Map realized reward into the next local update step count."""
    return diagnose_effort_update(state, decision, cfg).clipped_effort
