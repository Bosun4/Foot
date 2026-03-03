#!/bin/bash
set -euo pipefail

cd /workspaces/Foot

echo "=== Committing and pushing JJ improvements ==="
git add -A
git commit -m "fix: JJ auto-discover api + robust parse (no-playwright)" || true
git push

echo "=== Done ✅ ==="
echo "Now go to GitHub Actions to re-run jobs or wait for the next scheduled trigger (7 AM UTC)."
