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
    retention_enabled: bool = False
    retention_eta: float = 0.2
    retention_cost_weight: float = 0.02
    retention_risk_weight: float = 1.0
    retention_protection_weight: float = 1.0
    retention_relationship_weight: float = 1.0
    retention_exit_compensation_weight: float = 1.0
    min_participation_prob: float = 0.2
    exit_threshold: float = 0.05
    welfare_signal_weight: float = 1.0
    welfare_retention_weight: float = 0.2
    welfare_cost_weight: float = 0.05

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
        if self.retention_eta < 0:
            raise ValueError("retention_eta cannot be negative")
        if self.retention_cost_weight < 0:
            raise ValueError("retention_cost_weight cannot be negative")
        if self.retention_risk_weight < 0:
            raise ValueError("retention_risk_weight cannot be negative")
        if self.retention_protection_weight < 0:
            raise ValueError(
                "retention_protection_weight cannot be negative"
            )
        if self.retention_relationship_weight < 0:
            raise ValueError(
                "retention_relationship_weight cannot be negative"
            )
        if self.retention_exit_compensation_weight < 0:
            raise ValueError(
                "retention_exit_compensation_weight cannot be negative"
            )
        if not 0 <= self.min_participation_prob <= 1:
            raise ValueError("min_participation_prob must be in [0, 1]")
        if not 0 <= self.exit_threshold <= 1:
            raise ValueError("exit_threshold must be in [0, 1]")
        if self.welfare_cost_weight < 0:
            raise ValueError("welfare_cost_weight cannot be negative")


@dataclass
class ClientGovernanceState:
    client_id: int
    gamma: float
    cost_k: float
    client_group: str = "homogeneous"
    effort: int = 1
    credit: float = 0.0
    relationship_score: float = 0.0
    participation_prob: float = 1.0
    active: bool = True
    exit_round: int = -1
    cumulative_welfare: float = 0.0
    cumulative_net_welfare: float = 0.0
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
    participation_prob: float
    exit_event: bool
    exit_round: int
    client_group: str
    gamma: float
    cost_k: float
    welfare: float
    net_welfare: float
    cumulative_welfare: float
    cumulative_net_welfare: float


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
        from federatedscope.contrib.governance.retention_welfare import (
            compute_welfare,
            diagnose_retention_update,
        )

        round_records = []
        for client_id, state in sorted(self.client_states.items()):
            if not state.active:
                record = self._inactive_record(round_id, state)
                self.records.append(record)
                round_records.append(record)
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
            welfare, net_welfare = compute_welfare(
                state, decision, signal, effort_after, self.cfg
            )
            participation_prob, exit_event = diagnose_retention_update(
                state, decision, signal, self.cfg
            )

            state.effort = effort_after
            state.participation_prob = participation_prob
            if exit_event and state.active:
                state.active = False
                state.exit_round = round_id
            state.cumulative_welfare += welfare
            state.cumulative_net_welfare += net_welfare
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
                participation_prob=state.participation_prob,
                exit_event=exit_event,
                exit_round=state.exit_round,
                client_group=state.client_group,
                gamma=state.gamma,
                cost_k=state.cost_k,
                welfare=welfare,
                net_welfare=net_welfare,
                cumulative_welfare=state.cumulative_welfare,
                cumulative_net_welfare=state.cumulative_net_welfare,
            )
            self.records.append(record)
            round_records.append(record)

        return round_records

    def _inactive_record(self, round_id, state):
        return RoundRecord(
            round_id=round_id,
            client_id=state.client_id,
            mechanism=self.cfg.mechanism,
            signal=state.last_signal,
            effort_before=state.effort,
            effort_after=state.effort,
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=0.0,
            credit=state.credit,
            relationship_score=state.relationship_score,
            realized_reward=0.0,
            outside_option=0.0,
            cost_penalty=0.0,
            raw_effort=float(state.effort),
            rounded_effort=state.effort,
            clipped_by_lower=False,
            clipped_by_upper=False,
            active=False,
            participation_prob=state.participation_prob,
            exit_event=False,
            exit_round=state.exit_round,
            client_group=state.client_group,
            gamma=state.gamma,
            cost_k=state.cost_k,
            welfare=0.0,
            net_welfare=0.0,
            cumulative_welfare=state.cumulative_welfare,
            cumulative_net_welfare=state.cumulative_net_welfare,
        )

    def get_local_update_steps(self, client_id):
        return self.client_states[client_id].effort

    def active_client_ids(self):
        return [
            client_id for client_id, state in self.client_states.items()
            if state.active
        ]

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
