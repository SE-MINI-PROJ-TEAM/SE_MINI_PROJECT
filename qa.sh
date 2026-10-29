#!/usr/bin/env bash
# Runs the automated QA stages in Docker. The host only needs Docker (Compose v2). Same script locally and in CI.
#   ./qa.sh <stage...>      stages: consistency unit static integration perf zap e2e uat docs demo report   |   all   |   down
set -uo pipefail
cd "$(dirname "$0")"

export UAT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || true)"
COMPOSE="docker compose -f docker-compose.qa.yml"
mkdir -p qa/reports/k6 qa/reports/zap demo/videos
chmod -R a+rwX qa/reports demo/videos 2>/dev/null || true   # tool containers run as other users

run_stage() {
  case "$1" in
    consistency|unit|static|integration|e2e|uat|docs|demo|report)
      $COMPOSE run --rm --build qa python qa/run.py "$1" ;;
    perf) $COMPOSE run --rm --build k6 ;;
    zap)  $COMPOSE run --rm --build zap ;;
    *) echo "unknown stage: $1" >&2; return 2 ;;
  esac
}

if [ $# -eq 0 ]; then
  echo "usage: ./qa.sh <consistency|unit|static|integration|perf|zap|e2e|docs|demo|report|all|down> ..." >&2
  exit 2
fi

stages=("$@")
[ "${stages[0]}" = "all" ] && stages=(consistency unit static integration perf zap e2e)

if [ "${stages[0]}" = "down" ]; then
  $COMPOSE --profile qa --profile perf --profile zap down -v --remove-orphans
  exit 0
fi

declare -A result
overall=0
for stage in "${stages[@]}"; do
  echo; echo "=================== $stage ==================="
  run_stage "$stage"; code=$?
  result[$stage]=$code
  [ $code -ne 0 ] && overall=1
done

if [ "${1:-}" = "all" ]; then
  echo; echo "=================== report ==================="
  run_stage report || overall=1
  $COMPOSE --profile qa --profile perf --profile zap down -v --remove-orphans >/dev/null 2>&1
fi

echo; echo "============================================================"
for stage in "${stages[@]}"; do
  [ "${result[$stage]}" = "0" ] && echo "PASS  $stage" || echo "FAIL  $stage"
done
echo "============================================================"
exit $overall
