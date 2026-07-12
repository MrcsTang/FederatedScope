"""State and record management for governance simulation."""

from dataclasses import asdict, dataclass


SPOT = "spot"
FORMAL_SAFEGUARD = "formal_safeguard"
RELATIONAL_CONTRACT = "relational_contract"
ODRC = "odrc"
PAY_BY_VALIDATION_GAIN = "pay_by_validation_gain"
APPROX_SHAPLEY = "approx_shapley"
REPUTATION_ONLY = "reputation_only"
FORMAL_INSURANCE = "formal_insurance"
ODRC_TRIGGERED = "odrc_triggered"

MECHANISMS = [
    SPOT,
    FORMAL_SAFEGUARD,
    RELATIONAL_CONTRACT,
    ODRC,
    PAY_BY_VALIDATION_GAIN,
    APPROX_SHAPLEY,
    REPUTATION_ONLY,
    FORMAL_INSURANCE,
    ODRC_TRIGGERED,
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
    odrc_triggered_rel_bonus_fraction: float = -1.0
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
    proxy_ema_lambda: float = 0.7
    full_eval_interval: int = 0
    pay_gain_fraction: float = 0.5
    approx_shapley_budget: float = 0.5
    trigger_participation_threshold: float = 0.35
    trigger_relationship_threshold: float = 0.1
    trigger_signal_threshold: float = 0.35
    trigger_collapse_active_rate: float = 0.7
    formal_budget_cap: float = 0.0
    total_budget_cap: float = 0.0
    triggered_max_compensation: float = 1.0

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
        if not 0 <= self.proxy_ema_lambda <= 1:
            raise ValueError("proxy_ema_lambda must be in [0, 1]")
        if self.full_eval_interval < 0:
            raise ValueError("full_eval_interval cannot be negative")
        if self.pay_gain_fraction < 0:
            raise ValueError("pay_gain_fraction cannot be negative")
        if self.approx_shapley_budget < 0:
            raise ValueError("approx_shapley_budget cannot be negative")
        if not 0 <= self.trigger_participation_threshold <= 1:
            raise ValueError(
                "trigger_participation_threshold must be in [0, 1]"
            )
        if self.trigger_relationship_threshold < 0:
            raise ValueError(
                "trigger_relationship_threshold cannot be negative"
            )
        if not 0 <= self.trigger_signal_threshold <= 1:
            raise ValueError("trigger_signal_threshold must be in [0, 1]")
        if not 0 <= self.trigger_collapse_active_rate <= 1:
            raise ValueError("trigger_collapse_active_rate must be in [0, 1]")
        if self.formal_budget_cap < 0:
            raise ValueError("formal_budget_cap cannot be negative")
        if self.total_budget_cap < 0:
            raise ValueError("total_budget_cap cannot be negative")
        if self.triggered_max_compensation < 0:
            raise ValueError("triggered_max_compensation cannot be negative")
        if self.odrc_triggered_rel_bonus_fraction < 0:
            self.odrc_triggered_rel_bonus_fraction = self.rel_bonus_fraction


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
    proxy_signal: float = 0.5
    last_full_eval_signal: float = 0.5
    last_payment_now: float = 0.0
    last_payment_deferred: float = 0.0
    last_exit_compensation: float = 0.0


@dataclass
class RoundRecord:
    round_id: int
    client_id: int
    mechanism: str
    signal: float
    proxy_signal: float
    full_eval_signal: float
    effort_before: int
    effort_after: int
    payment_now: float
    payment_deferred: float
    exit_compensation: float
    formal_triggered: bool
    trigger_reason: str
    formal_budget_used: float
    total_budget_used: float
    formal_budget_remaining: float
    total_budget_remaining: float
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
        self.formal_budget_used = 0.0
        self.total_budget_used = 0.0

    def step(self, round_id, client_signals, full_eval_signals=None):
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
        signal_stats = self._signal_stats(client_signals)
        context = self._round_context(signal_stats)
        full_eval_signals = full_eval_signals or {}
        for client_id, state in sorted(self.client_states.items()):
            if not state.active:
                record = self._inactive_record(round_id, state)
                self.records.append(record)
                round_records.append(record)
                continue

            signal = float(client_signals.get(client_id, state.last_signal))
            full_eval_signal = full_eval_signals.get(client_id)
            if full_eval_signal is not None:
                full_eval_signal = float(full_eval_signal)
            proxy_signal = self._update_proxy_signal(
                state, signal, round_id, full_eval_signal=full_eval_signal
            )
            effort_before = state.effort
            decision = apply_mechanism(
                state, signal, self.cfg, context=context
            )
            decision = self._apply_budget_caps(decision)

            state.credit += decision.payment_now + decision.exit_compensation
            relationship_signal = decision.relationship_signal
            state.relationship_score = self._update_relationship_score(
                state, relationship_signal, decision.payment_deferred
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
            state.proxy_signal = proxy_signal
            state.last_payment_now = decision.payment_now
            state.last_payment_deferred = decision.payment_deferred
            state.last_exit_compensation = decision.exit_compensation

            record = RoundRecord(
                round_id=round_id,
                client_id=client_id,
                mechanism=self.cfg.mechanism,
                signal=signal,
                proxy_signal=proxy_signal,
                full_eval_signal=state.last_full_eval_signal,
                effort_before=effort_before,
                effort_after=effort_after,
                payment_now=decision.payment_now,
                payment_deferred=decision.payment_deferred,
                exit_compensation=decision.exit_compensation,
                formal_triggered=decision.formal_triggered,
                trigger_reason=decision.trigger_reason,
                formal_budget_used=self.formal_budget_used,
                total_budget_used=self.total_budget_used,
                formal_budget_remaining=self._record_budget_value(
                    self._remaining_formal_budget()
                ),
                total_budget_remaining=self._record_budget_value(
                    self._remaining_total_budget()
                ),
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

    def _signal_stats(self, client_signals):
        positive = {
            client_id: max(0.0, float(signal) - 0.5)
            for client_id, signal in client_signals.items()
        }
        positive_sum = sum(positive.values())
        return {
            "positive_margins": positive,
            "positive_sum": positive_sum,
        }

    def _round_context(self, signal_stats):
        active_count = len(self.active_client_ids())
        total_count = max(len(self.client_states), 1)
        active_rate = active_count / total_count
        return {
            "active_rate": active_rate,
            "formal_budget_remaining": self._remaining_formal_budget(),
            "total_budget_remaining": self._remaining_total_budget(),
            "positive_margins": signal_stats["positive_margins"],
            "positive_sum": signal_stats["positive_sum"],
        }

    def _update_proxy_signal(
        self, state, signal, round_id, full_eval_signal=None
    ):
        full_eval_round = (
            self.cfg.full_eval_interval > 0 and
            round_id % self.cfg.full_eval_interval == 0
        )
        if full_eval_round and full_eval_signal is None:
            full_eval_signal = signal
        if full_eval_signal is not None:
            state.last_full_eval_signal = full_eval_signal
        proxy_signal = (
            self.cfg.proxy_ema_lambda * state.proxy_signal +
            (1.0 - self.cfg.proxy_ema_lambda) * signal
        )
        if full_eval_signal is not None:
            proxy_signal = 0.5 * proxy_signal + 0.5 * full_eval_signal
        state.proxy_signal = proxy_signal
        return proxy_signal

    def _update_relationship_score(
        self, state, relationship_signal, payment_deferred
    ):
        if self.cfg.mechanism in (
            SPOT,
            FORMAL_SAFEGUARD,
            RELATIONAL_CONTRACT,
            ODRC,
        ):
            return self.cfg.delta * state.relationship_score + \
                payment_deferred

        score_from_signal = (
            self.cfg.proxy_ema_lambda * state.relationship_score +
            (1.0 - self.cfg.proxy_ema_lambda) * relationship_signal
        )
        return self.cfg.delta * score_from_signal + payment_deferred

    def _apply_budget_caps(self, decision):
        payment_total = decision.payment_now + decision.payment_deferred
        exit_comp = decision.exit_compensation
        if exit_comp > 0:
            formal_remaining = self._remaining_formal_budget()
            total_remaining = self._remaining_total_budget() - payment_total
            if formal_remaining >= 0:
                exit_comp = min(exit_comp, formal_remaining)
            if total_remaining >= 0:
                exit_comp = min(exit_comp, total_remaining)
            exit_comp = max(0.0, exit_comp)

        total_transfer = payment_total + exit_comp
        if total_transfer > 0:
            total_remaining = self._remaining_total_budget()
            if total_remaining >= 0 and total_transfer > total_remaining:
                scale = total_remaining / total_transfer
                payment_now = decision.payment_now * scale
                payment_deferred = decision.payment_deferred * scale
                exit_comp = exit_comp * scale
            else:
                payment_now = decision.payment_now
                payment_deferred = decision.payment_deferred
        else:
            payment_now = decision.payment_now
            payment_deferred = decision.payment_deferred

        self.formal_budget_used += exit_comp
        self.total_budget_used += payment_now + payment_deferred + exit_comp
        decision.payment_now = payment_now
        decision.payment_deferred = payment_deferred
        decision.exit_compensation = exit_comp
        if decision.protected and exit_comp <= 0:
            decision.formal_triggered = False
        return decision

    def _remaining_formal_budget(self):
        if self.cfg.formal_budget_cap <= 0:
            return float("inf")
        return max(0.0, self.cfg.formal_budget_cap - self.formal_budget_used)

    def _remaining_total_budget(self):
        if self.cfg.total_budget_cap <= 0:
            return float("inf")
        return max(0.0, self.cfg.total_budget_cap - self.total_budget_used)

    def _record_budget_value(self, value):
        return -1.0 if value == float("inf") else value

    def _inactive_record(self, round_id, state):
        return RoundRecord(
            round_id=round_id,
            client_id=state.client_id,
            mechanism=self.cfg.mechanism,
            signal=state.last_signal,
            proxy_signal=state.proxy_signal,
            full_eval_signal=state.last_full_eval_signal,
            effort_before=state.effort,
            effort_after=state.effort,
            payment_now=0.0,
            payment_deferred=0.0,
            exit_compensation=0.0,
            formal_triggered=False,
            trigger_reason="inactive",
            formal_budget_used=self.formal_budget_used,
            total_budget_used=self.total_budget_used,
            formal_budget_remaining=self._record_budget_value(
                self._remaining_formal_budget()
            ),
            total_budget_remaining=self._record_budget_value(
                self._remaining_total_budget()
            ),
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
