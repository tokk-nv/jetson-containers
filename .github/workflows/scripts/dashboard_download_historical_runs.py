#!/usr/bin/env python3
"""
Download historical workflow runs for dashboard timeline.

This script fetches recent workflow runs and their artifacts to provide
historical context in the dashboard.
"""

import os
import sys
import json
import requests
import zipfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List


def get_environment_variables() -> Dict[str, str]:
    """Get required environment variables."""
    return {
        'dashboard_pat': os.environ.get('DASHBOARD_PAT'),
        'github_token': os.environ.get('GITHUB_TOKEN'),
        'current_repo': os.environ.get('REPO', 'NVIDIA-AI-IOT/jetson-containers'),
        'github_event_name': os.environ.get('GITHUB_EVENT_NAME'),
        'github_actor': os.environ.get('GITHUB_ACTOR')
    }


def setup_authentication(dashboard_pat: Optional[str], github_token: Optional[str]) -> Dict[str, str]:
    """Setup authentication headers."""
    token = dashboard_pat or github_token
    if not token:
        print("❌ No authentication token available")
        sys.exit(1)

    print(f"🔍 Token debugging:")
    print(f"   DASHBOARD_PAT exists: {dashboard_pat is not None}")
    print(f"   GITHUB_TOKEN exists: {github_token is not None}")
    print(f"   Using token: {'DASHBOARD_PAT' if dashboard_pat else 'GITHUB_TOKEN'}")
    print(f"   Token length: {len(token)}")
    print(f"   Token prefix: {token[:10]}..." if token else "No token")

    return {'Authorization': f'token {token}'}


def test_repository_access(headers: Dict[str, str], repo: str) -> bool:
    """Test access to a repository and its workflows."""
    print(f"\n🧪 Testing access to repository: {repo}")

    # Test basic repo access
    repo_url = f'https://api.github.com/repos/{repo}'
    repo_response = requests.get(repo_url, headers=headers)
    print(f"   Repository access: {repo_response.status_code}")

    if repo_response.status_code != 200:
        return False

    # Test workflow file access
    workflow_url = f'https://api.github.com/repos/{repo}/actions/workflows/sweep-build-matrix.yml'
    workflow_response = requests.get(workflow_url, headers=headers)
    print(f"   Workflow file access: {workflow_response.status_code}")

    # Test workflow runs
    url = f'https://api.github.com/repos/{repo}/actions/workflows/sweep-build-matrix.yml/runs'
    params = {'per_page': 15}  # Fetch more runs for better historical timeline

    print(f"   Testing workflow runs API...")
    print(f"   URL: {url}")
    print(f"   Params: {params}")

    response = requests.get(url, headers=headers, params=params)
    print(f"   Workflow runs status: {response.status_code}")

    if response.status_code == 200:
        repo_runs = response.json().get('workflow_runs', [])
        print(f"   ✅ Success! Found {len(repo_runs)} total workflow runs")

        if len(repo_runs) > 0:
            # Show run details
            print(f"   📊 All found runs:")
            for i, run in enumerate(repo_runs):
                status = run['conclusion'] or run['status']
                created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                print(f"     {i+1}. Run {run['id']} - {status} - {created_at.strftime('%Y-%m-%d %H:%M')} UTC")

            # Filter completed runs
            completed_runs = [r for r in repo_runs if r['conclusion'] in ['success', 'failure']]
            print(f"   ✅ {len(completed_runs)} completed runs (success/failure) will be processed")
            return len(completed_runs) > 0
        else:
            print(f"   ⚠️  No workflow runs found at all")
            return False
    else:
        print(f"   ❌ Error: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Error details: {error_detail}")
        except:
            print(f"   Error text: {response.text[:200]}")
        return False


def download_historical_runs(headers: Dict[str, str], repo: str, triggering_run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Download recent workflow runs and their artifacts."""
    url = f'https://api.github.com/repos/{repo}/actions/workflows/sweep-build-matrix.yml/runs'
    params = {'per_page': 25}  # Fetch more to ensure we get the triggering run

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to get workflow runs: {response.status_code}")
        return []

    repo_runs = response.json().get('workflow_runs', [])
    completed_runs = [r for r in repo_runs if r['conclusion'] in ['success', 'failure']]

    # If we have a triggering run ID, prioritize it
    runs = []
    if triggering_run_id:
        # Find the triggering run first
        triggering_run = next((r for r in completed_runs if str(r['id']) == str(triggering_run_id)), None)
        if triggering_run:
            runs.append(triggering_run)
            print(f"📌 Prioritizing triggering run: {triggering_run_id}")
        else:
            print(f"⚠️  Triggering run {triggering_run_id} not found in completed runs")

        # Add other recent runs
        other_runs = [r for r in completed_runs if str(r['id']) != str(triggering_run_id)]
        runs.extend(other_runs[:24])  # Up to 25 total (1 triggering + 24 others)
    else:
        runs = completed_runs[:25]  # Process up to 25 recent runs

    print(f"\n🎯 Found workflow runs in: {repo}")
    print(f"📊 Will process {len(runs)} recent runs for timeline")

    # Create runs directory and process runs
    os.makedirs('./runs', exist_ok=True)

    for i, run in enumerate(runs):
        run_id = run['id']
        sha = run['head_sha']
        created_at = run['created_at']
        conclusion = run['conclusion']

        print(f"\n{'='*70}")
        print(f"Processing run {i+1}/{len(runs)}: {run_id}")
        print(f"  SHA: {sha[:8]}")
        print(f"  Status: {conclusion}")
        print(f"  Created: {created_at}")
        print(f"{'='*70}")

        # Get artifacts for this run (with pagination support)
        artifacts = []
        page = 1
        per_page = 100  # Max allowed by GitHub API

        while True:
            artifacts_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts?per_page={per_page}&page={page}'
            artifacts_response = requests.get(artifacts_url, headers=headers)

            if artifacts_response.status_code != 200:
                print(f"  ❌ Failed to get artifacts (page {page}): {artifacts_response.status_code}")
                break

            page_artifacts = artifacts_response.json().get('artifacts', [])
            if not page_artifacts:
                break  # No more artifacts

            artifacts.extend(page_artifacts)
            print(f"  📄 Page {page}: {len(page_artifacts)} artifacts")

            # Check if there are more pages
            if len(page_artifacts) < per_page:
                break  # Last page

            page += 1

        print(f"  📦 Found {len(artifacts)} total artifacts for run {run_id} (across {page} page(s))")

        # Find sweep results artifact
        sweep_artifact = None
        print(f"  🔍 Looking for sweep-results artifact...")
        for artifact in artifacts:
            print(f"    - {artifact['name']}")
            if artifact['name'].startswith('sweep-results-'):
                sweep_artifact = artifact
                print(f"    ✅ Found sweep results artifact!")
                break

        if sweep_artifact:
            print(f"  📥 Downloading sweep results: {sweep_artifact['name']}")

            # Download artifact
            download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{sweep_artifact['id']}/zip"
            download_response = requests.get(download_url, headers=headers)

            if download_response.status_code == 200:
                # Save artifact zip
                artifact_path = f'./runs/run-{run_id}.zip'
                with open(artifact_path, 'wb') as f:
                    f.write(download_response.content)

                # Extract zip
                with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
                    zip_ref.extractall(f'./runs/run-{run_id}')

                # Move results.json to a standardized location
                results_src = f'./runs/run-{run_id}/results.json'
                if os.path.exists(results_src):
                    results_dst = f'./runs/results-{run_id}.json'
                    with open(results_src, 'r') as f:
                        results_data = json.load(f)
                    shutil.move(results_src, results_dst)
                    print(f"  ✅ Saved results-{run_id}.json ({len(results_data)} results)")
                else:
                    print(f"  ❌ No results.json found in artifact")
                    print(f"  📂 Artifact contents:")
                    for root, dirs, files in os.walk(f'./runs/run-{run_id}'):
                        for file in files:
                            print(f"    - {os.path.join(root, file)}")

                # Clean up zip file and extracted directory
                os.remove(artifact_path)
                if os.path.exists(f'./runs/run-{run_id}'):
                    shutil.rmtree(f'./runs/run-{run_id}')
            else:
                print(f"  ❌ Failed to download artifact: {download_response.status_code}")
                print(f"  Response: {download_response.text[:200]}")
        else:
            print(f"  ⚠️  No sweep-results artifact found for run {run_id}")
            print(f"  💡 This run may not have completed the collate step")
            print(f"  🔧 Attempting to merge chunk artifacts manually...")

            # Find all chunk artifacts for this run
            chunk_artifacts = [a for a in artifacts if a['name'].startswith('results-') and '-chunk-' in a['name']]

            if chunk_artifacts:
                print(f"  📦 Found {len(chunk_artifacts)} chunk artifacts to merge")
                merged_results = []
                temp_dir = f'./runs/temp-merge-{run_id}'
                os.makedirs(temp_dir, exist_ok=True)

                try:
                    for i, chunk_artifact in enumerate(chunk_artifacts):
                        print(f"    📥 Downloading chunk {i+1}/{len(chunk_artifacts)}: {chunk_artifact['name']}")
                        download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{chunk_artifact['id']}/zip"
                        download_response = requests.get(download_url, headers=headers)

                        if download_response.status_code == 200:
                            chunk_zip_path = f'{temp_dir}/chunk-{i}.zip'
                            chunk_extract_dir = f'{temp_dir}/chunk-{i}'

                            # Save and extract chunk
                            with open(chunk_zip_path, 'wb') as f:
                                f.write(download_response.content)

                            with zipfile.ZipFile(chunk_zip_path, 'r') as zip_ref:
                                zip_ref.extractall(chunk_extract_dir)

                            # Find and load results.json from this chunk
                            results_file = os.path.join(chunk_extract_dir, 'results.json')
                            if os.path.exists(results_file):
                                with open(results_file, 'r') as f:
                                    chunk_results = json.load(f)
                                    if isinstance(chunk_results, list):
                                        merged_results.extend(chunk_results)
                                        print(f"      ✅ Loaded {len(chunk_results)} results from chunk")
                                    else:
                                        print(f"      ⚠️  Chunk results is not a list: {type(chunk_results)}")
                            else:
                                print(f"      ⚠️  No results.json found in chunk")

                            # Clean up chunk files
                            os.remove(chunk_zip_path)
                            shutil.rmtree(chunk_extract_dir)
                        else:
                            print(f"      ❌ Failed to download chunk: {download_response.status_code}")

                    # Save merged results
                    if merged_results:
                        results_dst = f'./runs/results-{run_id}.json'
                        with open(results_dst, 'w') as f:
                            json.dump(merged_results, f)
                        print(f"  ✅ Manually merged {len(merged_results)} total results from {len(chunk_artifacts)} chunks")
                    else:
                        print(f"  ⚠️  No results found in any chunks")

                finally:
                    # Clean up temp directory
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                print(f"  ❌ No chunk artifacts found either - run has no results data")

    return runs


def print_fallback_message():
    """Print fallback message when PAT is not available."""
    print()
    print(f"🔧 To enable historical runs timeline:")
    print(f"   1. Create Personal Access Token with 'actions:read' scope")
    print(f"   2. Add as repository secret named 'DASHBOARD_PAT'")
    print(f"   3. Re-run workflow to access historical data")
    print(f"   4. Timeline will show last 10 workflow runs with full details")


def main():
    """Main function to download historical runs."""
    env_vars = get_environment_variables()

    # Get triggering run ID if available (workflow_run event)
    triggering_run_id = os.environ.get('TRIGGERING_RUN_ID')

    print("🔍 Downloading historical workflow runs...")
    print(f"   Repository: {env_vars['current_repo']}")
    print(f"   Event: {env_vars.get('github_event_name', 'unknown')}")
    print(f"   Actor: {env_vars.get('github_actor', 'unknown')}")
    if triggering_run_id:
        print(f"   Triggering run ID: {triggering_run_id}")

    headers = setup_authentication(env_vars['dashboard_pat'], env_vars['github_token'])

    # Focus on upstream since that's where workflows run
    possible_repos = [
        'NVIDIA-AI-IOT/jetson-containers',  # Upstream repo where workflows run
    ]

    print(f"\n🔍 Will test access to repositories:")
    for repo in possible_repos:
        print(f"  - {repo}")

    successful_repo = None
    runs = []

    for repo in possible_repos:
        if test_repository_access(headers, repo):
            # Test successful, try to get runs
            try:
                runs = download_historical_runs(headers, repo, triggering_run_id)
                if runs:
                    successful_repo = repo
                    break
            except Exception as e:
                print(f"   ❌ Error downloading runs: {e}")
                import traceback
                traceback.print_exc()
                continue

    if not successful_repo:
        print(f"\n❌ Could not access historical workflow runs from any repository")
        print(f"💡 This is likely due to:")
        print(f"   1. DASHBOARD_PAT not configured or lacks 'actions:read' scope")
        print(f"   2. Cross-repository access limitations")
        print(f"   3. Workflow runs not found or expired")
        print_fallback_message()

        # Create empty runs directory
        os.makedirs('./runs', exist_ok=True)
    else:
        print(f"\n✅ Successfully downloaded {len(runs)} historical runs from {successful_repo}")

    print(f"\nCompleted historical runs download")


if __name__ == '__main__':
    main()
