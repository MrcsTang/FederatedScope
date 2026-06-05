"""Parameter sweep for governance effort differentiation."""

import copy
import itertools

from federatedscope.contrib.governance.governance_state import (
    MECHANISMS,
    ClientGovernanceState,
    GovernanceConfig,
    GovernanceStateManager,
)
from federatedscope.contrib.governance.payment_logger import summarize_records


DEFAULT_SIGNALS = [
    {client_id: 0.5 for client_id in range(1, 101)},
    {client_id: 0.62 for client_id in range(1, 101)},
    {client_id: 0.58 for client_id in range(1, 101)},
    {client_id: 0.64 for client_id in range(1, 101)},
    {client_id: 0.60 for client_id in range(1, 101)},
]


def _base_client_states():
    return [
        ClientGovernanceState(
            client_id=client_id,
            gamma=0.5,
            cost_k=1.0,
            effort=1,
        )
        for client_id in range(1, 101)
    ]


def run_mechanism(mechanism, signal_rounds, **cfg_kwargs):
    cfg = GovernanceConfig(mechanism=mechanism, **cfg_kwargs)
    manager = GovernanceStateManager(
        client_states=copy.deepcopy(_base_client_states()),
        cfg=cfg,
    )
    for round_id, signals in enumerate(signal_rounds):
        manager.step(round_id, signals)
    return summarize_records(manager.records), manager.records


def run_all(signal_rounds=DEFAULT_SIGNALS, **cfg_kwargs):
    summaries = []
    records_by_mechanism = {}
    for mechanism in MECHANISMS:
        summary, records = run_mechanism(
            mechanism,
            signal_rounds,
            **cfg_kwargs,
        )
        summaries.append(summary)
        records_by_mechanism[mechanism] = records
    return summaries, records_by_mechanism


def find_candidate_configs(signal_rounds=DEFAULT_SIGNALS, limit=5):
    search_space = {
        "effort_eta": [1.0, 2.0, 3.0, 4.0],
        "effort_cost_weight": [0.02, 0.05, 0.08, 0.1],
        "base_payment": [0.1, 0.2, 0.3],
        "rel_bonus_fraction": [0.5, 0.8, 1.0],
    }
    keys = list(search_space.keys())
    candidates = []
    for values in itertools.product(*(search_space[key] for key in keys)):
        cfg_kwargs = dict(zip(keys, values))
        summaries, _ = run_all(signal_rounds=signal_rounds, **cfg_kwargs)
        by_mechanism = {
            summary["mechanism"]: summary for summary in summaries
        }
        spot = by_mechanism["spot"]
        formal = by_mechanism["formal_safeguard"]
        relational = by_mechanism["relational_contract"]
        odrc = by_mechanism["odrc"]
        if spot["max_effort"] == 1 and formal["max_effort"] == 1 and (
                relational["max_effort"] > 1 or odrc["max_effort"] > 1):
            score = (
                relational["avg_effort"] + odrc["avg_effort"] -
                spot["avg_effort"] - formal["avg_effort"]
            )
            candidates.append((score, cfg_kwargs, summaries))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[:limit]


def _print_summaries(title, cfg_kwargs, summaries):
    print("===== {} =====".format(title))
    print("config={}".format(cfg_kwargs))
    for summary in summaries:
        print(
            "{mechanism}: avg_effort={avg_effort:.3f}, "
            "max_effort={max_effort}, effort_gt_min_rate="
            "{effort_gt_min_rate:.3f}, avg_raw_effort="
            "{avg_raw_effort:.3f}, lower_clip_rate={lower_clip_rate:.3f}".
            format(**summary)
        )
    print()


def main():
    baseline_kwargs = {
        "effort_eta": 1.0,
        "effort_cost_weight": 0.2,
        "base_payment": 0.1,
        "rel_bonus_fraction": 0.5,
    }
    baseline_summaries, _ = run_all(**baseline_kwargs)
    _print_summaries("current smoke calibration", baseline_kwargs,
                     baseline_summaries)

    candidates = find_candidate_configs()
    if not candidates:
        print("No candidate configs found.")
        return

    for idx, (score, cfg_kwargs, summaries) in enumerate(candidates, start=1):
        _print_summaries("candidate {} score={:.3f}".format(idx, score),
                         cfg_kwargs, summaries)


if __name__ == "__main__":
    main()
