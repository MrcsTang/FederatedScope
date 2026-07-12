import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..",
)))

from federatedscope.contrib.governance.calibrate_effort import run_all
from federatedscope.contrib.governance.governance_state import (
    ClientGovernanceState,
    GovernanceConfig,
    GovernanceStateManager,
)
from federatedscope.contrib.governance.fs_integration import (
    pack_model_para_with_governance,
    unpack_model_para_with_governance,
)
from federatedscope.contrib.governance.payment_logger import (
    write_records_csv,
    write_summary_json,
)
from scripts.summarize_governance_runs import build_rows


def test_calibrated_effort_differentiates_mechanisms():
    summaries, _ = run_all(
        effort_eta=3.0,
        effort_cost_weight=0.05,
        base_payment=0.1,
        rel_bonus_fraction=0.8,
    )
    by_mechanism = {summary["mechanism"]: summary for summary in summaries}

    assert by_mechanism["spot"]["max_effort"] == 1
    assert by_mechanism["formal_safeguard"]["max_effort"] == 1
    assert by_mechanism["relational_contract"]["max_effort"] > 1
    assert by_mechanism["odrc"]["max_effort"] > 1
    assert by_mechanism["odrc"]["effort_gt_min_rate"] > 0


def test_governance_payload_carries_local_update_steps():
    content = pack_model_para_with_governance({"weight": 1.0}, 3)
    model_para, governance_payload = unpack_model_para_with_governance(
        content
    )

    assert model_para == {"weight": 1.0}
    assert governance_payload["local_update_steps"] == 3


def test_odrc_exit_compensation_effort_channel_is_default_off():
    low_signals = [{client_id: 0.0 for client_id in range(1, 101)}]
    summaries, _ = run_all(
        signal_rounds=low_signals,
        effort_eta=20.0,
        effort_cost_weight=0.05,
        base_payment=0.1,
        rel_bonus_fraction=0.8,
    )
    by_mechanism = {summary["mechanism"]: summary for summary in summaries}

    assert by_mechanism["relational_contract"]["avg_effort"] == 1.0
    assert by_mechanism["odrc"]["avg_effort"] == 1.0
    assert by_mechanism["odrc"]["avg_exit_compensation"] > 0


def test_odrc_exit_compensation_effort_channel_can_change_effort():
    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    cfg = GovernanceConfig(
        mechanism="odrc",
        effort_eta=20.0,
        effort_cost_weight=0.05,
        base_payment=0.1,
        rel_bonus_fraction=0.8,
        odrc_exit_compensation_effort_weight=10.0,
    )
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    records = manager.step(round_id=0, client_signals={1: 0.0})

    assert records[0].exit_compensation > 0
    assert records[0].effort_after > 1
    assert records[0].realized_reward > cfg.base_payment


def test_triggered_budgeted_odrc_respects_formal_budget():
    states = [
        ClientGovernanceState(client_id=1, gamma=0.8, cost_k=1.2, effort=1),
        ClientGovernanceState(client_id=2, gamma=0.8, cost_k=1.2, effort=1),
    ]
    cfg = GovernanceConfig(
        mechanism="odrc_triggered",
        retention_enabled=True,
        rel_bonus_fraction=0.8,
        exit_compensation=1.0,
        safeguard_strength=1.0,
        trigger_signal_threshold=0.45,
        triggered_max_compensation=10.0,
        formal_budget_cap=0.5,
    )
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    records = manager.step(round_id=0, client_signals={1: 0.0, 2: 0.0})

    assert sum(record.exit_compensation for record in records) <= 0.5
    assert any(record.formal_triggered for record in records)
    assert max(record.formal_budget_used for record in records) <= 0.5


def test_triggered_odrc_defaults_to_shared_rel_bonus_fraction():
    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    cfg = GovernanceConfig(
        mechanism="odrc_triggered",
        rel_bonus_fraction=0.8,
        triggered_max_compensation=0.0,
    )
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    records = manager.step(round_id=0, client_signals={1: 0.5})

    assert cfg.odrc_triggered_rel_bonus_fraction == 0.8
    assert records[0].payment_now == pytest.approx(0.08)
    assert records[0].payment_deferred == pytest.approx(0.32)


def test_triggered_odrc_rel_bonus_can_be_decoupled_from_continuous_odrc():
    signal = 0.5
    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    triggered_cfg = GovernanceConfig(
        mechanism="odrc_triggered",
        rel_bonus_fraction=0.2,
        odrc_triggered_rel_bonus_fraction=0.6,
        triggered_max_compensation=0.0,
    )
    triggered = GovernanceStateManager(
        client_states=states, cfg=triggered_cfg
    )
    triggered_records = triggered.step(round_id=0, client_signals={1: signal})

    odrc_states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    odrc_cfg = GovernanceConfig(
        mechanism="odrc",
        rel_bonus_fraction=0.2,
        triggered_max_compensation=0.0,
    )
    continuous = GovernanceStateManager(
        client_states=odrc_states, cfg=odrc_cfg
    )
    odrc_records = continuous.step(round_id=0, client_signals={1: signal})

    assert triggered_records[0].payment_now == pytest.approx(0.06)
    assert triggered_records[0].payment_deferred == pytest.approx(0.24)
    assert odrc_records[0].payment_now == pytest.approx(0.02)
    assert odrc_records[0].payment_deferred == pytest.approx(0.08)


def test_approx_shapley_allocates_round_budget_to_positive_gain():
    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
        ClientGovernanceState(client_id=2, gamma=0.5, cost_k=1.0, effort=1),
    ]
    cfg = GovernanceConfig(
        mechanism="approx_shapley",
        approx_shapley_budget=1.0,
    )
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    records = manager.step(round_id=0, client_signals={1: 0.7, 2: 0.5})
    by_client = {record.client_id: record for record in records}

    assert by_client[1].payment_now == 1.0
    assert by_client[2].payment_now == 0.0
    assert sum(record.payment_now for record in records) == 1.0


def test_reputation_only_updates_relationship_without_transfer():
    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    cfg = GovernanceConfig(mechanism="reputation_only")
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    records = manager.step(round_id=0, client_signals={1: 0.8})

    assert records[0].relationship_score > 0.0
    assert records[0].payment_now == 0.0
    assert records[0].payment_deferred == 0.0
    assert records[0].exit_compensation == 0.0


def test_summary_exporter_reports_cost_benefit_fields(tmp_path):
    exp_root = Path(tmp_path)
    run_root = exp_root / "FedAvg_convnet2_on_femnist_lr0.01_lstep1_gov_odrc"
    run_dir = run_root / "sub_exp_20260604000000"
    run_dir.mkdir(parents=True)

    states = [
        ClientGovernanceState(client_id=1, gamma=0.5, cost_k=1.0, effort=1),
    ]
    cfg = GovernanceConfig(
        mechanism="odrc",
        effort_eta=20.0,
        effort_cost_weight=0.05,
        base_payment=0.1,
        rel_bonus_fraction=0.8,
        odrc_exit_compensation_effort_weight=10.0,
    )
    manager = GovernanceStateManager(client_states=states, cfg=cfg)
    manager.step(round_id=0, client_signals={1: 0.0})

    write_records_csv(manager.records, str(run_dir / "governance_records.csv"))
    write_summary_json({}, str(run_dir / "governance_summary.json"))
    rows = build_rows(str(exp_root))

    assert len(rows) == 1
    assert rows[0]["mechanism"] == "odrc"
    assert rows[0]["total_exit_compensation"] > 0
    assert rows[0]["total_governance_transfer"] > 0
    assert rows[0]["effort_distribution"] == "4: 1"
