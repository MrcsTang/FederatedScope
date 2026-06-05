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


register_config("governance", extend_governance_cfg)
