#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PS_SCRIPT="$ROOT_DIR/verify.ps1"

to_windows_path() {
  if command -v wslpath >/dev/null 2>&1; then
    wslpath -w "$1"
    return
  fi

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
    return
  fi

  printf '%s\n' "$1"
}

if command -v pwsh >/dev/null 2>&1; then
  exec pwsh -NoProfile -File "$PS_SCRIPT"
fi

if command -v powershell.exe >/dev/null 2>&1; then
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(to_windows_path "$PS_SCRIPT")"
fi

if command -v powershell >/dev/null 2>&1; then
  exec powershell -NoProfile -ExecutionPolicy Bypass -File "$(to_windows_path "$PS_SCRIPT")"
fi

echo "FAIL: PowerShell is required to run template verification from verify.sh."
exit 1
