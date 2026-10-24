#!/bin/zsh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
echo "typecheck"
npm run typecheck
echo "test"
npm test
echo "lint"
npx eslint .
