"""FederatedScope integration helpers for governance simulation."""

import os
import random

from federatedscope.contrib.governance.contribution_signal import (
    validation_gain_signal,
)
from federatedscope.contrib.governance.governance_state import (
    ClientGovernanceState,
    GovernanceConfig,
    GovernanceStateManager,
)
from federatedscope.contrib.governance.payment_logger import (
    summarize_records,
    write_records_csv,
    write_summary_json,
)


def is_governance_enabled(cfg):
    return hasattr(cfg, 'governance') and bool(cfg.governance.enabled)


def build_governance_manager(cfg, client_ids):
    gov_cfg = GovernanceConfig(
        mechanism=cfg.governance.mechanism,
        beta=cfg.governance.beta,
        delta=cfg.governance.delta,
        base_payment=cfg.governance.base_payment,
        safeguard_strength=cfg.governance.safeguard_strength,
        exit_compensation=cfg.governance.exit_compensation,
        rel_bonus_fraction=cfg.governance.rel_bonus_fraction,
        now_fraction=cfg.governance.now_fraction,
        min_effort=cfg.governance.min_effort,
        max_effort=cfg.governance.max_effort,
        effort_eta=cfg.governance.effort_eta,
        effort_cost_weight=cfg.governance.effort_cost_weight,
        odrc_exit_compensation_effort_weight=(
            cfg.governance.odrc_exit_compensation_effort_weight
        ),
        retention_enabled=cfg.governance.retention_enabled,
        retention_eta=cfg.governance.retention_eta,
        retention_cost_weight=cfg.governance.retention_cost_weight,
        retention_risk_weight=cfg.governance.retention_risk_weight,
        retention_protection_weight=(
            cfg.governance.retention_protection_weight
        ),
        retention_relationship_weight=(
            cfg.governance.retention_relationship_weight
        ),
        retention_exit_compensation_weight=(
            cfg.governance.retention_exit_compensation_weight
        ),
        min_participation_prob=cfg.governance.min_participation_prob,
        exit_threshold=cfg.governance.exit_threshold,
        welfare_signal_weight=cfg.governance.welfare_signal_weight,
        welfare_retention_weight=cfg.governance.welfare_retention_weight,
        welfare_cost_weight=cfg.governance.welfare_cost_weight,
    )
    client_states = _build_client_states(cfg, client_ids)
    return GovernanceStateManager(client_states=client_states, cfg=gov_cfg)


def _build_client_states(cfg, client_ids):
    rng = random.Random(int(cfg.governance.heterogeneity_seed))
    sorted_client_ids = sorted(int(client_id) for client_id in client_ids)
    states = []

    for client_id in sorted_client_ids:
        if cfg.governance.heterogeneity_enabled:
            gamma = rng.uniform(
                float(cfg.governance.gamma_low),
                float(cfg.governance.gamma_high),
            )
            cost_k = rng.uniform(
                float(cfg.governance.cost_k_low),
                float(cfg.governance.cost_k_high),
            )
            client_group = _client_group(gamma, cost_k, cfg)
        else:
            gamma = float(cfg.governance.gamma)
            cost_k = float(cfg.governance.cost_k)
            client_group = "homogeneous"

        states.append(
            ClientGovernanceState(
                client_id=client_id,
                gamma=gamma,
                cost_k=cost_k,
                client_group=client_group,
                effort=int(cfg.train.local_update_steps),
            )
        )

    return states


def _client_group(gamma, cost_k, cfg):
    gamma_mid = (
        float(cfg.governance.gamma_low) + float(cfg.governance.gamma_high)
    ) / 2.0
    cost_mid = (
        float(cfg.governance.cost_k_low) + float(cfg.governance.cost_k_high)
    ) / 2.0
    gamma_label = "high_gamma" if gamma >= gamma_mid else "low_gamma"
    cost_label = "high_cost" if cost_k >= cost_mid else "low_cost"
    return "{}_{}".format(gamma_label, cost_label)


def pack_model_para_with_governance(model_para, local_update_steps):
    return {
        'model_para': model_para,
        'governance': {
            'local_update_steps': int(local_update_steps),
        },
    }


def unpack_model_para_with_governance(content):
    if isinstance(content, dict) and 'model_para' in content and \
            'governance' in content:
        return content['model_para'], content['governance']
    return content, None


def metric_to_signal(previous_metrics, current_metrics, metric_name, scale):
    previous_value = _get_metric(previous_metrics, metric_name)
    current_value = _get_metric(current_metrics, metric_name)
    if previous_value is None or current_value is None:
        return 0.5
    return validation_gain_signal(previous_value, current_value, scale=scale)


def export_governance_records(manager, outdir):
    if manager is None:
        return
    os.makedirs(outdir, exist_ok=True)
    records = list(manager.records)
    write_records_csv(records, os.path.join(outdir, 'governance_records.csv'))
    write_summary_json(
        summarize_records(records),
        os.path.join(outdir, 'governance_summary.json'),
    )


def _get_metric(metrics, metric_name):
    if metrics is None:
        return None
    if metric_name in metrics:
        return float(metrics[metric_name])
    if not metric_name.startswith(('val_', 'test_', 'train_')):
        val_name = 'val_' + metric_name
        if val_name in metrics:
            return float(metrics[val_name])
    return None
