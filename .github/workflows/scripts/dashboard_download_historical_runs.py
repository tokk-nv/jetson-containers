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
            print(f"   📊 Recent runs:")
            for i, run in enumerate(repo_runs[:5]):
                status = run['conclusion'] or run['status']
                created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                print(f"     {i+1}. Run {run['id']} - {status} - {created_at.strftime('%Y-%m-%d %H:%M')} UTC")
            
            # Filter completed runs
            completed_runs = [r for r in repo_runs if r['conclusion'] in ['success', 'failure']]
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


def download_historical_runs(headers: Dict[str, str], repo: str) -> List[Dict[str, Any]]:
    """Download recent workflow runs and their artifacts."""
    url = f'https://api.github.com/repos/{repo}/actions/workflows/sweep-build-matrix.yml/runs'
    params = {'per_page': 15}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Failed to get workflow runs: {response.status_code}")
        return []
    
    repo_runs = response.json().get('workflow_runs', [])
    completed_runs = [r for r in repo_runs if r['conclusion'] in ['success', 'failure']]
    runs = completed_runs[:10]  # Process up to 10 recent runs
    
    print(f"\n🎯 Found workflow runs in: {repo}")
    print(f"📊 Will process {len(runs)} recent runs for timeline")
    
    # Create runs directory and process runs
    os.makedirs('./runs', exist_ok=True)
    
    for i, run in enumerate(runs):
        run_id = run['id']
        sha = run['head_sha']
        created_at = run['created_at']
        conclusion = run['conclusion']
        
        print(f"\nProcessing run {i+1}: {run_id} (SHA: {sha[:8]}, Status: {conclusion})")
        
        # Get artifacts for this run
        artifacts_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts'
        artifacts_response = requests.get(artifacts_url, headers=headers)
        
        if artifacts_response.status_code != 200:
            print(f"  ❌ Failed to get artifacts: {artifacts_response.status_code}")
            continue
        
        artifacts = artifacts_response.json().get('artifacts', [])
        
        # Find sweep results artifact
        sweep_artifact = None
        for artifact in artifacts:
            if artifact['name'].startswith('sweep-results-'):
                sweep_artifact = artifact
                break
        
        if sweep_artifact:
            print(f"  Found sweep results artifact: {sweep_artifact['name']}")
            
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
                    shutil.move(results_src, results_dst)
                    print(f"  ✅ Saved results-{run_id}.json")
                else:
                    print(f"  ❌ No results.json found in artifact")
                
                # Clean up zip file and extracted directory
                os.remove(artifact_path)
                if os.path.exists(f'./runs/run-{run_id}'):
                    shutil.rmtree(f'./runs/run-{run_id}')
            else:
                print(f"  ❌ Failed to download artifact: {download_response.status_code}")
        else:
            print(f"  ❌ No sweep results artifact found")
    
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
    
    print("🔍 Testing cross-repository access for historical runs...")
    print(f"   Current repository: {env_vars.get('current_repo', 'unknown')}")
    print(f"   Triggered by: {env_vars.get('github_event_name', 'unknown')}")
    print(f"   Repository: {env_vars['current_repo']}")
    print(f"   Event: {env_vars.get('github_event_name', 'unknown')}")
    print(f"   Actor: {env_vars.get('github_actor', 'unknown')}")
    
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
                runs = download_historical_runs(headers, repo)
                if runs:
                    successful_repo = repo
                    break
            except Exception as e:
                print(f"   ❌ Error downloading runs: {e}")
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
    
    print(f"\nCompleted repository access test")


if __name__ == '__main__':
    main()
