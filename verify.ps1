# Project verification script for Windows/PowerShell.
# Exit 0 = pass. Non-zero = verification failed.

$ErrorActionPreference = "Stop"

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python is required for context artifact validation."
}

& $python.Source ".codex/tools/validate-context-artifacts.py"
& $python.Source -m unittest discover -s ".codex/evals/context" -p "test_*.py"
