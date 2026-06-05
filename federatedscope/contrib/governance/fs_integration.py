"""FederatedScope integration helpers for governance simulation."""

import os

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
    )
    client_states = [
        ClientGovernanceState(
            client_id=int(client_id),
            gamma=cfg.governance.gamma,
            cost_k=cfg.governance.cost_k,
            effort=int(cfg.train.local_update_steps),
        ) for client_id in client_ids
    ]
    return GovernanceStateManager(client_states=client_states, cfg=gov_cfg)


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
