"""Round record summaries and lightweight exports."""

import csv
import json
from dataclasses import asdict, fields

from federatedscope.contrib.governance.governance_state import RoundRecord


def _mean(values):
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def summarize_records(records):
    """Summarize governance records across rounds and clients."""
    records = list(records)
    if not records:
        return {
            "mechanism": None,
            "n_rounds": 0,
            "n_clients": 0,
            "avg_effort": 0.0,
            "max_effort": 0,
            "effort_gt_min_rate": 0.0,
            "avg_credit": 0.0,
            "avg_relationship_score": 0.0,
            "avg_payment_now": 0.0,
            "avg_payment_deferred": 0.0,
            "avg_exit_compensation": 0.0,
            "total_payment_now": 0.0,
            "total_payment_deferred": 0.0,
            "total_exit_compensation": 0.0,
            "total_governance_transfer": 0.0,
            "avg_realized_reward": 0.0,
            "avg_outside_option": 0.0,
            "avg_cost_penalty": 0.0,
            "avg_raw_effort": 0.0,
            "lower_clip_rate": 0.0,
            "upper_clip_rate": 0.0,
            "active_rate": 0.0,
            "exit_rate": 0.0,
            "avg_participation_prob": 0.0,
            "avg_welfare": 0.0,
            "avg_net_welfare": 0.0,
            "total_welfare": 0.0,
            "total_net_welfare": 0.0,
            "group_summary": {},
        }

    min_effort = min(record.effort_before for record in records)
    total_payment_now = sum(record.payment_now for record in records)
    total_payment_deferred = sum(
        record.payment_deferred for record in records
    )
    total_exit_compensation = sum(
        record.exit_compensation for record in records
    )
    total_welfare = sum(record.welfare for record in records)
    total_net_welfare = sum(record.net_welfare for record in records)
    summary = {
        "mechanism": records[0].mechanism,
        "n_rounds": len({record.round_id for record in records}),
        "n_clients": len({record.client_id for record in records}),
        "avg_effort": _mean(record.effort_after for record in records),
        "max_effort": max(record.effort_after for record in records),
        "effort_gt_min_rate": _mean(
            1.0 if record.effort_after > min_effort else 0.0
            for record in records
        ),
        "avg_credit": _mean(record.credit for record in records),
        "avg_relationship_score": _mean(
            record.relationship_score for record in records
        ),
        "avg_payment_now": _mean(record.payment_now for record in records),
        "avg_payment_deferred": _mean(
            record.payment_deferred for record in records
        ),
        "avg_exit_compensation": _mean(
            record.exit_compensation for record in records
        ),
        "total_payment_now": total_payment_now,
        "total_payment_deferred": total_payment_deferred,
        "total_exit_compensation": total_exit_compensation,
        "total_governance_transfer": (
            total_payment_now + total_payment_deferred +
            total_exit_compensation
        ),
        "avg_realized_reward": _mean(
            record.realized_reward for record in records
        ),
        "avg_outside_option": _mean(
            record.outside_option for record in records
        ),
        "avg_cost_penalty": _mean(record.cost_penalty for record in records),
        "avg_raw_effort": _mean(record.raw_effort for record in records),
        "lower_clip_rate": _mean(
            1.0 if record.clipped_by_lower else 0.0 for record in records
        ),
        "upper_clip_rate": _mean(
            1.0 if record.clipped_by_upper else 0.0 for record in records
        ),
        "active_rate": _mean(1.0 if record.active else 0.0
                             for record in records),
        "exit_rate": _mean(1.0 if record.exit_event else 0.0
                           for record in records),
        "avg_participation_prob": _mean(
            record.participation_prob for record in records
        ),
        "avg_welfare": _mean(record.welfare for record in records),
        "avg_net_welfare": _mean(record.net_welfare for record in records),
        "total_welfare": total_welfare,
        "total_net_welfare": total_net_welfare,
        "group_summary": _summarize_groups(records),
    }
    return summary


def _summarize_groups(records):
    group_records = {}
    for record in records:
        group_records.setdefault(record.client_group, []).append(record)

    return {
        group: {
            "n_clients": len({record.client_id for record in group_items}),
            "active_rate": _mean(
                1.0 if record.active else 0.0 for record in group_items
            ),
            "exit_rate": _mean(
                1.0 if record.exit_event else 0.0
                for record in group_items
            ),
            "avg_participation_prob": _mean(
                record.participation_prob for record in group_items
            ),
            "avg_effort": _mean(
                record.effort_after for record in group_items
            ),
            "avg_welfare": _mean(
                record.welfare for record in group_items
            ),
            "avg_net_welfare": _mean(
                record.net_welfare for record in group_items
            ),
        }
        for group, group_items in sorted(group_records.items())
    }


def records_to_csv(records, path):
    """Write round records to CSV."""
    fieldnames = [field.name for field in fields(RoundRecord)]
    with open(path, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_records_csv(records, path):
    records_to_csv(records, path)


def write_summary_json(summary, path):
    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump(summary, file_obj, indent=2, sort_keys=True)
        file_obj.write("\n")
