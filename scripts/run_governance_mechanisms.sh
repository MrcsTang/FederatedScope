#!/usr/bin/env bash
set -euo pipefail

TOTAL_ROUNDS="${TOTAL_ROUNDS:-2}"
DATA_SUBSAMPLE="${DATA_SUBSAMPLE:-0.01}"
SAMPLE_CLIENT_RATE="${SAMPLE_CLIENT_RATE:-0.05}"
SAMPLE_CLIENT_NUM="${SAMPLE_CLIENT_NUM:-5}"
BATCH_SIZE="${BATCH_SIZE:-8}"
EVAL_FREQ="${EVAL_FREQ:-1}"
DEVICE="${DEVICE:-0}"
USE_GPU="${USE_GPU:-True}"
COUNT_FLOPS="${COUNT_FLOPS:-False}"
GOV_BASE_PAYMENT="${GOV_BASE_PAYMENT:-0.1}"
GOV_REL_BONUS_FRACTION="${GOV_REL_BONUS_FRACTION:-0.5}"
GOV_EFFORT_ETA="${GOV_EFFORT_ETA:-1.0}"
GOV_EFFORT_COST_WEIGHT="${GOV_EFFORT_COST_WEIGHT:-0.2}"
GOV_SIGNAL_SCALE="${GOV_SIGNAL_SCALE:-1.0}"
GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT="${GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT:-0.0}"

CFG_FILE="${CFG_FILE:-scripts/example_configs/femnist_governance_smoke.yaml}"

usage() {
  cat <<'EOF'
Usage: scripts/run_governance_mechanisms.sh [options]

Options:
  --total-rounds N
  --data-subsample X
  --sample-client-num N
  --batch-size N
  --eval-freq N
  --device ID
  --use-gpu True|False
  --count-flops True|False
  --cfg-file PATH
  --gov-base-payment X
  --gov-rel-bonus-fraction X
  --gov-effort-eta X
  --gov-effort-cost-weight X
  --gov-signal-scale X
  --gov-odrc-exit-comp-effort-weight X
  -h, --help

Environment variables with matching uppercase names are still supported.
Command-line options take precedence over environment variables.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --total-rounds)
      TOTAL_ROUNDS="$2"; shift 2 ;;
    --data-subsample)
      DATA_SUBSAMPLE="$2"; shift 2 ;;
    --sample-client-num)
      SAMPLE_CLIENT_NUM="$2"; shift 2 ;;
    --batch-size)
      BATCH_SIZE="$2"; shift 2 ;;
    --eval-freq)
      EVAL_FREQ="$2"; shift 2 ;;
    --device)
      DEVICE="$2"; shift 2 ;;
    --use-gpu)
      USE_GPU="$2"; shift 2 ;;
    --count-flops)
      COUNT_FLOPS="$2"; shift 2 ;;
    --cfg-file)
      CFG_FILE="$2"; shift 2 ;;
    --gov-base-payment)
      GOV_BASE_PAYMENT="$2"; shift 2 ;;
    --gov-rel-bonus-fraction)
      GOV_REL_BONUS_FRACTION="$2"; shift 2 ;;
    --gov-effort-eta)
      GOV_EFFORT_ETA="$2"; shift 2 ;;
    --gov-effort-cost-weight)
      GOV_EFFORT_COST_WEIGHT="$2"; shift 2 ;;
    --gov-signal-scale)
      GOV_SIGNAL_SCALE="$2"; shift 2 ;;
    --gov-odrc-exit-comp-effort-weight)
      GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

export PYTHONPATH="${PYTHONPATH:-.}"

run_case() {
  local enabled="$1"
  local mechanism="$2"
  local tag="$3"

  echo "===== Running: ${tag} ====="

  python federatedscope/main.py \
    --cfg "${CFG_FILE}" \
    use_gpu "${USE_GPU}" \
    device "${DEVICE}" \
    federate.total_round_num "${TOTAL_ROUNDS}" \
    data.subsample "${DATA_SUBSAMPLE}" \
    federate.sample_client_num "${SAMPLE_CLIENT_NUM}" \
    federate.sample_client_rate -1.0 \
    dataloader.batch_size "${BATCH_SIZE}" \
    eval.freq "${EVAL_FREQ}" \
    eval.count_flops "${COUNT_FLOPS}" \
    governance.enabled "${enabled}" \
    governance.mechanism "${mechanism}" \
    governance.base_payment "${GOV_BASE_PAYMENT}" \
    governance.rel_bonus_fraction "${GOV_REL_BONUS_FRACTION}" \
    governance.effort_eta "${GOV_EFFORT_ETA}" \
    governance.effort_cost_weight "${GOV_EFFORT_COST_WEIGHT}" \
    governance.signal_scale "${GOV_SIGNAL_SCALE}" \
    governance.odrc_exit_compensation_effort_weight \
      "${GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT}" \
    expname_tag "${tag}"

  echo
}

run_case False spot gov_disabled

for mechanism in spot formal_safeguard relational_contract odrc; do
  run_case True "${mechanism}" "gov_${mechanism}"
done

echo "===== Governance summaries ====="
find exp -path "*gov_*" -name governance_summary.json \
  -printf "%TY-%Tm-%Td %TH:%TM %p\n" | sort | tail -n 12
