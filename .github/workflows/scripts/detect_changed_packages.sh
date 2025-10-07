#!/usr/bin/env bash

set -euo pipefail

# Inputs:
#   BASE_REF  - base branch name (e.g., 'dev') for PR diff (optional)
# Outputs:
#   Writes a JSON array of package names to $GITHUB_OUTPUT as 'packages', if available.
#   Also echoes the JSON to stdout for debugging.

BASE_REF_ENV=${BASE_REF:-}

if [[ -z "$BASE_REF_ENV" ]]; then
  json='[]'
  echo "$json"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "packages=$json" >> "$GITHUB_OUTPUT"
  fi
  exit 0
fi

git fetch --no-tags --prune origin "$BASE_REF_ENV"

# Check if there are any changes to fundamental files:
# - jetson_containers/*.py
# - .github/workflows/
# - root-level .sh files
# - pyproject.toml, requirements.txt
# - jetson-containers file
mapfile -t fundamental_changes < <(
  git diff --name-only "origin/${BASE_REF_ENV}"...HEAD \
    | grep -E '^(jetson_containers/.*\.py$|\.github/workflows/|[^/]+\.sh$|pyproject\.toml$|requirements\.txt$|jetson-containers$)' || true
)

mapfile -t candidates < <(
  git diff --name-only "origin/${BASE_REF_ENV}"...HEAD \
    | awk -F/ '$1=="packages" { if (NF>=3) print $3; else if (NF==2) print $2 }' \
    | sort -u
)

packages=()
for p in "${candidates[@]}"; do
  [[ -z "$p" || "$p" == *.* ]] && continue
  if [[ -d "packages/$p" ]] || compgen -G "packages/*/$p" >/dev/null; then
    packages+=("$p")
  fi
done

# If fundamental changes detected, ensure build-essential is in the list
if (( ${#fundamental_changes[@]} > 0 )); then
  echo "Fundamental changes detected - including build-essential:" >&2
  printf '%s\n' "${fundamental_changes[@]}" >&2
  
  # Check if build-essential is already in the packages array
  build_essential_present=false
  for p in "${packages[@]}"; do
    if [[ "$p" == "build-essential" ]]; then
      build_essential_present=true
      break
    fi
  done
  
  # Add build-essential if not already present
  if [[ "$build_essential_present" == "false" ]]; then
    packages=("build-essential" "${packages[@]}")
  fi
fi

# If no packages detected at all, default to build-essential
if (( ${#packages[@]} == 0 )); then
  echo "No package changes detected - defaulting to build-essential" >&2
  json='["build-essential"]'
  echo "$json"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "packages=$json" >> "$GITHUB_OUTPUT"
  fi
  exit 0
fi

json='['
sep=''
for p in "${packages[@]}"; do
  json+="$sep\"$p\""
  sep=','
done
json+=']'

echo "$json"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "packages=$json" >> "$GITHUB_OUTPUT"
fi
