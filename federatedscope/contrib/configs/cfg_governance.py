from federatedscope.core.configs.config import CN
from federatedscope.register import register_config


def extend_governance_cfg(cfg):
    cfg.governance = CN()

    cfg.governance.enabled = False
    cfg.governance.mechanism = 'spot'
    cfg.governance.beta = 0.6
    cfg.governance.delta = 0.7
    cfg.governance.base_payment = 0.1
    cfg.governance.safeguard_strength = 0.4
    cfg.governance.exit_compensation = 0.15
    cfg.governance.rel_bonus_fraction = 0.5
    cfg.governance.now_fraction = 0.2
    cfg.governance.min_effort = 1
    cfg.governance.max_effort = 5
    cfg.governance.effort_eta = 1.0
    cfg.governance.effort_cost_weight = 0.2
    cfg.governance.odrc_exit_compensation_effort_weight = 0.0
    cfg.governance.retention_enabled = False
    cfg.governance.retention_eta = 0.2
    cfg.governance.retention_cost_weight = 0.02
    cfg.governance.retention_risk_weight = 1.0
    cfg.governance.retention_protection_weight = 1.0
    cfg.governance.retention_relationship_weight = 1.0
    cfg.governance.retention_exit_compensation_weight = 1.0
    cfg.governance.min_participation_prob = 0.2
    cfg.governance.exit_threshold = 0.05
    cfg.governance.welfare_signal_weight = 1.0
    cfg.governance.welfare_retention_weight = 0.2
    cfg.governance.welfare_cost_weight = 0.05
    cfg.governance.heterogeneity_enabled = False
    cfg.governance.heterogeneity_seed = 12345
    cfg.governance.gamma_low = 0.2
    cfg.governance.gamma_high = 0.8
    cfg.governance.cost_k_low = 0.8
    cfg.governance.cost_k_high = 1.2
    cfg.governance.gamma = 0.5
    cfg.governance.cost_k = 1.0
    cfg.governance.signal_metric = 'val_acc'
    cfg.governance.signal_scale = 1.0

    cfg.register_cfg_check_fun(assert_governance_cfg)


def assert_governance_cfg(cfg):
    if cfg.governance.mechanism not in [
            'spot', 'formal_safeguard', 'relational_contract', 'odrc'
    ]:
        raise ValueError(
            "cfg.governance.mechanism must be one of "
            "['spot', 'formal_safeguard', 'relational_contract', 'odrc']")
    if cfg.governance.min_effort <= 0:
        raise ValueError("cfg.governance.min_effort must be positive")
    if cfg.governance.max_effort < cfg.governance.min_effort:
        raise ValueError(
            "cfg.governance.max_effort must be no smaller than min_effort")
    if cfg.governance.odrc_exit_compensation_effort_weight < 0:
        raise ValueError(
            "cfg.governance.odrc_exit_compensation_effort_weight must be "
            "non-negative")
    if cfg.governance.retention_eta < 0:
        raise ValueError("cfg.governance.retention_eta must be non-negative")
    if cfg.governance.retention_cost_weight < 0:
        raise ValueError(
            "cfg.governance.retention_cost_weight must be non-negative")
    if cfg.governance.retention_risk_weight < 0:
        raise ValueError(
            "cfg.governance.retention_risk_weight must be non-negative")
    if cfg.governance.retention_protection_weight < 0:
        raise ValueError(
            "cfg.governance.retention_protection_weight must be "
            "non-negative")
    if cfg.governance.retention_relationship_weight < 0:
        raise ValueError(
            "cfg.governance.retention_relationship_weight must be "
            "non-negative")
    if cfg.governance.retention_exit_compensation_weight < 0:
        raise ValueError(
            "cfg.governance.retention_exit_compensation_weight must be "
            "non-negative")
    if not 0 <= cfg.governance.min_participation_prob <= 1:
        raise ValueError(
            "cfg.governance.min_participation_prob must be in [0, 1]")
    if not 0 <= cfg.governance.exit_threshold <= 1:
        raise ValueError("cfg.governance.exit_threshold must be in [0, 1]")
    if cfg.governance.welfare_cost_weight < 0:
        raise ValueError(
            "cfg.governance.welfare_cost_weight must be non-negative")
    if cfg.governance.gamma_low > cfg.governance.gamma_high:
        raise ValueError(
            "cfg.governance.gamma_low must be no larger than gamma_high")
    if cfg.governance.cost_k_low > cfg.governance.cost_k_high:
        raise ValueError(
            "cfg.governance.cost_k_low must be no larger than cost_k_high")


register_config("governance", extend_governance_cfg)
