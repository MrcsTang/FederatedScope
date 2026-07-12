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
GOV_SAFEGUARD_STRENGTH="${GOV_SAFEGUARD_STRENGTH:-0.4}"
GOV_EXIT_COMPENSATION="${GOV_EXIT_COMPENSATION:-0.15}"
GOV_REL_BONUS_FRACTION="${GOV_REL_BONUS_FRACTION:-0.5}"
GOV_ODRC_TRIGGERED_REL_BONUS_FRACTION="${GOV_ODRC_TRIGGERED_REL_BONUS_FRACTION:--1.0}"
GOV_EFFORT_ETA="${GOV_EFFORT_ETA:-1.0}"
GOV_EFFORT_COST_WEIGHT="${GOV_EFFORT_COST_WEIGHT:-0.2}"
GOV_SIGNAL_SCALE="${GOV_SIGNAL_SCALE:-1.0}"
GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT="${GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT:-0.0}"
GOV_RETENTION_ENABLED="${GOV_RETENTION_ENABLED:-False}"
GOV_RETENTION_ETA="${GOV_RETENTION_ETA:-0.2}"
GOV_RETENTION_COST_WEIGHT="${GOV_RETENTION_COST_WEIGHT:-0.02}"
GOV_RETENTION_RISK_WEIGHT="${GOV_RETENTION_RISK_WEIGHT:-1.0}"
GOV_RETENTION_PROTECTION_WEIGHT="${GOV_RETENTION_PROTECTION_WEIGHT:-1.0}"
GOV_RETENTION_RELATIONSHIP_WEIGHT="${GOV_RETENTION_RELATIONSHIP_WEIGHT:-1.0}"
GOV_RETENTION_EXIT_COMP_WEIGHT="${GOV_RETENTION_EXIT_COMP_WEIGHT:-1.0}"
GOV_MIN_PARTICIPATION_PROB="${GOV_MIN_PARTICIPATION_PROB:-0.2}"
GOV_EXIT_THRESHOLD="${GOV_EXIT_THRESHOLD:-0.05}"
GOV_WELFARE_SIGNAL_WEIGHT="${GOV_WELFARE_SIGNAL_WEIGHT:-1.0}"
GOV_WELFARE_RETENTION_WEIGHT="${GOV_WELFARE_RETENTION_WEIGHT:-0.2}"
GOV_WELFARE_COST_WEIGHT="${GOV_WELFARE_COST_WEIGHT:-0.05}"
GOV_PROXY_EMA_LAMBDA="${GOV_PROXY_EMA_LAMBDA:-0.7}"
GOV_FULL_EVAL_INTERVAL="${GOV_FULL_EVAL_INTERVAL:-0}"
GOV_FULL_EVAL_SIGNAL_METRIC="${GOV_FULL_EVAL_SIGNAL_METRIC:-}"
GOV_FULL_EVAL_SIGNAL_SCALE="${GOV_FULL_EVAL_SIGNAL_SCALE:-1.0}"
GOV_PAY_GAIN_FRACTION="${GOV_PAY_GAIN_FRACTION:-0.5}"
GOV_APPROX_SHAPLEY_BUDGET="${GOV_APPROX_SHAPLEY_BUDGET:-0.5}"
GOV_TRIGGER_PARTICIPATION_THRESHOLD="${GOV_TRIGGER_PARTICIPATION_THRESHOLD:-0.35}"
GOV_TRIGGER_RELATIONSHIP_THRESHOLD="${GOV_TRIGGER_RELATIONSHIP_THRESHOLD:-0.1}"
GOV_TRIGGER_SIGNAL_THRESHOLD="${GOV_TRIGGER_SIGNAL_THRESHOLD:-0.35}"
GOV_TRIGGER_COLLAPSE_ACTIVE_RATE="${GOV_TRIGGER_COLLAPSE_ACTIVE_RATE:-0.7}"
GOV_FORMAL_BUDGET_CAP="${GOV_FORMAL_BUDGET_CAP:-0.0}"
GOV_TOTAL_BUDGET_CAP="${GOV_TOTAL_BUDGET_CAP:-0.0}"
GOV_TRIGGERED_MAX_COMPENSATION="${GOV_TRIGGERED_MAX_COMPENSATION:-1.0}"
GOV_HETEROGENEITY_ENABLED="${GOV_HETEROGENEITY_ENABLED:-False}"
GOV_HETEROGENEITY_SEED="${GOV_HETEROGENEITY_SEED:-12345}"
GOV_GAMMA_LOW="${GOV_GAMMA_LOW:-0.2}"
GOV_GAMMA_HIGH="${GOV_GAMMA_HIGH:-0.8}"
GOV_COST_K_LOW="${GOV_COST_K_LOW:-0.8}"
GOV_COST_K_HIGH="${GOV_COST_K_HIGH:-1.2}"
GOV_MECHANISMS="${GOV_MECHANISMS:-spot formal_safeguard relational_contract odrc}"

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
  --gov-safeguard-strength X
  --gov-exit-compensation X
  --gov-rel-bonus-fraction X
  --gov-odrc-triggered-rel-bonus-fraction X
  --gov-effort-eta X
  --gov-effort-cost-weight X
  --gov-signal-scale X
  --gov-odrc-exit-comp-effort-weight X
  --gov-retention-enabled True|False
  --gov-retention-eta X
  --gov-retention-cost-weight X
  --gov-retention-risk-weight X
  --gov-retention-protection-weight X
  --gov-retention-relationship-weight X
  --gov-retention-exit-comp-weight X
  --gov-min-participation-prob X
  --gov-exit-threshold X
  --gov-welfare-signal-weight X
  --gov-welfare-retention-weight X
  --gov-welfare-cost-weight X
  --gov-proxy-ema-lambda X
  --gov-full-eval-interval N
  --gov-full-eval-signal-metric NAME
  --gov-full-eval-signal-scale X
  --gov-pay-gain-fraction X
  --gov-approx-shapley-budget X
  --gov-trigger-participation-threshold X
  --gov-trigger-relationship-threshold X
  --gov-trigger-signal-threshold X
  --gov-trigger-collapse-active-rate X
  --gov-formal-budget-cap X
  --gov-total-budget-cap X
  --gov-triggered-max-compensation X
  --gov-heterogeneity-enabled True|False
  --gov-heterogeneity-seed N
  --gov-gamma-low X
  --gov-gamma-high X
  --gov-cost-k-low X
  --gov-cost-k-high X
  --gov-mechanisms "spot relational_contract odrc_triggered"
  -h, --help

Environment variables with matching uppercase names are still supported.
Command-line options take precedence over environment variables.
Use --gov-mechanisms odrc_v2 to run the fixed expanded comparison set.
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
    --gov-safeguard-strength)
      GOV_SAFEGUARD_STRENGTH="$2"; shift 2 ;;
    --gov-exit-compensation)
      GOV_EXIT_COMPENSATION="$2"; shift 2 ;;
    --gov-rel-bonus-fraction)
      GOV_REL_BONUS_FRACTION="$2"; shift 2 ;;
    --gov-odrc-triggered-rel-bonus-fraction)
      GOV_ODRC_TRIGGERED_REL_BONUS_FRACTION="$2"; shift 2 ;;
    --gov-effort-eta)
      GOV_EFFORT_ETA="$2"; shift 2 ;;
    --gov-effort-cost-weight)
      GOV_EFFORT_COST_WEIGHT="$2"; shift 2 ;;
    --gov-signal-scale)
      GOV_SIGNAL_SCALE="$2"; shift 2 ;;
    --gov-odrc-exit-comp-effort-weight)
      GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT="$2"; shift 2 ;;
    --gov-retention-enabled)
      GOV_RETENTION_ENABLED="$2"; shift 2 ;;
    --gov-retention-eta)
      GOV_RETENTION_ETA="$2"; shift 2 ;;
    --gov-retention-cost-weight)
      GOV_RETENTION_COST_WEIGHT="$2"; shift 2 ;;
    --gov-retention-risk-weight)
      GOV_RETENTION_RISK_WEIGHT="$2"; shift 2 ;;
    --gov-retention-protection-weight)
      GOV_RETENTION_PROTECTION_WEIGHT="$2"; shift 2 ;;
    --gov-retention-relationship-weight)
      GOV_RETENTION_RELATIONSHIP_WEIGHT="$2"; shift 2 ;;
    --gov-retention-exit-comp-weight)
      GOV_RETENTION_EXIT_COMP_WEIGHT="$2"; shift 2 ;;
    --gov-min-participation-prob)
      GOV_MIN_PARTICIPATION_PROB="$2"; shift 2 ;;
    --gov-exit-threshold)
      GOV_EXIT_THRESHOLD="$2"; shift 2 ;;
    --gov-welfare-signal-weight)
      GOV_WELFARE_SIGNAL_WEIGHT="$2"; shift 2 ;;
    --gov-welfare-retention-weight)
      GOV_WELFARE_RETENTION_WEIGHT="$2"; shift 2 ;;
    --gov-welfare-cost-weight)
      GOV_WELFARE_COST_WEIGHT="$2"; shift 2 ;;
    --gov-proxy-ema-lambda)
      GOV_PROXY_EMA_LAMBDA="$2"; shift 2 ;;
    --gov-full-eval-interval)
      GOV_FULL_EVAL_INTERVAL="$2"; shift 2 ;;
    --gov-full-eval-signal-metric)
      GOV_FULL_EVAL_SIGNAL_METRIC="$2"; shift 2 ;;
    --gov-full-eval-signal-scale)
      GOV_FULL_EVAL_SIGNAL_SCALE="$2"; shift 2 ;;
    --gov-pay-gain-fraction)
      GOV_PAY_GAIN_FRACTION="$2"; shift 2 ;;
    --gov-approx-shapley-budget)
      GOV_APPROX_SHAPLEY_BUDGET="$2"; shift 2 ;;
    --gov-trigger-participation-threshold)
      GOV_TRIGGER_PARTICIPATION_THRESHOLD="$2"; shift 2 ;;
    --gov-trigger-relationship-threshold)
      GOV_TRIGGER_RELATIONSHIP_THRESHOLD="$2"; shift 2 ;;
    --gov-trigger-signal-threshold)
      GOV_TRIGGER_SIGNAL_THRESHOLD="$2"; shift 2 ;;
    --gov-trigger-collapse-active-rate)
      GOV_TRIGGER_COLLAPSE_ACTIVE_RATE="$2"; shift 2 ;;
    --gov-formal-budget-cap)
      GOV_FORMAL_BUDGET_CAP="$2"; shift 2 ;;
    --gov-total-budget-cap)
      GOV_TOTAL_BUDGET_CAP="$2"; shift 2 ;;
    --gov-triggered-max-compensation)
      GOV_TRIGGERED_MAX_COMPENSATION="$2"; shift 2 ;;
    --gov-heterogeneity-enabled)
      GOV_HETEROGENEITY_ENABLED="$2"; shift 2 ;;
    --gov-heterogeneity-seed)
      GOV_HETEROGENEITY_SEED="$2"; shift 2 ;;
    --gov-gamma-low)
      GOV_GAMMA_LOW="$2"; shift 2 ;;
    --gov-gamma-high)
      GOV_GAMMA_HIGH="$2"; shift 2 ;;
    --gov-cost-k-low)
      GOV_COST_K_LOW="$2"; shift 2 ;;
    --gov-cost-k-high)
      GOV_COST_K_HIGH="$2"; shift 2 ;;
    --gov-mechanisms)
      GOV_MECHANISMS="$2"; shift 2 ;;
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
    governance.safeguard_strength "${GOV_SAFEGUARD_STRENGTH}" \
    governance.exit_compensation "${GOV_EXIT_COMPENSATION}" \
    governance.rel_bonus_fraction "${GOV_REL_BONUS_FRACTION}" \
    governance.odrc_triggered_rel_bonus_fraction \
      "${GOV_ODRC_TRIGGERED_REL_BONUS_FRACTION}" \
    governance.effort_eta "${GOV_EFFORT_ETA}" \
    governance.effort_cost_weight "${GOV_EFFORT_COST_WEIGHT}" \
    governance.signal_scale "${GOV_SIGNAL_SCALE}" \
    governance.odrc_exit_compensation_effort_weight \
      "${GOV_ODRC_EXIT_COMP_EFFORT_WEIGHT}" \
    governance.retention_enabled "${GOV_RETENTION_ENABLED}" \
    governance.retention_eta "${GOV_RETENTION_ETA}" \
    governance.retention_cost_weight "${GOV_RETENTION_COST_WEIGHT}" \
    governance.retention_risk_weight "${GOV_RETENTION_RISK_WEIGHT}" \
    governance.retention_protection_weight \
      "${GOV_RETENTION_PROTECTION_WEIGHT}" \
    governance.retention_relationship_weight \
      "${GOV_RETENTION_RELATIONSHIP_WEIGHT}" \
    governance.retention_exit_compensation_weight \
      "${GOV_RETENTION_EXIT_COMP_WEIGHT}" \
    governance.min_participation_prob "${GOV_MIN_PARTICIPATION_PROB}" \
    governance.exit_threshold "${GOV_EXIT_THRESHOLD}" \
    governance.welfare_signal_weight "${GOV_WELFARE_SIGNAL_WEIGHT}" \
    governance.welfare_retention_weight "${GOV_WELFARE_RETENTION_WEIGHT}" \
    governance.welfare_cost_weight "${GOV_WELFARE_COST_WEIGHT}" \
    governance.proxy_ema_lambda "${GOV_PROXY_EMA_LAMBDA}" \
    governance.full_eval_interval "${GOV_FULL_EVAL_INTERVAL}" \
    governance.full_eval_signal_metric "${GOV_FULL_EVAL_SIGNAL_METRIC}" \
    governance.full_eval_signal_scale "${GOV_FULL_EVAL_SIGNAL_SCALE}" \
    governance.pay_gain_fraction "${GOV_PAY_GAIN_FRACTION}" \
    governance.approx_shapley_budget "${GOV_APPROX_SHAPLEY_BUDGET}" \
    governance.trigger_participation_threshold \
      "${GOV_TRIGGER_PARTICIPATION_THRESHOLD}" \
    governance.trigger_relationship_threshold \
      "${GOV_TRIGGER_RELATIONSHIP_THRESHOLD}" \
    governance.trigger_signal_threshold "${GOV_TRIGGER_SIGNAL_THRESHOLD}" \
    governance.trigger_collapse_active_rate \
      "${GOV_TRIGGER_COLLAPSE_ACTIVE_RATE}" \
    governance.formal_budget_cap "${GOV_FORMAL_BUDGET_CAP}" \
    governance.total_budget_cap "${GOV_TOTAL_BUDGET_CAP}" \
    governance.triggered_max_compensation \
      "${GOV_TRIGGERED_MAX_COMPENSATION}" \
    governance.heterogeneity_enabled "${GOV_HETEROGENEITY_ENABLED}" \
    governance.heterogeneity_seed "${GOV_HETEROGENEITY_SEED}" \
    governance.gamma_low "${GOV_GAMMA_LOW}" \
    governance.gamma_high "${GOV_GAMMA_HIGH}" \
    governance.cost_k_low "${GOV_COST_K_LOW}" \
    governance.cost_k_high "${GOV_COST_K_HIGH}" \
    expname_tag "${tag}"

  echo
}

run_case False spot gov_disabled

if [[ "${GOV_MECHANISMS}" == "odrc_v2" ]]; then
  GOV_MECHANISMS="spot pay_by_validation_gain approx_shapley reputation_only formal_insurance relational_contract odrc odrc_triggered"
fi

for mechanism in ${GOV_MECHANISMS}; do
  run_case True "${mechanism}" "gov_${mechanism}"
done

echo "===== Governance summaries ====="
find exp -path "*gov_*" -name governance_summary.json \
  -printf "%TY-%Tm-%Td %TH:%TM %p\n" | sort | tail -n 12
