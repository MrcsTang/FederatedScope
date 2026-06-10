"""Smoke test for the lightweight governance simulation layer."""

import copy

from federatedscope.contrib.governance.governance_state import (
    MECHANISMS,
    ClientGovernanceState,
    GovernanceConfig,
    GovernanceStateManager,
)
from federatedscope.contrib.governance.payment_logger import summarize_records


def run_smoke_test(n_rounds=10):
    base_client_states = [
        ClientGovernanceState(client_id=1, gamma=0.2, cost_k=1.2),
        ClientGovernanceState(client_id=2, gamma=0.5, cost_k=1.0),
        ClientGovernanceState(client_id=3, gamma=0.8, cost_k=0.8),
    ]
    signals = {
        1: 0.7,
        2: 0.5,
        3: 0.3,
    }

    summaries = []
    records_by_mechanism = {}
    for mechanism in MECHANISMS:
        cfg = GovernanceConfig(
            mechanism=mechanism,
            effort_eta=2.0,
            effort_cost_weight=0.1,
        )
        manager = GovernanceStateManager(
            client_states=copy.deepcopy(base_client_states),
            cfg=cfg,
        )
        for round_id in range(n_rounds):
            manager.step(round_id, signals)

        records_by_mechanism[mechanism] = list(manager.records)
        summaries.append(summarize_records(manager.records))

    _assert_mechanism_differences(summaries)
    _assert_retention_and_welfare(base_client_states, signals)
    _assert_retention_stress_channel(base_client_states, signals)
    return summaries, records_by_mechanism


def _summary_by_mechanism(summaries):
    return {summary["mechanism"]: summary for summary in summaries}


def _assert_mechanism_differences(summaries):
    by_mechanism = _summary_by_mechanism(summaries)
    spot = by_mechanism["spot"]
    formal = by_mechanism["formal_safeguard"]
    relational = by_mechanism["relational_contract"]
    odrc = by_mechanism["odrc"]

    assert relational["avg_relationship_score"] > spot[
        "avg_relationship_score"
    ]
    assert odrc["avg_relationship_score"] > formal[
        "avg_relationship_score"
    ]
    assert formal["avg_exit_compensation"] > spot[
        "avg_exit_compensation"
    ]
    assert odrc["avg_exit_compensation"] > relational[
        "avg_exit_compensation"
    ]
    assert odrc["avg_effort"] >= spot["avg_effort"]


def _assert_retention_and_welfare(base_client_states, signals):
    cfg = GovernanceConfig(
        mechanism="odrc",
        retention_enabled=True,
        retention_eta=0.5,
        retention_cost_weight=0.2,
        exit_threshold=0.9,
        min_participation_prob=0.0,
    )
    manager = GovernanceStateManager(
        client_states=copy.deepcopy(base_client_states),
        cfg=cfg,
    )
    for round_id in range(3):
        manager.step(round_id, signals)

    summary = summarize_records(manager.records)
    assert "avg_participation_prob" in summary
    assert "avg_net_welfare" in summary
    assert "group_summary" in summary
    assert summary["avg_participation_prob"] <= 1.0
    assert any(record.exit_event for record in manager.records)


def _assert_retention_stress_channel(base_client_states, signals):
    relational_cfg = GovernanceConfig(
        mechanism="relational_contract",
        retention_enabled=True,
        retention_eta=0.6,
        retention_cost_weight=0.25,
        retention_risk_weight=2.0,
        retention_relationship_weight=0.0,
        retention_exit_compensation_weight=20.0,
        exit_threshold=0.75,
        min_participation_prob=0.0,
    )
    odrc_cfg = GovernanceConfig(
        mechanism="odrc",
        retention_enabled=True,
        retention_eta=0.6,
        retention_cost_weight=0.25,
        retention_risk_weight=2.0,
        retention_relationship_weight=0.0,
        retention_exit_compensation_weight=20.0,
        exit_compensation=1.0,
        safeguard_strength=1.0,
        exit_threshold=0.75,
        min_participation_prob=0.0,
    )
    relational = GovernanceStateManager(
        client_states=copy.deepcopy(base_client_states),
        cfg=relational_cfg,
    )
    odrc = GovernanceStateManager(
        client_states=copy.deepcopy(base_client_states),
        cfg=odrc_cfg,
    )
    for round_id in range(3):
        relational.step(round_id, signals)
        odrc.step(round_id, signals)

    relational_summary = summarize_records(relational.records)
    odrc_summary = summarize_records(odrc.records)
    assert odrc_summary["avg_participation_prob"] > relational_summary[
        "avg_participation_prob"
    ]
    assert odrc_summary["active_rate"] >= relational_summary["active_rate"]


def main():
    summaries, _ = run_smoke_test()
    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()
