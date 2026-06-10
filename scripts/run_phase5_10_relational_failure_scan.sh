#!/usr/bin/env bash
set -euo pipefail

# Compact Phase 5.10 scan:
#   - Goal: find regimes where Relational Contract starts to lose retention
#     and ODRC's formal safeguard can create net value.
#   - Scope: 4 regimes * 2 mechanisms, 30 rounds by default.
#   - GPU assignment: one regime per worker, using CUDA devices 1/2/3.

TOTAL_ROUNDS="${TOTAL_ROUNDS:-30}"
DATA_SUBSAMPLE="${DATA_SUBSAMPLE:-0.02}"
SAMPLE_CLIENT_NUM="${SAMPLE_CLIENT_NUM:-5}"
BATCH_SIZE="${BATCH_SIZE:-8}"
EVAL_FREQ="${EVAL_FREQ:-1}"
CFG_FILE="${CFG_FILE:-scripts/example_configs/femnist_governance_smoke.yaml}"
OUT_ROOT="${OUT_ROOT:-exp/phase5_10_relational_failure_scan}"
GPUS=(${GPUS:-1 2 3})

COMMON_EFFORT_ETA="${COMMON_EFFORT_ETA:-2.5}"
COMMON_EFFORT_COST_WEIGHT="${COMMON_EFFORT_COST_WEIGHT:-0.12}"
COMMON_BASE_PAYMENT="${COMMON_BASE_PAYMENT:-0.1}"
COMMON_SAFEGUARD_STRENGTH="${COMMON_SAFEGUARD_STRENGTH:-1.0}"
COMMON_RETENTION_ETA="${COMMON_RETENTION_ETA:-0.35}"
COMMON_RETENTION_COST_WEIGHT="${COMMON_RETENTION_COST_WEIGHT:-0.10}"
COMMON_RETENTION_RISK_WEIGHT="${COMMON_RETENTION_RISK_WEIGHT:-2.5}"
COMMON_RETENTION_PROTECTION_WEIGHT="${COMMON_RETENTION_PROTECTION_WEIGHT:-1.0}"
COMMON_RETENTION_EXIT_COMP_WEIGHT="${COMMON_RETENTION_EXIT_COMP_WEIGHT:-12.0}"
COMMON_MIN_PARTICIPATION_PROB="${COMMON_MIN_PARTICIPATION_PROB:-0.0}"
COMMON_EXIT_THRESHOLD="${COMMON_EXIT_THRESHOLD:-0.60}"
COMMON_WELFARE_SIGNAL_WEIGHT="${COMMON_WELFARE_SIGNAL_WEIGHT:-1.0}"
COMMON_WELFARE_RETENTION_WEIGHT="${COMMON_WELFARE_RETENTION_WEIGHT:-0.2}"
COMMON_WELFARE_COST_WEIGHT="${COMMON_WELFARE_COST_WEIGHT:-0.05}"

HETEROGENEITY_SEED="${HETEROGENEITY_SEED:-12345}"
GAMMA_LOW="${GAMMA_LOW:-0.2}"
GAMMA_HIGH="${GAMMA_HIGH:-0.8}"
COST_K_LOW="${COST_K_LOW:-0.8}"
COST_K_HIGH="${COST_K_HIGH:-1.2}"

mkdir -p "${OUT_ROOT}/logs"

run_one_mechanism() {
  local tag="$1"
  local gpu="$2"
  local mechanism="$3"
  local rel_bonus="$4"
  local rel_weight="$5"
  local exit_comp="$6"
  local log_file="${OUT_ROOT}/logs/${tag}_${mechanism}.log"
  local status_file="${OUT_ROOT}/logs/${tag}_${mechanism}.status"
  local exit_code=0

  echo "[$(date '+%F %T')] ${tag} ${mechanism} on CUDA ${gpu}" \
    | tee -a "${log_file}"

  set +e
  CUDA_VISIBLE_DEVICES="${gpu}" PYTHONPATH="${PYTHONPATH:-.}" \
  python federatedscope/main.py \
    --cfg "${CFG_FILE}" \
    use_gpu True \
    device 0 \
    federate.total_round_num "${TOTAL_ROUNDS}" \
    data.subsample "${DATA_SUBSAMPLE}" \
    federate.sample_client_num "${SAMPLE_CLIENT_NUM}" \
    federate.sample_client_rate -1.0 \
    dataloader.batch_size "${BATCH_SIZE}" \
    eval.freq "${EVAL_FREQ}" \
    eval.count_flops False \
    outdir "${OUT_ROOT}/${tag}" \
    expname_tag "phase5_10_${tag}_gov_${mechanism}" \
    governance.enabled True \
    governance.mechanism "${mechanism}" \
    governance.base_payment "${COMMON_BASE_PAYMENT}" \
    governance.safeguard_strength "${COMMON_SAFEGUARD_STRENGTH}" \
    governance.exit_compensation "${exit_comp}" \
    governance.rel_bonus_fraction "${rel_bonus}" \
    governance.effort_eta "${COMMON_EFFORT_ETA}" \
    governance.effort_cost_weight "${COMMON_EFFORT_COST_WEIGHT}" \
    governance.signal_scale 1.0 \
    governance.odrc_exit_compensation_effort_weight 0.0 \
    governance.retention_enabled True \
    governance.retention_eta "${COMMON_RETENTION_ETA}" \
    governance.retention_cost_weight "${COMMON_RETENTION_COST_WEIGHT}" \
    governance.retention_risk_weight "${COMMON_RETENTION_RISK_WEIGHT}" \
    governance.retention_protection_weight \
      "${COMMON_RETENTION_PROTECTION_WEIGHT}" \
    governance.retention_relationship_weight "${rel_weight}" \
    governance.retention_exit_compensation_weight \
      "${COMMON_RETENTION_EXIT_COMP_WEIGHT}" \
    governance.min_participation_prob "${COMMON_MIN_PARTICIPATION_PROB}" \
    governance.exit_threshold "${COMMON_EXIT_THRESHOLD}" \
    governance.welfare_signal_weight "${COMMON_WELFARE_SIGNAL_WEIGHT}" \
    governance.welfare_retention_weight "${COMMON_WELFARE_RETENTION_WEIGHT}" \
    governance.welfare_cost_weight "${COMMON_WELFARE_COST_WEIGHT}" \
    governance.heterogeneity_enabled True \
    governance.heterogeneity_seed "${HETEROGENEITY_SEED}" \
    governance.gamma_low "${GAMMA_LOW}" \
    governance.gamma_high "${GAMMA_HIGH}" \
    governance.cost_k_low "${COST_K_LOW}" \
    governance.cost_k_high "${COST_K_HIGH}" \
    >> "${log_file}" 2>&1
  exit_code=$?
  set -e

  if [[ "${exit_code}" -eq 0 ]]; then
    echo "ok" > "${status_file}"
    echo "[$(date '+%F %T')] ${tag} ${mechanism} finished"
  else
    echo "failed:${exit_code}" > "${status_file}"
    echo "[$(date '+%F %T')] ${tag} ${mechanism} failed with exit code ${exit_code}" \
      | tee -a "${log_file}"
  fi

  return 0
}

run_regime() {
  local tag="$1"
  local gpu="$2"
  local rel_bonus="$3"
  local rel_weight="$4"
  local exit_comp="$5"

  echo "[$(date '+%F %T')] Start regime ${tag} on CUDA ${gpu}"
  run_one_mechanism "${tag}" "${gpu}" relational_contract \
    "${rel_bonus}" "${rel_weight}" "${exit_comp}"
  run_one_mechanism "${tag}" "${gpu}" odrc \
    "${rel_bonus}" "${rel_weight}" "${exit_comp}"

  python scripts/summarize_governance_runs.py \
    --exp-root "${OUT_ROOT}/${tag}" \
    --csv "${OUT_ROOT}/${tag}_summary.csv" \
    > "${OUT_ROOT}/logs/${tag}_summary.md" || true
  echo "[$(date '+%F %T')] Finished regime ${tag}"
}

# Format: tag rel_bonus rel_weight exit_comp
REGIMES=(
  "rb04_rw000_ec075 0.4 0.00 0.75"
  "rb04_rw005_ec075 0.4 0.05 0.75"
  "rb06_rw000_ec075 0.6 0.00 0.75"
  "rb06_rw005_ec100 0.6 0.05 1.00"
)

worker() {
  local worker_idx="$1"
  local gpu="$2"
  for idx in "${!REGIMES[@]}"; do
    if (( idx % ${#GPUS[@]} != worker_idx )); then
      continue
    fi
    read -r tag rel_bonus rel_weight exit_comp <<< "${REGIMES[$idx]}"
    run_regime "${tag}" "${gpu}" "${rel_bonus}" "${rel_weight}" \
      "${exit_comp}"
  done
}

pids=()
for worker_idx in "${!GPUS[@]}"; do
  worker "${worker_idx}" "${GPUS[$worker_idx]}" &
  pids+=("$!")
done

trap 'echo "Stopping child jobs"; kill "${pids[@]}" 2>/dev/null || true' INT TERM

for pid in "${pids[@]}"; do
  wait "${pid}"
done

combined_csv="${OUT_ROOT}/phase5_10_relational_failure_scan_summary.csv"
summary_files=("${OUT_ROOT}"/*_summary.csv)
if [[ -e "${summary_files[0]}" ]]; then
  awk 'FNR == 1 && NR != 1 { next } { print }' \
    "${summary_files[@]}" > "${combined_csv}"
else
  echo "No per-regime summary CSV files were generated." >&2
  exit 1
fi

echo
echo "Combined summary: ${combined_csv}"
echo "Logs: ${OUT_ROOT}/logs"
echo
python - <<'PY' "${combined_csv}"
import csv
import sys

path = sys.argv[1]
rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
print("| regime | mechanism | active_rate | exit_rate | avg_participation_prob | avg_net_welfare | total_governance_transfer | weighted_test_acc |")
print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
for row in rows:
    run_dir = row.get("run_dir", "")
    regime = ""
    parts = run_dir.split("/")
    for part in parts:
        if part.startswith("rb"):
            regime = part
            break
    print(
        "| {regime} | {mechanism} | {active} | {exit} | {part_prob} | "
        "{net} | {transfer} | {acc} |".format(
            regime=regime,
            mechanism=row.get("mechanism", ""),
            active=row.get("active_rate", ""),
            exit=row.get("exit_rate", ""),
            part_prob=row.get("avg_participation_prob", ""),
            net=row.get("avg_net_welfare", ""),
            transfer=row.get("total_governance_transfer", ""),
            acc=row.get("client_summarized_weighted_avg_test_acc", ""),
        )
    )
PY
