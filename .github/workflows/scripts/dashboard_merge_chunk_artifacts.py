#!/usr/bin/env python3
"""
Merge chunk artifacts when merged results artifact is missing.

This script processes chunk artifacts from a failed Build Matrix workflow
to create the missing results.json file for the dashboard.
"""

import os
import sys
import json
import requests
import zipfile
import shutil
from typing import Dict, Any, List
from datetime import datetime


def get_environment_variables() -> Dict[str, str]:
    """Get required environment variables."""
    return {
        'dashboard_pat': os.environ.get('DASHBOARD_PAT'),
        'github_token': os.environ.get('GITHUB_TOKEN'),
        'current_run_id': os.environ.get('CURRENT_RUN_ID'),
        'current_sha': os.environ.get('CURRENT_SHA'),
        'current_attempt': os.environ.get('CURRENT_ATTEMPT'),
        'repo': os.environ.get('REPO', 'NVIDIA-AI-IOT/jetson-containers')
    }


def setup_authentication(dashboard_pat: str, github_token: str) -> Dict[str, str]:
    """Setup authentication headers."""
    token = dashboard_pat or github_token
    if not token:
        print("❌ No authentication token available")
        sys.exit(1)

    return {'Authorization': f'token {token}'}


def download_chunk_artifacts(headers: Dict[str, str], repo: str, run_id: str) -> List[Dict[str, Any]]:
    """Download and process chunk artifacts to extract results."""
    print(f"🔍 Downloading chunk artifacts from run {run_id}")

    # Get all artifacts from the run
    artifacts_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
    response = requests.get(artifacts_url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to get artifacts: {response.status_code}")
        return []

    artifacts = response.json().get('artifacts', [])
    chunk_artifacts = [a for a in artifacts if a['name'].startswith('results-') and '-chunk-' in a['name']]

    print(f"📋 Found {len(chunk_artifacts)} chunk artifacts")

    all_results = []
    temp_dir = f'./temp-chunk-merge-{run_id}'
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for i, artifact in enumerate(chunk_artifacts):
            print(f"  📥 Processing chunk {i+1}/{len(chunk_artifacts)}: {artifact['name']}")

            # Download artifact
            download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact['id']}/zip"
            download_response = requests.get(download_url, headers=headers)

            if download_response.status_code != 200:
                print(f"    ❌ Failed to download: {download_response.status_code}")
                continue

            # Save and extract artifact
            artifact_path = os.path.join(temp_dir, f"{artifact['name']}.zip")
            with open(artifact_path, 'wb') as f:
                f.write(download_response.content)

            with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.join(temp_dir, artifact['name']))

            # Look for results.json in the extracted artifact
            results_path = os.path.join(temp_dir, artifact['name'], 'results.json')
            if os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    chunk_results = json.load(f)
                    if isinstance(chunk_results, list):
                        all_results.extend(chunk_results)
                        print(f"    ✅ Added {len(chunk_results)} results")
                    else:
                        print(f"    ⚠️ Unexpected results format in {artifact['name']}")
            else:
                print(f"    ⚠️ No results.json found in {artifact['name']}")

            # Clean up artifact zip
            os.remove(artifact_path)

    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    # Sort results alphabetically by package name to maintain consistent ordering
    all_results.sort(key=lambda x: x.get('package', ''))
    print(f"✅ Merged and sorted {len(all_results)} total results from chunk artifacts")
    return all_results


def create_results_json(results: List[Dict[str, Any]], run_id: str, sha: str) -> None:
    """Create the results.json file for the dashboard."""
    # Add metadata to each result
    for result in results:
        result['run_id'] = run_id
        result['run_url'] = f"https://github.com/NVIDIA-AI-IOT/jetson-containers/actions/runs/{run_id}"
        result['sha'] = sha
        result['timestamp'] = datetime.now().timestamp()

    # Create runs directory (treat as historical run)
    os.makedirs('./runs', exist_ok=True)

    # Write results file in historical runs format
    results_file = f'./runs/results-{run_id}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Created results file with {len(results)} results")
    print(f"📁 Saved to: {results_file}")


def main():
    """Main function to merge chunk artifacts."""
    env_vars = get_environment_variables()

    if not env_vars['current_run_id']:
        print("❌ CURRENT_RUN_ID not set")
        sys.exit(1)

    headers = setup_authentication(env_vars['dashboard_pat'], env_vars['github_token'])

    print(f"🔧 Merging chunk artifacts for run {env_vars['current_run_id']}")
    print(f"   SHA: {env_vars['current_sha']}")
    print(f"   Repo: {env_vars['repo']}")

    # Download and merge chunk artifacts
    results = download_chunk_artifacts(headers, env_vars['repo'], env_vars['current_run_id'])

    if not results:
        print("❌ No results found in chunk artifacts")
        sys.exit(1)

    # Create results.json
    create_results_json(results, env_vars['current_run_id'], env_vars['current_sha'])

    print(f"✅ Successfully created results.json from chunk artifacts")


if __name__ == '__main__':
    main()

