#!/usr/bin/env python3
"""
Generate markdown build report for build results.

This script creates a comprehensive markdown report with statistics,
platform breakdown, and detailed results table.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any


def load_results(run_id: str = None) -> List[Dict[str, Any]]:
    """Load build results from a specific run or the latest run."""
    runs_dir = './runs'

    if not os.path.exists(runs_dir):
        print(f"❌ No runs directory found at {runs_dir}")
        return []

    # If specific run ID provided, load that run
    if run_id:
        results_file = os.path.join(runs_dir, f'results-{run_id}.json')
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
                print(f"✅ Loaded results for run {run_id}")
                return results
        except FileNotFoundError:
            print(f"❌ No results found for run {run_id} at {results_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {results_file}: {e}")
            return []

    # Otherwise, load the most recent run
    results_files = sorted([f for f in os.listdir(runs_dir) if f.startswith('results-') and f.endswith('.json')])

    if not results_files:
        print(f"❌ No results files found in {runs_dir}")
        return []

    # Sort by modification time to get the latest
    results_files_with_time = [(f, os.path.getmtime(os.path.join(runs_dir, f))) for f in results_files]
    results_files_with_time.sort(key=lambda x: x[1], reverse=True)
    latest_file = results_files_with_time[0][0]
    latest_run_id = latest_file.replace('results-', '').replace('.json', '')

    try:
        results_path = os.path.join(runs_dir, latest_file)
        with open(results_path, 'r') as f:
            results = json.load(f)
            print(f"✅ Loaded latest run: {latest_run_id} ({len(results)} results)")
            return results
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {latest_file}: {e}")
        return []


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate build statistics."""
    total = len(results)
    if total == 0:
        return {
            'total': 0, 'success': 0, 'failed': 0, 'timeout': 0, 'oom': 0,
            'success_rate': 0, 'run_id': 'unknown', 'run_url': '#',
            'sha': 'unknown', 'timestamp': 0
        }

    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'build_fail')
    timeout = sum(1 for r in results if r['status'] == 'timeout')
    oom = sum(1 for r in results if r['status'] == 'oom_killed')

    success_rate = (success / total * 100) if total > 0 else 0

    # Get run info from first result
    run_id = results[0]['run_id'] if results else 'unknown'
    run_url = results[0]['run_url'] if results else '#'
    sha = results[0]['sha'] if results else 'unknown'
    timestamp = results[0]['timestamp'] if results else 0

    return {
        'total': total,
        'success': success,
        'failed': failed,
        'timeout': timeout,
        'oom': oom,
        'success_rate': success_rate,
        'run_id': run_id,
        'run_url': run_url,
        'sha': sha,
        'timestamp': timestamp
    }


def calculate_platform_breakdown(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate statistics by platform."""
    platforms = {}

    for r in results:
        platform = r.get('runner_label', 'unknown')
        if platform not in platforms:
            platforms[platform] = {
                'total': 0, 'success': 0, 'failed': 0, 'timeout': 0, 'oom': 0
            }

        platforms[platform]['total'] += 1
        if r['status'] == 'success':
            platforms[platform]['success'] += 1
        elif r['status'] == 'build_fail':
            platforms[platform]['failed'] += 1
        elif r['status'] == 'timeout':
            platforms[platform]['timeout'] += 1
        elif r['status'] == 'oom_killed':
            platforms[platform]['oom'] += 1

    return platforms


def generate_markdown_report(results: List[Dict[str, Any]]) -> str:
    """Generate the complete markdown report."""

    stats = calculate_statistics(results)
    platforms = calculate_platform_breakdown(results)

    # Generate markdown
    md = f'''# 🚀 Jetson Containers Build Report

**Generated:** {datetime.fromtimestamp(stats['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC') if stats['timestamp'] else 'Unknown'}
**Run ID:** [{stats['run_id']}]({stats['run_url']})
**SHA:** `{stats['sha'][:8]}`

## 📊 Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Success | {stats['success']} | {(stats['success']/stats['total']*100) if stats['total'] > 0 else 0:.1f}% |
| ❌ Failed | {stats['failed']} | {(stats['failed']/stats['total']*100) if stats['total'] > 0 else 0:.1f}% |
| ⏰ Timeout | {stats['timeout']} | {(stats['timeout']/stats['total']*100) if stats['total'] > 0 else 0:.1f}% |
| 💥 OOM Killed | {stats['oom']} | {(stats['oom']/stats['total']*100) if stats['total'] > 0 else 0:.1f}% |
| **Total** | **{stats['total']}** | **100.0%** |

**Overall Success Rate:** {stats['success_rate']:.1f}%

## 🖥️ Platform Breakdown

'''

    for platform, platform_stats in platforms.items():
        platform_success_rate = (platform_stats['success'] / platform_stats['total'] * 100) if platform_stats['total'] > 0 else 0
        md += f'''
### {platform.upper()}

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Success | {platform_stats['success']} | {(platform_stats['success']/platform_stats['total']*100) if platform_stats['total'] > 0 else 0:.1f}% |
| ❌ Failed | {platform_stats['failed']} | {(platform_stats['failed']/platform_stats['total']*100) if platform_stats['total'] > 0 else 0:.1f}% |
| ⏰ Timeout | {platform_stats['timeout']} | {(platform_stats['timeout']/platform_stats['total']*100) if platform_stats['total'] > 0 else 0:.1f}% |
| 💥 OOM Killed | {platform_stats['oom']} | {(platform_stats['oom']/platform_stats['total']*100) if platform_stats['total'] > 0 else 0:.1f}% |
| **Total** | **{platform_stats['total']}** | **100.0%** |

**Success Rate:** {platform_success_rate:.1f}%

'''

    md += '''
## 📦 Detailed Results

| Package | Tag | Platform | Status | Failure Point | Duration (s) | Log |
|---------|-----|----------|--------|---------------|--------------|-----|
'''

    for r in results:
        status_emoji = {
            'success': '✅',
            'build_fail': '❌',
            'timeout': '⏰',
            'oom_killed': '💥'
        }.get(r['status'], '❓')

        md += f"| {r['package']} | {r['tag']} | {r.get('runner_label', 'unknown')} | {status_emoji} {r['status']} | {r['failure_point']} | {r['duration_s']} | [View]({r['run_url']}) |\n"

    return md


def main(run_id: str = None):
    """Main function to generate markdown report."""
    print("📋 Generating markdown build report...")

    # Load results from specific run or latest run
    if run_id:
        print(f"🎯 Generating report for run: {run_id}")
    else:
        print("🎯 Generating report for latest run")

    results = load_results(run_id)
    if not results:
        print("⚠️ No results available - generating empty report")
        # Create empty results for fallback
        results = []

    print(f"📊 Processing {len(results)} build results...")

    # Generate markdown
    md = generate_markdown_report(results)

    # Write markdown file
    with open('./build-report.md', 'w') as f:
        f.write(md)

    print(f"✅ Generated markdown report with {len(results)} results")
    print(f"📁 Output: ./build-report.md")


if __name__ == '__main__':
    main()
