#!/usr/bin/env python3
"""
Download current run artifacts and logs for dashboard generation.

This script downloads artifacts from the current GitHub Actions workflow run,
including merged results and chunk artifacts containing log files.
"""

import os
import sys
import json
import requests
import zipfile
import shutil
from typing import Optional, Dict, Any


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


def setup_authentication(dashboard_pat: Optional[str], github_token: Optional[str]) -> Dict[str, str]:
    """Setup authentication headers."""
    token = dashboard_pat or github_token
    if not token:
        print("❌ No authentication token available")
        sys.exit(1)

    print(f"🔍 Token debugging for current run download:")
    print(f"   DASHBOARD_PAT exists: {dashboard_pat is not None}")
    print(f"   GITHUB_TOKEN exists: {github_token is not None}")
    print(f"   Using token: {'DASHBOARD_PAT' if dashboard_pat else 'GITHUB_TOKEN'}")

    return {'Authorization': f'token {token}'}


def create_directories():
    """Create necessary directories."""
    os.makedirs('./results-data', exist_ok=True)
    os.makedirs('./logs/run-current', exist_ok=True)


def download_artifact(artifact: Dict[str, Any], headers: Dict[str, str], repo: str) -> Optional[bytes]:
    """Download a single artifact."""
    download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact['id']}/zip"
    response = requests.get(download_url, headers=headers)

    if response.status_code == 200:
        return response.content
    else:
        print(f"    ❌ Failed to download {artifact['name']}: {response.status_code}")
        return None


def process_merged_results_artifact(artifact: Dict[str, Any], headers: Dict[str, str], repo: str):
    """Process the merged results artifact."""
    print(f"    📥 Downloading merged results...")
    content = download_artifact(artifact, headers, repo)

    if content:
        with open('./results-data/results.zip', 'wb') as f:
            f.write(content)

        with zipfile.ZipFile('./results-data/results.zip', 'r') as zip_ref:
            zip_ref.extractall('./results-data')

        os.remove('./results-data/results.zip')
        print(f"    ✅ Merged results downloaded")


def process_chunk_artifact(artifact: Dict[str, Any], headers: Dict[str, str], repo: str):
    """Process a chunk artifact containing logs."""
    print(f"    📥 Downloading chunk artifact with logs...")
    content = download_artifact(artifact, headers, repo)

    if not content:
        return

    # Extract platform info from artifact name
    # Format: results-{platform}-chunk-{index}-{attempt}
    parts = artifact['name'].split('-')
    platform = parts[1] if len(parts) > 1 else 'unknown'
    chunk_index = parts[3] if len(parts) > 3 else '000'

    artifact_path = f'./temp-{artifact["id"]}.zip'
    with open(artifact_path, 'wb') as f:
        f.write(content)

    with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
        zip_ref.extractall(f'./temp-{artifact["id"]}')

    # Move log files with unique names
    temp_dir = f'./temp-{artifact["id"]}'
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.log'):
                src = os.path.join(root, file)
                # Create unique filename with platform
                base_name, ext = os.path.splitext(file)
                unique_name = f"{base_name}_{platform}{ext}"
                dst = os.path.join('./logs/run-current', unique_name)
                print(f"    📝 Moving log: {file} -> {unique_name}")
                shutil.move(src, dst)

    # Clean up
    os.remove(artifact_path)
    shutil.rmtree(temp_dir)
    print(f"    ✅ Chunk logs processed for {platform}")


def move_logs_to_main_directory():
    """Move logs from run-current to main logs directory."""
    if not os.path.exists('./logs/run-current'):
        print(f"  ℹ️ No run-current directory found")
        return

    run_current_logs = os.listdir('./logs/run-current')
    if not run_current_logs:
        print(f"  ℹ️ No log files in run-current directory")
        return

    print(f"📝 Moving {len(run_current_logs)} log files from run-current to main logs directory...")
    for log_file in run_current_logs:
        src = os.path.join('./logs/run-current', log_file)
        dst = os.path.join('./logs', log_file)
        shutil.move(src, dst)
        print(f"  Moved: {log_file}")

    # Remove empty run-current directory
    os.rmdir('./logs/run-current')
    print(f"✅ Log files moved successfully")


def print_summary():
    """Print summary of downloaded files."""
    print(f"\n📁 Downloaded files:")

    if os.path.exists('./results-data/results.json'):
        print(f"  ✅ ./results-data/results.json")
    else:
        print(f"  ❌ ./results-data/results.json missing")

    if os.path.exists('./logs'):
        log_files = [f for f in os.listdir('./logs') if f.endswith('.log')]
        print(f"  📝 Log files ({len(log_files)}):")
        for log_file in log_files:
            print(f"    - {log_file}")
    else:
        print(f"  ❌ No log files found")


def main():
    """Main function to download current run artifacts."""
    env_vars = get_environment_variables()
    headers = setup_authentication(env_vars['dashboard_pat'], env_vars['github_token'])

    print(f"🔍 Downloading artifacts from current run {env_vars['current_run_id']}")
    print(f"   SHA: {env_vars['current_sha']}, Attempt: {env_vars['current_attempt']}")

    # Get all artifacts from current run
    artifacts_url = f"https://api.github.com/repos/{env_vars['repo']}/actions/runs/{env_vars['current_run_id']}/artifacts"
    response = requests.get(artifacts_url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to get artifacts: {response.status_code}")
        print(f"   This may happen if the Build Matrix workflow was cancelled")
        print(f"   Creating empty results structure for dashboard fallback")
        create_directories()
        # Create empty results.json for fallback
        with open('./results-data/results.json', 'w') as f:
            json.dump([], f)
        print(f"✅ Created empty results.json for fallback")
        return

    artifacts = response.json().get('artifacts', [])
    print(f"📋 Found {len(artifacts)} total artifacts for current run:")

    create_directories()

    merged_results_found = False
    chunk_artifacts_found = 0

    for artifact in artifacts:
        print(f"  - {artifact['name']} ({artifact['size_in_bytes']} bytes)")

        # Download final merged results
        if artifact['name'] == f"sweep-results-{env_vars['current_sha']}-{env_vars['current_attempt']}":
            process_merged_results_artifact(artifact, headers, env_vars['repo'])
            merged_results_found = True

        # Download chunk artifacts (contain logs)
        elif (artifact['name'].startswith('results-') and
              '-chunk-' in artifact['name'] and
              artifact['name'].endswith(f"-{env_vars['current_attempt']}")):
            process_chunk_artifact(artifact, headers, env_vars['repo'])
            chunk_artifacts_found += 1

    # If no merged results were found, create empty results.json for fallback
    if not merged_results_found:
        print(f"⚠️ No merged results artifact found for current run")
        print(f"   This is expected when the Build Matrix workflow is cancelled")
        print(f"   Creating empty results.json for dashboard fallback")
        with open('./results-data/results.json', 'w') as f:
            json.dump([], f)
        print(f"✅ Created empty results.json for fallback")

    print(f"✅ Current run artifact download complete")
    print(f"   - Merged results: {'✅ Found' if merged_results_found else '❌ Not found (cancelled workflow)'}")
    print(f"   - Chunk artifacts: {chunk_artifacts_found} found")

    move_logs_to_main_directory()
    print_summary()


if __name__ == '__main__':
    main()
