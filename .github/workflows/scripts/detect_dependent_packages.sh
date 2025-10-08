#!/usr/bin/env bash

set -euo pipefail

# Inputs:
#   BASE_REF  - base branch name (e.g., 'dev') for PR diff (optional)
# Outputs:
#   Writes a JSON array of package names to $GITHUB_OUTPUT as 'packages', if available.
#   Also echoes the JSON to stdout for debugging.
#
# This script detects changed packages and adds vllm/sglang if any of their dependencies were touched.

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

# Function to extract dependencies from a Dockerfile
# Usage: get_dependencies <package_name>
# Returns: space-separated list of dependencies
get_dependencies() {
  local pkg="$1"
  local dockerfile=""
  
  # Search for the package Dockerfile in the packages directory
  dockerfile=$(find packages -type f -path "*/$pkg/Dockerfile" | head -n 1)
  
  if [[ -z "$dockerfile" || ! -f "$dockerfile" ]]; then
    return 0
  fi
  
  # Extract the depends line from the header comment
  local depends_line=$(grep -E '^\s*#\s*depends:' "$dockerfile" | head -n 1 || true)
  
  if [[ -z "$depends_line" ]]; then
    return 0
  fi
  
  # Parse the dependencies from the line
  # Format can be: "# depends: [dep1, dep2, dep3]" or "# depends: dep1"
  local deps=""
  if echo "$depends_line" | grep -q '\['; then
    # Bracket format: extract content between []
    deps=$(echo "$depends_line" | sed -E 's/.*depends:\s*\[([^]]*)\].*/\1/' | tr ',' ' ' | sed 's/[][]//g' | tr -s ' ')
  else
    # Simple format: just take everything after "depends:"
    deps=$(echo "$depends_line" | sed -E 's/.*depends:\s*//' | tr ',' ' ' | tr -s ' ')
  fi
  
  echo "$deps"
}

# Function to recursively get all dependencies of a package
# Usage: get_all_dependencies <package_name>
# Uses a queue-based approach to avoid recursion issues
# Returns: space-separated list of all recursive dependencies
get_all_dependencies() {
  local root_pkg="$1"
  local -A visited
  local -a queue
  local all_deps=""
  
  queue=("$root_pkg")
  visited["$root_pkg"]=1
  
  while (( ${#queue[@]} > 0 )); do
    local current="${queue[0]}"
    queue=("${queue[@]:1}")
    
    local direct_deps=$(get_dependencies "$current")
    
    for dep in $direct_deps; do
      # Skip if already visited
      if [[ -n "${visited[$dep]:-}" ]]; then
        continue
      fi
      
      visited["$dep"]=1
      all_deps="$all_deps $dep"
      queue+=("$dep")
    done
  done
  
  echo "$all_deps"
}

# Check if there are any changes to fundamental files
mapfile -t fundamental_changes < <(
  git diff --name-only "origin/${BASE_REF_ENV}"...HEAD \
    | grep -E '^(jetson_containers/.*\.py$|\.github/workflows/|[^/]+\.sh$|pyproject\.toml$|requirements\.txt$|jetson-containers$)' || true
)

# Get all changed packages
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
  
  build_essential_present=false
  for p in "${packages[@]}"; do
    if [[ "$p" == "build-essential" ]]; then
      build_essential_present=true
      break
    fi
  done
  
  if [[ "$build_essential_present" == "false" ]]; then
    packages=("build-essential" "${packages[@]}")
  fi
fi

# Now check if any changed package is a dependency of vllm or sglang
echo "Checking dependencies for vllm and sglang..." >&2

# Get all dependencies for vllm
vllm_all_deps=$(get_all_dependencies "vllm")
echo "vllm dependencies: $vllm_all_deps" >&2

# Get all dependencies for sglang
sglang_all_deps=$(get_all_dependencies "sglang")
echo "sglang dependencies: $sglang_all_deps" >&2

# Check if any changed package affects vllm
vllm_affected=false
for changed_pkg in "${packages[@]}"; do
  for dep in $vllm_all_deps; do
    if [[ "$changed_pkg" == "$dep" ]]; then
      vllm_affected=true
      echo "Package '$changed_pkg' is a dependency of vllm" >&2
      break 2
    fi
  done
done

# Check if any changed package affects sglang
sglang_affected=false
for changed_pkg in "${packages[@]}"; do
  for dep in $sglang_all_deps; do
    if [[ "$changed_pkg" == "$dep" ]]; then
      sglang_affected=true
      echo "Package '$changed_pkg' is a dependency of sglang" >&2
      break 2
    fi
  done
done

# Add vllm if affected and not already in the list
if [[ "$vllm_affected" == "true" ]]; then
  vllm_present=false
  for p in "${packages[@]}"; do
    if [[ "$p" == "vllm" ]]; then
      vllm_present=true
      break
    fi
  done
  
  if [[ "$vllm_present" == "false" ]]; then
    echo "Adding vllm to the build list (dependency was touched)" >&2
    packages+=("vllm")
  fi
fi

# Add sglang if affected and not already in the list
if [[ "$sglang_affected" == "true" ]]; then
  sglang_present=false
  for p in "${packages[@]}"; do
    if [[ "$p" == "sglang" ]]; then
      sglang_present=true
      break
    fi
  done
  
  if [[ "$sglang_present" == "false" ]]; then
    echo "Adding sglang to the build list (dependency was touched)" >&2
    packages+=("sglang")
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

# Build JSON output
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
