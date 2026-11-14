#!/usr/bin/env bash
# Runs the modern-web-guidance skill CLI with a compatible Node.
#
# The CLI requires Node >= 22. Projects often pin an older Node for their
# frontend, so calling `npx -y modern-web-guidance@latest ...` directly fails.
# This wrapper uses the active Node when it is new enough, otherwise the newest
# one installed through nvm, without changing the project's pinned version.
#
# Usage:
#   scripts/dev/mwg.sh install                 # install the skill for your agents
#   scripts/dev/mwg.sh search "light dismiss dialog"
#   scripts/dev/mwg.sh retrieve "dark-mode,dark-mode-toggle"
#   scripts/dev/mwg.sh legacy-scan frontend/src --json
#   scripts/dev/mwg.sh update
set -euo pipefail

MIN_NODE_MAJOR=22

node_major() {
  "$1" -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0
}

find_node_bin_dir() {
  local current
  current="$(command -v node || true)"
  if [[ -n "$current" && "$(node_major "$current")" -ge "$MIN_NODE_MAJOR" ]]; then
    dirname "$current"
    return 0
  fi

  local nvm_root="${NVM_DIR:-$HOME/.nvm}/versions/node"
  local candidate
  if [[ -d "$nvm_root" ]]; then
    while IFS= read -r candidate; do
      if [[ -x "$candidate/bin/node" && "$(node_major "$candidate/bin/node")" -ge "$MIN_NODE_MAJOR" ]]; then
        echo "$candidate/bin"
        return 0
      fi
    done < <(find "$nvm_root" -mindepth 1 -maxdepth 1 -type d | sort -rV)
  fi
  return 1
}

if ! NODE_BIN_DIR="$(find_node_bin_dir)"; then
  echo "modern-web-guidance needs Node >= ${MIN_NODE_MAJOR} and none was found." >&2
  echo "Install one with: nvm install ${MIN_NODE_MAJOR}" >&2
  exit 1
fi

export PATH="$NODE_BIN_DIR:$PATH"
# The CLI sends anonymous usage telemetry to Google; it stays off unless asked for.
export DISABLE_TELEMETRY="${DISABLE_TELEMETRY:-1}"

exec npx -y modern-web-guidance@latest "$@"
