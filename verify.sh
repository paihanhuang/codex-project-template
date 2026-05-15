#!/usr/bin/env bash
# Project verification script. Keep this fast enough for routine agent use.
# Exit 0 = pass. Non-zero = verification failed.

set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "Python is required for context artifact validation." >&2
  exit 1
fi

"$PYTHON_BIN" .codex/tools/validate-context-artifacts.py
"$PYTHON_BIN" -m unittest discover -s .codex/evals/context -p 'test_*.py'
