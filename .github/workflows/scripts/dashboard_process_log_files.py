#!/usr/bin/env python3
"""
Process log files from historical workflow runs.

This script downloads and organizes log files from chunk artifacts
for historical runs to provide detailed log access in the dashboard.
"""

import os
import sys
import json
import requests
import zipfile
import shutil
import re
from typing import Optional, Dict, Any, List


def get_environment_variables() -> Dict[str, str]:
    """Get required environment variables."""
    return {
        'dashboard_pat': os.environ.get('DASHBOARD_PAT'),
        'github_token': os.environ.get('GITHUB_TOKEN'),
        'repo': os.environ.get('REPO', 'NVIDIA-AI-IOT/jetson-containers')
    }


def setup_authentication(dashboard_pat: Optional[str], github_token: Optional[str]) -> Dict[str, str]:
    """Setup authentication headers."""
    token = dashboard_pat or github_token
    if not token:
        print("❌ No authentication token available")
        sys.exit(1)

    return {'Authorization': f'token {token}'}


def process_run_logs(run_id: str, headers: Dict[str, str], repo: str):
    """Process log files for a specific run."""
    print(f"Processing logs for run {run_id}")

    # Load results JSON to get runner names for each log
    results_file = f'./runs/results-{run_id}.json'
    log_to_runner_map = {}

    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            # Create mapping from log base name to runner label
            # log_relpath format: "logs/index_000_gdrcopy.log"
            for result in results:
                log_relpath = result.get('log_relpath', '')
                runner_label = result.get('runner_label') or result.get('runner', 'unknown')

                if log_relpath:
                    # Extract base filename: "logs/index_000_gdrcopy.log" -> "index_000_gdrcopy"
                    log_basename = os.path.basename(log_relpath).replace('.log', '')
                    log_to_runner_map[log_basename] = runner_label

            print(f"  📋 Loaded runner mappings for {len(log_to_runner_map)} log files")
        except Exception as e:
            print(f"  ⚠️  Failed to load results JSON: {e}")
            print(f"  ℹ️  Will use generic platform suffixes as fallback")
    else:
        print(f"  ⚠️  Results file not found: {results_file}")
        print(f"  ℹ️  Will use generic platform suffixes as fallback")

    # Get artifacts for this run (with pagination support)
    print(f"  📋 Checking artifacts for run {run_id}:")
    print(f"    🔑 Using token: {'DASHBOARD_PAT' if os.environ.get('DASHBOARD_PAT') else 'GITHUB_TOKEN'}")

    artifacts = []
    page = 1
    per_page = 100  # Max allowed by GitHub API
    total_count = 0

    while True:
        artifacts_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts?per_page={per_page}&page={page}'
        print(f"    🌐 Fetching page {page}: {artifacts_url}")

        artifacts_response = requests.get(artifacts_url, headers=headers)
        print(f"    📡 API Response Status (page {page}): {artifacts_response.status_code}")

        if artifacts_response.status_code != 200:
            break

        artifacts_data = artifacts_response.json()
        page_artifacts = artifacts_data.get('artifacts', [])
        total_count = artifacts_data.get('total_count', 0)

        if not page_artifacts:
            break  # No more artifacts

        artifacts.extend(page_artifacts)
        print(f"    📄 Page {page}: {len(page_artifacts)} artifacts")

        # Check if there are more pages
        if len(page_artifacts) < per_page:
            break  # Last page

        page += 1

    print(f"    📊 Total artifacts fetched: {len(artifacts)} (API reported total_count={total_count})")

    if artifacts_response.status_code == 200:

        if artifacts:
            print(f"    📦 Found {len(artifacts)} artifacts:")
            for artifact in artifacts:
                expired_status = artifact.get('expired', 'unknown')
                print(f"      - Name: {artifact['name']}, Size: {artifact['size_in_bytes']} bytes, Expired: {expired_status}")
        else:
            print(f"    ❌ No artifacts found for run {run_id}")
            print(f"    🔍 Raw API response keys: {list(artifacts_data.keys())}")
            if 'message' in artifacts_data:
                print(f"    📄 API message: {artifacts_data['message']}")
    else:
        print(f"    ❌ API Error {artifacts_response.status_code}")
        print(f"    📄 Error response: {artifacts_response.text[:300]}...")
        if artifacts_response.status_code == 401:
            print(f"    🚨 Authentication failed - check PAT permissions!")
        elif artifacts_response.status_code == 403:
            print(f"    🚨 Forbidden - token lacks required permissions!")
        return

    if not artifacts:
        return

    # Find chunk results artifacts (these contain the logs)
    chunk_artifacts = [a for a in artifacts if a['name'].startswith('results-') and 'chunk-' in a['name']]

    # If no chunk artifacts, try broader search for log-containing artifacts
    if not chunk_artifacts:
        log_artifacts = [a for a in artifacts if 'log' in a['name'].lower() or a['name'].startswith('results-')]
        if log_artifacts:
            print(f"    📋 No chunk artifacts found, but found {len(log_artifacts)} potential log artifacts:")
            for artifact in log_artifacts:
                print(f"      - {artifact['name']}")
            chunk_artifacts = log_artifacts[:2]  # Try first 2 as fallback

    if chunk_artifacts:
        print(f"    📋 Found {len(chunk_artifacts)} log artifacts")

        # Create run-specific logs directory
        run_logs_dir = f'./logs/run-{run_id}'
        os.makedirs(run_logs_dir, exist_ok=True)

        downloaded_logs = []

        for log_artifact in chunk_artifacts:
            print(f"      📥 Downloading {log_artifact['name']}")

            # Download artifact
            download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{log_artifact['id']}/zip"
            download_response = requests.get(download_url, headers=headers)

            if download_response.status_code == 200:
                # Save and extract artifact
                log_artifact_path = f'./temp-log-{log_artifact["id"]}.zip'
                with open(log_artifact_path, 'wb') as f:
                    f.write(download_response.content)

                # Extract log files
                with zipfile.ZipFile(log_artifact_path, 'r') as zip_ref:
                    zip_ref.extractall(f'./temp-log-{log_artifact["id"]}')

                # Move log files to run directory with unique names
                temp_log_dir = f'./temp-log-{log_artifact["id"]}'
                artifact_name = log_artifact['name']
                print(f"       📂 Extracting from: {temp_log_dir} (Artifact: {artifact_name})")

                # Determine platform suffix from artifact name (fallback)
                platform_suffix = ""
                if 'orin' in artifact_name.lower():
                    platform_suffix = "_orin"
                elif 'thor' in artifact_name.lower():
                    platform_suffix = "_thor"

                for root, dirs, files in os.walk(temp_log_dir):
                    print(f"         📁 Directory: {root}")
                    print(f"         📄 Files found in artifact: {files}")
                    for file in files:
                        if file.endswith('.log'):
                            src = os.path.join(root, file)
                            base_name, ext = os.path.splitext(file)

                            # Try to get actual runner name from results JSON mapping
                            if base_name in log_to_runner_map:
                                runner_label = log_to_runner_map[base_name]
                                # Sanitize runner label for filename (replace special chars)
                                runner_suffix = '_' + re.sub(r'[^a-zA-Z0-9]', '-', runner_label)
                                print(f"         🏷️  Using runner label: {runner_label} → suffix: {runner_suffix}")
                            else:
                                # Fallback to platform suffix if no mapping found
                                runner_suffix = platform_suffix
                                print(f"         ⚠️  No runner mapping for {base_name}, using platform suffix: {runner_suffix}")

                            unique_file = f"{base_name}{runner_suffix}{ext}"
                            dst = os.path.join(run_logs_dir, unique_file)
                            print(f"         📝 Moving log: {src} → {dst}")
                            shutil.move(src, dst)
                            downloaded_logs.append(unique_file)
                        else:
                            print(f"         ⚠️  Skipping non-log file: {file}")

                # Clean up log temp files
                os.remove(log_artifact_path)
                shutil.rmtree(temp_log_dir)
            else:
                print(f"      ❌ Failed to download {log_artifact['name']}: {download_response.status_code}")

        if downloaded_logs:
            print(f"    ✅ Downloaded {len(downloaded_logs)} log files for run {run_id}")
            print(f"    📋 Log files created:")
            for log_file in downloaded_logs:
                log_path = os.path.join(run_logs_dir, log_file)
                if os.path.exists(log_path):
                    size = os.path.getsize(log_path)
                    print(f"      - {log_file} ({size} bytes)")
        else:
            print(f"    ⚠️  No log files downloaded for run {run_id}")
    else:
        print(f"    ❌ No log artifacts found for run {run_id}")


def main():
    """Main function to process log files."""
    env_vars = get_environment_variables()
    headers = setup_authentication(env_vars['dashboard_pat'], env_vars['github_token'])

    # Create logs directory
    os.makedirs('./logs', exist_ok=True)

    # Check if we should only process a specific (triggering) run
    triggering_run_id = os.environ.get('TRIGGERING_RUN_ID')

    # Process each run directory
    runs_dir = './runs'
    if not os.path.exists(runs_dir):
        print("❌ No runs directory found - historical runs must be downloaded first")
        sys.exit(1)

    processed_runs = 0

    # ALWAYS process all historical runs to build complete log history
    # The "for efficiency" optimization that only processed triggering_run_id was a regression
    # that broke historical log access - we need logs for ALL runs to be available
    print(f"📋 Processing logs for all runs in {runs_dir}")
    print(f"    (Triggered by run: {triggering_run_id or 'manual'})")

    for filename in os.listdir(runs_dir):
        if filename.startswith('results-') and filename.endswith('.json'):
            run_id = filename.replace('results-', '').replace('.json', '')
            process_run_logs(run_id, headers, env_vars['repo'])
            processed_runs += 1

    print(f"\n✅ Completed processing log files for {processed_runs} run(s)")


if __name__ == '__main__':
    main()
