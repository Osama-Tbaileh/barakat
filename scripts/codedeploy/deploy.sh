#!/usr/bin/env bash
# CodeDeploy AfterInstall hook — deploy one Frappe app onto the shared bench.
# Picks branch from the CodeDeploy deployment-group name (no env wiring needed):
#   *-prod-dg -> main   |   *-dev-dg -> dev
# Runs as root (per appspec) then drops to the `frappe` user for all bench commands.
set -euo pipefail

# ── set per repo ──────────────────────────────────────────────────────────────
APP="barakat"
BENCH="/home/frappe/erp_project"
# ──────────────────────────────────────────────────────────────────────────────

case "${DEPLOYMENT_GROUP_NAME:-}" in
  *prod*) BRANCH="main" ;;
  *dev*)  BRANCH="dev"  ;;
  *)      BRANCH="main" ;;          # safe default
esac
echo "[deploy] app=$APP branch=$BRANCH group=${DEPLOYMENT_GROUP_NAME:-?}"

sudo -H -u frappe bash -euo pipefail <<EOF
export PATH=/usr/bin:/usr/local/bin:/home/frappe/.local/bin:\$PATH
cd "$BENCH"

# 1. Safety backup of every site before any migration (skip on dev for speed if desired)
if [ "$BRANCH" = "main" ]; then
  bench --site all backup
fi

# 2. Fast-forward the app's checkout to the deployed branch
cd "apps/$APP"
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"
cd "$BENCH"

# 3. Apply schema/patches, rebuild this app's assets, restart workers
bench --site all migrate
bench build --app "$APP"
bench restart
EOF

echo "[deploy] done"
