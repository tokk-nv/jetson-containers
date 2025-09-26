#!/usr/bin/env python3
"""
Create meaningful results.json when all chunks timeout or fail.
This script is called from the Build Matrix workflow when no chunk artifacts are found.
"""

import json
import os
import glob
from datetime import datetime

def main():
    # Get workflow metadata
    run_id = os.environ.get('GITHUB_RUN_ID', 'unknown')
    run_attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    sha = os.environ.get('GITHUB_SHA', 'unknown')
    workflow_url = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'unknown')}/actions/runs/{run_id}"
    timestamp = int(datetime.now().timestamp())

    # Initialize results
    results = []

    # Try to get package information from plan artifacts
    plan_dirs = glob.glob("_plans/plan-*")
    if plan_dirs:
        print(f"   Found {len(plan_dirs)} plan artifacts")

        for plan_dir in plan_dirs:
            platform = os.path.basename(plan_dir).replace("plan-", "")
            chunks_file = os.path.join(plan_dir, "chunks.json")

            if os.path.exists(chunks_file):
                try:
                    with open(chunks_file, 'r') as f:
                        chunks = json.load(f)

                    # Create a result entry for each package that was supposed to be built
                    for chunk_idx, packages in enumerate(chunks):
                        for package in packages:
                            results.append({
                                "package": package,
                                "tag": f"{platform}-chunk-{chunk_idx}",
                                "status": "cancelled",
                                "duration_s": 0.0,
                                "timestamp": timestamp,
                                "run_id": run_id,
                                "run_url": workflow_url,
                                "sha": sha,
                                "runner": f"{platform}-runner",
                                "runner_label": platform,
                                "log_relpath": None,
                                "failure_point": "workflow_cancelled",
                                "cancellation_reason": "All build chunks timed out or failed before completion"
                            })
                except Exception as e:
                    print(f"   Error reading {chunks_file}: {e}")
    else:
        print("   No plan artifacts found - creating basic cancellation entry")
        # Create a basic result entry when no plan data is available
        results.append({
            "package": "unknown-packages",
            "tag": "cancelled-workflow",
            "status": "cancelled",
            "duration_s": 0.0,
            "timestamp": timestamp,
            "run_id": run_id,
            "run_url": workflow_url,
            "sha": sha,
            "runner": "unknown-runner",
            "runner_label": "unknown",
            "log_relpath": None,
            "failure_point": "workflow_cancelled",
            "cancellation_reason": "All build chunks timed out or failed before completion"
        })

    # Write results
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"   Created results.json with {len(results)} entries")

if __name__ == "__main__":
    main()
