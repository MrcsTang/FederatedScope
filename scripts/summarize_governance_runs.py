"""Summarize FederatedScope governance experiment outputs."""

import argparse
import ast
import csv
import glob
import json
import os
from collections import Counter


MECHANISM_ORDER = [
    "disabled",
    "spot",
    "formal_safeguard",
    "relational_contract",
    "odrc",
]


def _find_run_dirs(exp_root, sub_exp_prefix=None):
    run_dirs = {}
    for path in glob.glob(os.path.join(exp_root, "*_gov_*")):
        mechanism = path.rsplit("_gov_", 1)[1]
        if sub_exp_prefix:
            candidates = sorted(glob.glob(
                os.path.join(path, "{}*".format(sub_exp_prefix))
            ))
        else:
            candidates = sorted(glob.glob(os.path.join(path, "sub_exp_*")))
        if candidates:
            run_dirs[mechanism] = candidates[-1]
        else:
            run_dirs[mechanism] = path
    return run_dirs


def _read_governance_summary(run_dir):
    path = os.path.join(run_dir, "governance_summary.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _format_distribution(counter):
    if not counter:
        return ""
    return ", ".join(
        "{}: {}".format(key, counter[key]) for key in sorted(counter)
    )


def _read_records_summary(run_dir):
    path = os.path.join(run_dir, "governance_records.csv")
    if not os.path.exists(path):
        return {}

    records = []
    with open(path, newline="", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            records.append(row)

    if not records:
        return {}

    rounds = [_to_int(row.get("round_id")) for row in records]
    last_round = max(rounds)
    first_last5_round = max(min(rounds), last_round - 4)
    effort_dist = Counter(
        _to_int(row.get("effort_after")) for row in records
    )
    final_effort_dist = Counter(
        _to_int(row.get("effort_after"))
        for row in records
        if _to_int(row.get("round_id")) == last_round
    )
    final5_effort_dist = Counter(
        _to_int(row.get("effort_after"))
        for row in records
        if _to_int(row.get("round_id")) >= first_last5_round
    )
    total_payment_now = sum(
        _to_float(row.get("payment_now")) for row in records
    )
    total_payment_deferred = sum(
        _to_float(row.get("payment_deferred")) for row in records
    )
    total_exit_compensation = sum(
        _to_float(row.get("exit_compensation")) for row in records
    )
    total_welfare = sum(_to_float(row.get("welfare")) for row in records)
    total_net_welfare = sum(
        _to_float(row.get("net_welfare")) for row in records
    )
    n_records = len(records)

    return {
        "record_count": n_records,
        "total_payment_now": total_payment_now,
        "total_payment_deferred": total_payment_deferred,
        "total_exit_compensation": total_exit_compensation,
        "total_governance_transfer": (
            total_payment_now + total_payment_deferred +
            total_exit_compensation
        ),
        "avg_payment_now": total_payment_now / n_records,
        "avg_payment_deferred": total_payment_deferred / n_records,
        "avg_exit_compensation": total_exit_compensation / n_records,
        "avg_participation_prob": sum(
            _to_float(row.get("participation_prob"), default=1.0)
            for row in records
        ) / n_records,
        "active_rate": sum(
            1.0 if str(row.get("active", "")).lower() == "true" else 0.0
            for row in records
        ) / n_records,
        "exit_rate": sum(
            1.0 if str(row.get("exit_event", "")).lower() == "true"
            else 0.0
            for row in records
        ) / n_records,
        "avg_welfare": total_welfare / n_records,
        "avg_net_welfare": total_net_welfare / n_records,
        "total_welfare": total_welfare,
        "total_net_welfare": total_net_welfare,
        "effort_distribution": _format_distribution(effort_dist),
        "final_round_effort_distribution": _format_distribution(
            final_effort_dist
        ),
        "final5_effort_distribution": _format_distribution(
            final5_effort_dist
        ),
    }


def _read_final_metrics(run_dir):
    path = os.path.join(run_dir, "eval_results.log")
    if not os.path.exists(path):
        return {}
    final_result = None
    with open(path, encoding="utf-8") as file_obj:
        for line in file_obj:
            if "'Role': 'Server #'" in line and "'Round': 'Final'" in line:
                final_result = ast.literal_eval(line.strip())
    if final_result is None:
        return {}
    return final_result.get("Results_raw", {})


def _flatten_metrics(metrics, prefix):
    values = metrics.get(prefix, {})
    return {
        "{}_test_acc".format(prefix): values.get("test_acc", ""),
        "{}_val_acc".format(prefix): values.get("val_acc", ""),
        "{}_test_avg_loss".format(prefix): values.get("test_avg_loss", ""),
        "{}_val_avg_loss".format(prefix): values.get("val_avg_loss", ""),
    }


def build_rows(exp_root, sub_exp_prefix=None):
    run_dirs = _find_run_dirs(exp_root, sub_exp_prefix=sub_exp_prefix)
    rows = []
    for mechanism in MECHANISM_ORDER:
        run_dir = run_dirs.get(mechanism)
        if run_dir is None:
            continue
        governance = _read_governance_summary(run_dir)
        records = _read_records_summary(run_dir)
        metrics = _read_final_metrics(run_dir)
        weighted = _flatten_metrics(metrics, "client_summarized_weighted_avg")
        averaged = _flatten_metrics(metrics, "client_summarized_avg")

        row = {
            "mechanism": mechanism,
            "run_dir": run_dir,
            "n_rounds": governance.get("n_rounds", ""),
            "avg_effort": governance.get("avg_effort", ""),
            "max_effort": governance.get("max_effort", ""),
            "effort_gt_min_rate": governance.get("effort_gt_min_rate", ""),
            "avg_raw_effort": governance.get("avg_raw_effort", ""),
            "avg_credit": governance.get("avg_credit", ""),
            "avg_payment_now": governance.get(
                "avg_payment_now", records.get("avg_payment_now", "")
            ),
            "avg_payment_deferred": governance.get(
                "avg_payment_deferred",
                records.get("avg_payment_deferred", ""),
            ),
            "avg_relationship_score": governance.get(
                "avg_relationship_score", ""
            ),
            "avg_exit_compensation": governance.get(
                "avg_exit_compensation",
                records.get("avg_exit_compensation", ""),
            ),
            "total_payment_now": governance.get(
                "total_payment_now", records.get("total_payment_now", "")
            ),
            "total_payment_deferred": governance.get(
                "total_payment_deferred",
                records.get("total_payment_deferred", ""),
            ),
            "total_exit_compensation": governance.get(
                "total_exit_compensation",
                records.get("total_exit_compensation", ""),
            ),
            "total_governance_transfer": governance.get(
                "total_governance_transfer",
                records.get("total_governance_transfer", ""),
            ),
            "avg_realized_reward": governance.get("avg_realized_reward", ""),
            "avg_outside_option": governance.get("avg_outside_option", ""),
            "avg_cost_penalty": governance.get("avg_cost_penalty", ""),
            "active_rate": governance.get(
                "active_rate", records.get("active_rate", "")
            ),
            "exit_rate": governance.get(
                "exit_rate", records.get("exit_rate", "")
            ),
            "avg_participation_prob": governance.get(
                "avg_participation_prob",
                records.get("avg_participation_prob", ""),
            ),
            "avg_welfare": governance.get(
                "avg_welfare", records.get("avg_welfare", "")
            ),
            "avg_net_welfare": governance.get(
                "avg_net_welfare", records.get("avg_net_welfare", "")
            ),
            "total_welfare": governance.get(
                "total_welfare", records.get("total_welfare", "")
            ),
            "total_net_welfare": governance.get(
                "total_net_welfare", records.get("total_net_welfare", "")
            ),
            "group_summary": json.dumps(
                governance.get("group_summary", {}),
                sort_keys=True,
                separators=(",", ":"),
            ) if governance.get("group_summary") else "",
            "record_count": records.get("record_count", ""),
            "effort_distribution": records.get("effort_distribution", ""),
            "final_round_effort_distribution": records.get(
                "final_round_effort_distribution", ""
            ),
            "final5_effort_distribution": records.get(
                "final5_effort_distribution", ""
            ),
        }
        row.update(weighted)
        row.update(averaged)
        rows.append(row)

    baseline = next(
        (row for row in rows if row.get("mechanism") == "disabled"),
        None,
    )
    if baseline:
        baseline_acc = _to_float(
            baseline.get("client_summarized_weighted_avg_test_acc"),
            default=None,
        )
        baseline_loss = _to_float(
            baseline.get("client_summarized_weighted_avg_test_avg_loss"),
            default=None,
        )
        for row in rows:
            test_acc = _to_float(
                row.get("client_summarized_weighted_avg_test_acc"),
                default=None,
            )
            test_loss = _to_float(
                row.get("client_summarized_weighted_avg_test_avg_loss"),
                default=None,
            )
            row["weighted_test_acc_gain_vs_disabled"] = (
                "" if baseline_acc is None or test_acc is None
                else test_acc - baseline_acc
            )
            row["weighted_test_avg_loss_delta_vs_disabled"] = (
                "" if baseline_loss is None or test_loss is None
                else test_loss - baseline_loss
            )
    return rows


def write_csv(rows, path):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _format_value(value):
    if isinstance(value, float):
        return "{:.6f}".format(value)
    return str(value)


def print_markdown(rows):
    if not rows:
        print("No rows found.")
        return
    columns = [
        "mechanism",
        "n_rounds",
        "avg_effort",
        "max_effort",
        "effort_gt_min_rate",
        "client_summarized_weighted_avg_test_acc",
        "weighted_test_acc_gain_vs_disabled",
        "client_summarized_weighted_avg_val_acc",
        "client_summarized_weighted_avg_test_avg_loss",
        "weighted_test_avg_loss_delta_vs_disabled",
        "client_summarized_weighted_avg_val_avg_loss",
        "avg_credit",
        "avg_payment_now",
        "avg_payment_deferred",
        "avg_exit_compensation",
        "total_governance_transfer",
        "effort_distribution",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        print("| " + " | ".join(_format_value(row.get(column, ""))
                                for column in columns) + " |")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-root", default="exp")
    parser.add_argument("--sub-exp-prefix", default=None)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    rows = build_rows(args.exp_root, sub_exp_prefix=args.sub_exp_prefix)
    if args.csv:
        write_csv(rows, args.csv)
    print_markdown(rows)


if __name__ == "__main__":
    main()
