"""State and record management for governance simulation."""

from dataclasses import asdict, dataclass


SPOT = "spot"
FORMAL_SAFEGUARD = "formal_safeguard"
RELATIONAL_CONTRACT = "relational_contract"
ODRC = "odrc"

MECHANISMS = [
    SPOT,
    FORMAL_SAFEGUARD,
    RELATIONAL_CONTRACT,
    ODRC,
]


@dataclass
class GovernanceConfig:
    mechanism: str
    beta: float = 0.6
    delta: float = 0.7
    base_payment: float = 0.1
    safeguard_strength: float = 0.4
    exit_compensation: float = 0.15
    rel_bonus_fraction: float = 0.5
    now_fraction: float = 0.2
    min_effort: int = 1
    max_effort: int = 5
    effort_eta: float = 1.0
    effort_cost_weight: float = 0.2
    odrc_exit_compensation_effort_weight: float = 0.0

    def __post_init__(self):
        if self.mechanism not in MECHANISMS:
            raise ValueError(
                "mechanism must be one of {}, got {!r}".format(
                    MECHANISMS, self.mechanism
                )
            )
        if self.min_effort > self.max_effort:
            raise ValueError("min_effort cannot exceed max_effort")
        if self.odrc_exit_compensation_effort_weight < 0:
            raise ValueError(
                "odrc_exit_compensation_effort_weight cannot be negative"
            )


@dataclass
class ClientGovernanceState:
    client_id: int
    gamma: float
    cost_k: float
    effort: int = 1
    credit: float = 0.0
    relationship_score: float = 0.0
    participation_prob: float = 1.0
    active: bool = True
    last_signal: float = 0.0
    last_payment_now: float = 0.0
    last_payment_deferred: float = 0.0
    last_exit_compensation: float = 0.0


@dataclass
class RoundRecord:
    round_id: int
    client_id: int
    mechanism: str
    signal: float
    effort_before: int
    effort_after: int
    payment_now: float
    payment_deferred: float
    exit_compensation: float
    credit: float
    relationship_score: float
    realized_reward: float
    outside_option: float
    cost_penalty: float
    raw_effort: float
    rounded_effort: int
    clipped_by_lower: bool
    clipped_by_upper: bool
    active: bool


class GovernanceStateManager:
    """Manage client governance state and round-level records."""

    def __init__(self, client_states, cfg):
        self.client_states = {
            state.client_id: state
            for state in client_states
        }
        self.cfg = cfg
        self.records = []

    def step(self, round_id, client_signals):
        from federatedscope.contrib.governance.effort_scheduler import (
            diagnose_effort_update,
        )
        from federatedscope.contrib.governance.mechanism_rules import (
            apply_mechanism,
        )

        round_records = []
        for client_id, state in sorted(self.client_states.items()):
            if not state.active:
                continue

            signal = float(client_signals.get(client_id, state.last_signal))
            effort_before = state.effort
            decision = apply_mechanism(state, signal, self.cfg)

            state.credit += decision.payment_now + decision.exit_compensation
            state.relationship_score = (
                self.cfg.delta * state.relationship_score +
                decision.payment_deferred
            )
            effort_diag = diagnose_effort_update(state, decision, self.cfg)
            effort_after = effort_diag.clipped_effort

            state.effort = effort_after
            state.last_signal = signal
            state.last_payment_now = decision.payment_now
            state.last_payment_deferred = decision.payment_deferred
            state.last_exit_compensation = decision.exit_compensation

            record = RoundRecord(
                round_id=round_id,
                client_id=client_id,
                mechanism=self.cfg.mechanism,
                signal=signal,
                effort_before=effort_before,
                effort_after=effort_after,
                payment_now=decision.payment_now,
                payment_deferred=decision.payment_deferred,
                exit_compensation=decision.exit_compensation,
                credit=state.credit,
                relationship_score=state.relationship_score,
                realized_reward=effort_diag.realized_reward,
                outside_option=effort_diag.outside_option,
                cost_penalty=effort_diag.cost_penalty,
                raw_effort=effort_diag.raw_effort,
                rounded_effort=effort_diag.rounded_effort,
                clipped_by_lower=effort_diag.clipped_by_lower,
                clipped_by_upper=effort_diag.clipped_by_upper,
                active=state.active,
            )
            self.records.append(record)
            round_records.append(record)

        return round_records

    def get_local_update_steps(self, client_id):
        return self.client_states[client_id].effort

    def to_dicts(self):
        return [asdict(record) for record in self.records]

    def to_dataframe(self):
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "pandas is required for GovernanceStateManager.to_dataframe()"
            ) from exc
        return pd.DataFrame(self.to_dicts())
