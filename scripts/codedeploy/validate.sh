#!/usr/bin/env bash
# CodeDeploy ValidateService / ApplicationStop hook — confirm the bench is serving.
# Non-fatal on ApplicationStop (pre-deploy); fatal on ValidateService (post-deploy).
set -uo pipefail

# Pick a representative site per env to health-check.
case "${DEPLOYMENT_GROUP_NAME:-}" in
  *prod*) SITE="barakat.iztech.net" ;;
  *dev*)  SITE="pos2.35.158.120.8.nip.io" ;;
  *)      SITE="" ;;
esac
[ -z "$SITE" ] && { echo "[validate] no site mapped, skipping"; exit 0; }

code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $SITE" http://localhost/api/method/ping || echo 000)
echo "[validate] $SITE -> HTTP $code"

# ValidateService must fail the deploy if the site is down; ApplicationStop should not.
if [ "${LIFECYCLE_EVENT:-}" = "ValidateService" ] && [ "$code" != "200" ]; then
  echo "[validate] site not healthy after deploy"; exit 1
fi
exit 0
