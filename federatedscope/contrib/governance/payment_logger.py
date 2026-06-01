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
            "avg_credit": 0.0,
            "avg_relationship_score": 0.0,
            "avg_payment_now": 0.0,
            "avg_payment_deferred": 0.0,
            "avg_exit_compensation": 0.0,
            "active_rate": 0.0,
        }

    return {
        "mechanism": records[0].mechanism,
        "n_rounds": len({record.round_id for record in records}),
        "n_clients": len({record.client_id for record in records}),
        "avg_effort": _mean(record.effort_after for record in records),
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
        "active_rate": _mean(1.0 if record.active else 0.0
                             for record in records),
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
