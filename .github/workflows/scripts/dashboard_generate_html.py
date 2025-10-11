#!/usr/bin/env python3
"""
Generate interactive HTML dashboard for build results.

This script creates a comprehensive dashboard with historical timeline,
filtering, search, and detailed log access capabilities.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Configuration constants
TIMELINE_RUNS_LIMIT = 25  # Number of runs to show in timeline
MIN_MARKER_SPACING = 3.0  # Minimum spacing between timeline markers in percentage




def load_historical_runs() -> List[Dict[str, Any]]:
    """Load historical run data for timeline."""
    available_runs = []
    runs_dir = './runs'

    print(f"🔍 Looking for historical runs in: {runs_dir}")
    if not os.path.exists(runs_dir):
        print("❌ No runs directory found - no historical data available")
        return []

    files = os.listdir(runs_dir)
    results_files = [f for f in files if f.startswith('results-') and f.endswith('.json')]
    print(f"📄 Found {len(files)} total files, {len(results_files)} results files: {results_files}")

    for filename in results_files:
        run_id = filename.replace('results-', '').replace('.json', '')
        try:
            with open(os.path.join(runs_dir, filename), 'r') as f:
                run_data = json.load(f)
            if run_data:
                available_runs.append({
                    'run_id': run_id,
                    'sha': run_data[0]['sha'],
                    'timestamp': run_data[0]['timestamp'],
                    'total': len(run_data),
                    'success': sum(1 for r in run_data if r['status'] == 'success'),
                    'failed': sum(1 for r in run_data if r['status'] == 'build_fail'),
                    'started': sum(1 for r in run_data if r['status'] == 'started'),
                    'timeout': sum(1 for r in run_data if r['status'] == 'timeout'),
                    'oom': sum(1 for r in run_data if r['status'] == 'oom_killed'),
                    'results': run_data  # Include the actual results data
                })
                print(f"✅ Loaded run {run_id} with {len(run_data)} results")
            else:
                # Skip empty files - they don't provide meaningful data for the dashboard
                print(f"⚠️ Skipping run {run_id} - no meaningful data (empty file)")
                continue
        except Exception as e:
            print(f"Error loading {filename}: {e}")


    # Sort runs by timestamp (newest first) - this will ensure current run is first
    available_runs.sort(key=lambda x: x['timestamp'], reverse=True)

    print(f"✅ Found {len(available_runs)} available runs for timeline")
    if len(available_runs) == 0:
        print("❌ No runs available - timeline will be empty")
        print("ℹ️  This is normal for the first few runs until we build up history")
    else:
        print(f"📊 Timeline will show: {[r['run_id'] for r in available_runs[:5]]}...")
    print(f"🎯 Total runs that will appear in dashboard: {len(available_runs)}")

    return available_runs


def generate_dashboard_html(available_runs: List[Dict[str, Any]]) -> str:
    """Generate the complete HTML dashboard."""

    # Get current run info (most recent run, which is first in the list)
    current_run = available_runs[0] if available_runs else None
    current_results = current_run.get('results', []) if current_run else []
    current_run_id = current_run['run_id'] if current_run else 'unknown'
    current_run_url = current_results[0]['run_url'] if current_results else '#'
    current_sha = current_results[0]['sha'] if current_results else 'unknown'
    current_timestamp = current_run['timestamp'] if current_run else 0

    # Get Publish Dashboard workflow run info for the footer
    # This shows which "Publish Dashboard" workflow generated this page
    publish_run_id = os.environ.get('PUBLISH_RUN_ID', 'unknown')
    publish_run_url = os.environ.get('PUBLISH_RUN_URL', '#')

    # Debug: Show log_relpath values from current results
    print(f"🔍 Debug: Current results log_relpath values:")
    for i, result in enumerate(current_results[:3]):
        log_path = result.get('log_relpath', 'N/A')
        runner = result.get('runner_label', result.get('runner', 'unknown'))
        print(f"  {i+1}. {result['package']} ({runner}): {log_path}")

    # Check which log files actually exist to prevent 404 links
    print(f"\n📂 Checking existence of log files...")
    import re
    logs_missing = 0
    logs_found = 0

    for run in available_runs:
        run_id = run['run_id']
        for result in run.get('results', []):
            if result.get('log_relpath'):
                # Reconstruct the expected log filename (matching JavaScript URL generation logic)
                runner_label = result.get('runner_label') or result.get('runner') or 'unknown'
                base_file_name = result['log_relpath'].replace('logs/', '').replace('.log', '')
                runner_suffix = '_' + re.sub(r'[^a-zA-Z0-9]', '-', runner_label)

                # Check for both HTML and log files
                log_file_html = f'./logs/run-{run_id}/{base_file_name}{runner_suffix}.html'
                log_file_log = f'./logs/run-{run_id}/{base_file_name}{runner_suffix}.log'

                if os.path.exists(log_file_html) or os.path.exists(log_file_log):
                    result['log_exists'] = True
                    logs_found += 1
                else:
                    result['log_exists'] = False
                    logs_missing += 1
            else:
                result['log_exists'] = False

    print(f"📊 Log file check: {logs_found} found, {logs_missing} missing")

    # Generate timeline items for available runs (mathematical axis approach)
    timeline_items = []

    # Calculate positions for timeline markers chronologically (oldest to newest)
    if available_runs:
        # Sort runs chronologically for timeline display (oldest first)
        timeline_runs = sorted(available_runs[:TIMELINE_RUNS_LIMIT], key=lambda x: x['timestamp'])

        # Use all run timestamps for range calculation
        all_timestamps = [run["timestamp"] for run in timeline_runs]
        oldest_timestamp = min(all_timestamps)
        newest_timestamp = max(all_timestamps)
        time_range = newest_timestamp - oldest_timestamp if newest_timestamp != oldest_timestamp else 86400  # Default to 1 day if same

        print(f"🕐 Timeline range: {time_range/86400:.1f} days ({oldest_timestamp} to {newest_timestamp})")
        print(f"📊 Timeline order: {[r['run_id'] for r in timeline_runs]} (oldest to newest)")

        # Calculate simple proportional positions (oldest=10%, newest=90%)
        positions = []
        if time_range > 0:
            for run in timeline_runs:
                time_ratio = (run["timestamp"] - oldest_timestamp) / time_range
                position_percent = 10 + (time_ratio * 80)  # 10% to 90% range
                positions.append(position_percent)
        else:
            # Fallback to equal spacing if timestamps are identical
            positions = [10 + (i * (80 / len(timeline_runs))) for i in range(len(timeline_runs))]

        for i, run in enumerate(timeline_runs):
            position_percent = positions[i]
            time_ratio = (run["timestamp"] - oldest_timestamp) / time_range if time_range > 0 else i / len(timeline_runs)
            print(f"   📍 Run {run['run_id']}: {time_ratio:.3f} ratio → {position_percent:.1f}% position")

            # Determine build health status
            if run["total"] == 0:
                # Cancelled runs with no data
                health_status = "cancelled"
                health_color = "#6c757d"  # Gray
                health_label = "Cancelled"
            else:
                success_rate = (run["success"] / run["total"]) * 100
                if success_rate == 100:
                    health_status = "perfect"
                    health_color = "#28a745"  # Green
                    health_label = "All Success"
                elif success_rate >= 80:
                    health_status = "good"
                    health_color = "#ffc107"  # Yellow
                    health_label = "Mostly Success"
                elif success_rate >= 50:
                    health_status = "partial"
                    health_color = "#8b5cf6"  # Purple
                    health_label = "Partial Failure"
                else:
                    health_status = "poor"
                    health_color = "#dc3545"  # Red
                    health_label = "Major Issues"

            # Check if this is the most recent run (last in chronologically sorted list)
            is_latest = (run["timestamp"] == newest_timestamp)
            marker_class = f"timeline-marker {'latest-run' if is_latest else ''}"

            timeline_item = f'''
                <div class="{marker_class}" data-run="{run["run_id"]}" style="left: {position_percent}%;">
                    <div class="marker-dot {health_status} {'latest' if is_latest else ''}" style="background-color: {health_color};"></div>
                    <div class="marker-popup">
                        <div class="popup-header">
                            <strong>Run {run["run_id"]}</strong>
                            <div class="popup-date" data-timestamp="{run["timestamp"]}"></div>
                        </div>
                        <div class="popup-stats">
                            <div class="stat-item">
                                <span class="stat-label">Status:</span>
                                <span class="stat-value {health_status}">{health_label}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Packages:</span>
                                <span class="stat-value">{run["total"]} attempted</span>
                            </div>
                            <div class="stat-breakdown">
                                <span class="success-count">{run["success"]} ✅</span>
                                <span class="failed-count">{run["failed"]} ❌</span>
                                {f'<span class="started-count">{run.get("started", 0)} 🔄</span>' if run.get("started", 0) > 0 else ''}
                                {f'<span class="timeout-count">{run.get("timeout", 0)} ⏱️</span>' if run.get("timeout", 0) > 0 else ''}
                                {f'<span class="oom-count">{run.get("oom", 0)} 💥</span>' if run.get("oom", 0) > 0 else ''}
                            </div>
                        </div>
                    </div>
                </div>'''
            timeline_items.append(timeline_item)

    timeline_html = ''.join(timeline_items)

    # Generate run options for select dropdown
    run_options = []
    for i, run in enumerate(available_runs):
        # Mark the first (most recent) run as selected and add 🆕 emoji
        selected = 'selected' if i == 0 else ''
        emoji = ' 🆕' if i == 0 else ''
        option = f'<option value="{run["run_id"]}" data-timestamp="{run["timestamp"]}" {selected}>Run {run["run_id"]}{emoji}</option>'
        run_options.append(option)

    run_options_html = ''.join(run_options)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jetson Containers Build Dashboard</title>
    <!-- Chart.js for enhanced timeline visualization -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@2.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #212529;
            font-weight: 600;
        }}

        .run-selector {{
            padding: 20px;
            background: #e3f2fd;
            border-bottom: 1px solid #bbdefb;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .run-select {{
            padding: 10px;
            border: 1px solid #2196f3;
            border-radius: 4px;
            font-size: 14px;
            background: white;
            min-width: 200px;
        }}

        .run-info {{
            font-size: 14px;
            color: #1976d2;
        }}

        .timeline {{
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}

        .timeline-axis-container {{
            position: relative;
            width: 100%;
            height: 80px;
            margin: 20px 0;
        }}

        .timeline-axis {{
            position: relative;
            width: 100%;
            height: 100%;
        }}

        .axis-line {{
            position: absolute;
            top: 40px;
            left: 2%;
            right: 2%;
            height: 2px;
            background: linear-gradient(to right, #6c757d, #007bff);
            border-radius: 1px;
        }}

        .axis-line::after {{
            content: '';
            position: absolute;
            right: -6px;
            top: -3px;
            width: 0;
            height: 0;
            border-left: 8px solid #007bff;
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }}

        .axis-labels {{
            position: absolute;
            top: 55px;
            left: 2%;
            right: 2%;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #6c757d;
            font-weight: 500;
        }}

        .timeline-marker {{
            position: absolute;
            top: 30px;
            transform: translateX(-50%);
            cursor: pointer;
            z-index: 10;
        }}

        .marker-dot {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            position: relative;
        }}

        .marker-dot.perfect {{
            background: #28a745;
            box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.3);
        }}

        .marker-dot.good {{
            background: #ffc107;
            box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3);
        }}

        .marker-dot.partial {{
            background: #8b5cf6;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3);
        }}

        .marker-dot.poor {{
            background: #dc3545;
            box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.3);
        }}

        .marker-dot.cancelled {{
            background: #6c757d;
            box-shadow: 0 0 0 3px rgba(108, 117, 125, 0.3);
            opacity: 0.7;
        }}

        .marker-dot.current {{
            background: #007bff;
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
            animation: pulse 2s infinite;
        }}

        .marker-dot.latest {{
            width: 24px;
            height: 24px;
            border: 4px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transform: scale(1.1);
        }}

        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3); }}
            50% {{ box-shadow: 0 0 0 6px rgba(0, 123, 255, 0.1); }}
            100% {{ box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3); }}
        }}

        .timeline-marker:hover .marker-dot {{
            transform: scale(1.2);
        }}

        .marker-popup {{
            position: absolute;
            bottom: 35px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 12px;
            min-width: 200px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 20;
        }}

        .timeline-marker:hover .marker-popup {{
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) translateY(-5px);
        }}

        .popup-header {{
            margin-bottom: 8px;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 6px;
        }}

        .popup-header strong {{
            color: #495057;
            font-size: 14px;
        }}

        .popup-date {{
            font-size: 11px;
            color: #6c757d;
            margin-top: 2px;
        }}

        .popup-stats {{
            font-size: 12px;
        }}

        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
        }}

        .stat-label {{
            color: #212529;
            font-weight: 600;
        }}

        .stat-value {{
            font-weight: 600;
        }}

        .stat-value.perfect {{ color: #28a745; }}
        .stat-value.good {{ color: #ffc107; }}
        .stat-value.partial {{ color: #8b5cf6; }}
        .stat-value.poor {{ color: #dc3545; }}

        .stat-breakdown {{
            display: flex;
            gap: 8px;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid #f8f9fa;
            font-size: 11px;
        }}

        .stat-breakdown span {{
            font-weight: 500;
        }}

        .success-count {{ color: #28a745; }}
        .failed-count {{ color: #dc3545; }}
        .timeout-count {{ color: #ffc107; }}
        .oom-count {{ color: #8b5cf6; }}

        /* Legacy timeline classes for backward compatibility */
        .timeline-item {{
            display: none; /* Hide old timeline items */
        }}

        .timeline-date {{
            display: none;
        }}

        .timeline-stats {{
            display: none;
        }}

        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 200px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}

        .filter-select {{
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background: white;
        }}

        .table-container {{
            overflow-x: auto;
            /* Removed max-height and overflow-y to prevent double scrollbars */
            /* Let the main window handle vertical scrolling */
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th {{
            background: #f8f9fa;
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }}

        /* Right-align Duration column (5th column) */
        th:nth-child(5), td:nth-child(5) {{
            text-align: right;
        }}

        tr:hover {{
            background-color: #f8f9fa;
        }}

        .status {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status.success {{
            background-color: #d4edda;
            color: #155724;
        }}

        .status.build_fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}

        .status.timeout {{
            background-color: #fff3cd;
            color: #856404;
        }}

        .status.oom_killed {{
            background-color: #f5c6cb;
            color: #721c24;
        }}

        .package-name {{
            font-weight: 600;
            color: #495057;
        }}

        .tag {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-family: monospace;
        }}

        .duration {{
            font-family: monospace;
            font-size: 13px;
        }}

        .failure-point {{
            max-width: 200px;
            word-wrap: break-word;
            font-size: 12px;
            color: #6c757d;
        }}

        .platform {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .platform-orin {{
            background: linear-gradient(135deg, #059669 0%, #10a0b9 100%);
            color: white;
        }}

        .platform-thor {{
            background: linear-gradient(135deg, #3a3ded 0%, #791d95 100%);
            color: white;
        }}

        .platform-unknown {{
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
        }}

        .runner {{
            font-family: monospace;
            font-size: 12px;
            color: #6c757d;
        }}

        .loading {{
            text-align: center;
            padding: 50px;
            color: #6c757d;
        }}

        .error {{
            text-align: center;
            padding: 50px;
            color: #dc3545;
        }}

        .pagination {{
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}

        .pagination button {{
            margin: 0 5px;
            padding: 8px 12px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
        }}

        .pagination button:hover {{
            background: #e9ecef;
        }}

        .pagination button.active {{
            background: #007bff;
            color: white;
            border-color: #007bff;
        }}

        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e0e0e0;
            background: #f8f9fa;
        }}

        .comparison {{
            display: none;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}

        .comparison.active {{
            display: block;
        }}

        .comparison-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .comparison-stat {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            text-align: center;
        }}

        .comparison-stat h4 {{
            margin: 0 0 10px 0;
            color: #495057;
        }}

        .comparison-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Jetson Containers Build Dashboard</h1>
            <div class="stats" id="stats">
                <div class="stat">
                    <span class="stat-number" id="total-packages">-</span>
                    <span class="stat-label">Total Packages</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="success-count">-</span>
                    <span class="stat-label">Successful</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="failed-count">-</span>
                    <span class="stat-label">Failed</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="timeout-count">-</span>
                    <span class="stat-label">Timeouts</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="oom-count">-</span>
                    <span class="stat-label">OOM Killed</span>
                </div>
                <div class="stat">
                    <span class="stat-number" id="success-rate">-</span>
                    <span class="stat-label">Success Rate</span>
                </div>
            </div>
        </div>

        <div class="run-selector">
            <label for="run-select"><strong>Select Run:</strong></label>
            <select id="run-select" class="run-select">
                {run_options_html}
            </select>
            <div class="run-info" id="run-info" data-timestamp="{current_timestamp}">
                SHA: {current_sha[:8]} | Generated: <span class="timestamp-display"></span>
            </div>
        </div>

        <div class="timeline" id="timeline">
            <div style="font-weight: bold; margin-bottom: 15px; color: #495057;">📊 Recent Runs Timeline:</div>

            <!-- Enhanced Chart.js Timeline -->
            <div class="chart-container" style="position: relative; height: 300px; width: 100%; min-width: 1000px; margin: 20px 0; overflow-x: auto;">
                <canvas id="timelineChart" style="min-width: 1000px;"></canvas>
            </div>

            <!-- Fallback: Original timeline for compatibility -->
            <div class="timeline-axis-container" id="fallback-timeline" style="display: none;">
                <div class="timeline-axis">
                    <div class="axis-line"></div>
                    <div class="axis-labels">
                        <span class="axis-label-left">Oldest</span>
                        <span class="axis-label-right">Latest</span>
                    </div>
                    {timeline_html}
                </div>
            </div>

            <div style="color: #6c757d; font-size: 12px; margin-top: 15px;">
                💡 Click on bars to view run details • Hover for statistics • Timeline shows last {TIMELINE_RUNS_LIMIT} runs
            </div>
        </div>

        <div class="comparison" id="comparison">
            <h3>Run Comparison</h3>
            <div class="comparison-stats" id="comparison-stats">
                <!-- Comparison stats will be populated here -->
            </div>
        </div>

        <div class="controls">
            <input type="text" id="search" class="search-box" placeholder="Search packages, tags, or failure points...">
            <select id="status-filter" class="filter-select">
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="build_fail">Build Fail</option>
                <option value="timeout">Timeout</option>
                <option value="oom_killed">OOM Killed</option>
            </select>
            <select id="platform-filter" class="filter-select">
                <option value="">All Platforms</option>
            </select>
            <select id="runner-filter" class="filter-select">
                <option value="">All Runners</option>
            </select>
            <select id="sort-by" class="filter-select">
                <option value="package">Sort by Package</option>
                <option value="platform">Sort by Platform</option>
                <option value="status">Sort by Status</option>
                <option value="duration_s">Sort by Duration</option>
                <option value="timestamp">Sort by Time</option>
            </select>
            <button id="compare-btn" class="filter-select" style="background: #28a745; color: white; border-color: #28a745;">
                Compare Runs
            </button>
        </div>

        <div class="table-container">
            <div id="loading" class="loading">Loading results...</div>
            <div id="error" class="error" style="display: none;">Error loading results.json</div>
            <table id="results-table" style="display: none;">
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Tag</th>
                        <th>Platform</th>
                        <th>Runner</th>
                        <th style="text-align: left;">Status</th>
                        <th>Duration</th>
                        <th>Failure Point</th>
                        <th>Log</th>
                    </tr>
                </thead>
                <tbody id="results-tbody">
                </tbody>
            </table>
        </div>

        <div class="pagination" id="pagination" style="display: none;">
            <button id="prev-page" onclick="changePage(-1)">Previous</button>
            <span id="page-info">Page 1 of 1</span>
            <button id="next-page" onclick="changePage(1)">Next</button>
        </div>

        <div class="footer">
            <p>Generated on <span class="timestamp-display" data-timestamp="{current_timestamp}"></span></p>
            <p>Run ID: <a href="{publish_run_url}" target="_blank">{publish_run_id}</a> | SHA: {current_sha[:8]}</p>
        </div>
    </div>

    <script>
        let allResults = [];
        let filteredResults = [];
        let currentPage = 1;
        let currentRun = 'current';
        const itemsPerPage = 50;

        // Timestamp formatting functions
        function formatTimestamp(timestamp) {{
            if (!timestamp) return 'Unknown';
            const date = new Date(timestamp * 1000);
            const options = {{
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
            }};
            return date.toLocaleString(undefined, options);
        }}

        function formatTimelineDate(timestamp) {{
            if (!timestamp) return 'Unknown';
            const date = new Date(timestamp * 1000);
            const options = {{
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZoneName: 'short'
            }};
            return date.toLocaleString(undefined, options);
        }}

        function formatRunOptionDate(timestamp) {{
            if (!timestamp) return '';
            const date = new Date(timestamp * 1000);
            const options = {{
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZoneName: 'short'
            }};
            return ' - ' + date.toLocaleString(undefined, options);
        }}

        // Function to format duration in compact h m s format
        function formatDuration(seconds) {{
            if (!seconds || seconds < 0) return '0 s';

            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);

            let result = [];

            if (hours > 0) {{
                result.push(hours + ' h');
            }}
            if (minutes > 0) {{
                result.push(minutes + ' m');
            }}
            if (secs > 0 || result.length === 0) {{
                result.push(secs + ' s');
            }}

            return result.join(' ');
        }}

        // Initialize timestamp displays on page load
        function initializeTimestamps() {{
            // Update all timeline popup dates
            document.querySelectorAll('.popup-date[data-timestamp]').forEach(element => {{
                const timestamp = parseFloat(element.getAttribute('data-timestamp'));
                element.textContent = formatTimelineDate(timestamp);
            }});

            // Update all timestamp displays
            document.querySelectorAll('.timestamp-display[data-timestamp]').forEach(element => {{
                const timestamp = parseFloat(element.getAttribute('data-timestamp'));
                element.textContent = formatTimestamp(timestamp);
            }});

            // Update run selector options with local times
            document.querySelectorAll('#run-select option[data-timestamp]').forEach(option => {{
                const timestamp = parseFloat(option.getAttribute('data-timestamp'));
                const runId = option.value;
                const isSelected = option.hasAttribute('selected');
                const emoji = isSelected ? ' 🆕' : '';
                option.textContent = `Run ${{runId}}${{formatRunOptionDate(timestamp)}}${{emoji}}`;
            }});

            // Update current run info
            updateRunInfo(currentRun);
        }}

        // Available runs data
        const availableRuns = {json.dumps(available_runs, separators=(',', ':'))};

        // Chart.js timeline chart
        let timelineChart = null;

        function initializeTimelineChart() {{
            // Check if Chart.js is loaded
            if (typeof Chart === 'undefined') {{
                throw new Error('Chart.js is not loaded');
            }}

            console.log('Chart.js version:', Chart.version);
            console.log('Available runs for chart:', availableRuns.length);

            const ctx = document.getElementById('timelineChart').getContext('2d');
            console.log('Chart container width:', ctx.canvas.clientWidth);
            console.log('Chart container height:', ctx.canvas.clientHeight);

            // Prepare data for Chart.js - back to time scale for proportional positioning
            const chartData = availableRuns.slice(0, {TIMELINE_RUNS_LIMIT}).map(run => {{
                const date = new Date(run.timestamp * 1000);
                return {{
                    x: date,  // Use actual date for proportional positioning
                    runId: run.run_id,
                    success: run.success,
                    failed: run.failed,
                    timeout: run.timeout || 0,
                    oom: run.oom || 0,
                    started: run.started || 0,
                    total: run.total,
                    sha: run.sha
                }};
            }});

            // Sort chronologically (oldest to newest for proper display)
            chartData.sort((a, b) => a.x - b.x);

            timelineChart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    datasets: [
                        {{
                            label: 'Success',
                            data: chartData.map(d => ({{ x: d.x, y: d.success, runData: d }})),
                            backgroundColor: '#28a745',
                            borderColor: '#1e7e34',
                            borderWidth: 1,
                            stack: 'builds'
                        }},
                        {{
                            label: 'Failed',
                            data: chartData.map(d => ({{ x: d.x, y: d.failed, runData: d }})),
                            backgroundColor: '#dc3545',
                            borderColor: '#c82333',
                            borderWidth: 1,
                            stack: 'builds'
                        }},
                        {{
                            label: 'Timeout',
                            data: chartData.map(d => ({{ x: d.x, y: d.timeout, runData: d }})),
                            backgroundColor: '#ffc107',
                            borderColor: '#e0a800',
                            borderWidth: 1,
                            stack: 'builds'
                        }},
                        {{
                            label: 'OOM',
                            data: chartData.map(d => ({{ x: d.x, y: d.oom, runData: d }})),
                            backgroundColor: '#8b5cf6',
                            borderColor: '#7c3aed',
                            borderWidth: 1,
                            stack: 'builds'
                        }},
                        {{
                            label: 'Started',
                            data: chartData.map(d => ({{ x: d.x, y: d.started, runData: d }})),
                            backgroundColor: '#6c757d',
                            borderColor: '#5a6268',
                            borderWidth: 1,
                            stack: 'builds'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    elements: {{
                        bar: {{
                            barThickness: 80,      // Very thick bars - 80px
                            maxBarThickness: 100,  // Maximum thickness
                            minBarLength: 2        // Minimum bar length for visibility
                        }}
                    }},
                    plugins: {{
                        title: {{
                            display: false
                        }},
                        legend: {{
                            display: true,
                            position: 'top',
                            labels: {{
                                usePointStyle: true,
                                padding: 20
                            }}
                        }},
                        tooltip: {{
                            position: 'nearest',
                            xAlign: function(tooltipItem) {{
                                const chart = tooltipItem.chart;
                                const dataPoint = tooltipItem.tooltip.dataPoints[0];
                                const barX = dataPoint.element.x;
                                const chartWidth = chart.width;
                                return barX < chartWidth / 2 ? 'left' : 'right';
                            }},
                            yAlign: 'center',
                            caretPadding: 10,
                            displayColors: false,  // Disable color boxes completely
                            callbacks: {{
                                title: function(context) {{
                                    const runData = context[0].raw.runData;
                                    return [
                                        `Run ${{runData.runId}}`,
                                        `${{runData.x.toLocaleDateString()}} ${{runData.x.toLocaleTimeString()}}`,
                                        `Total Packages: ${{runData.total}}`
                                    ];
                                }},
                                label: function(context) {{
                                    // Only show on first dataset to avoid duplication
                                    if (context.datasetIndex !== 0) return null;

                                    const runData = context.raw.runData;
                                    const total = runData.total;

                                    // Calculate percentages
                                    const successPct = total > 0 ? ((runData.success / total) * 100).toFixed(1) : '0.0';
                                    const failedPct = total > 0 ? ((runData.failed / total) * 100).toFixed(1) : '0.0';
                                    const timeoutPct = total > 0 ? ((runData.timeout / total) * 100).toFixed(1) : '0.0';
                                    const oomPct = total > 0 ? ((runData.oom / total) * 100).toFixed(1) : '0.0';
                                    const startedPct = total > 0 ? ((runData.started / total) * 100).toFixed(1) : '0.0';

                                    // Return array with all status lines
                                    return [
                                        `🟢 Success: ${{runData.success}} (${{successPct}}%)`,
                                        `🔴 Failed: ${{runData.failed}} (${{failedPct}}%)`,
                                        `🟡 Timeout: ${{runData.timeout}} (${{timeoutPct}}%)`,
                                        `🟣 OOM: ${{runData.oom}} (${{oomPct}}%)`,
                                        `⚪ Started: ${{runData.started}} (${{startedPct}}%)`
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'time',  // Back to time scale for proportional positioning
                            time: {{
                                unit: 'day',  // Use day units for cleaner display
                                displayFormats: {{
                                    day: 'MMM dd'
                                }}
                            }},
                            scaleLabel: {{
                                display: true,
                                labelString: 'Date'
                            }},
                            offset: true,  // Add offset to give bars more space
                            barPercentage: 1.0,  // Use 100% of available space for bars
                            categoryPercentage: 1.0  // Use 100% of category space
                        }},
                        y: {{
                            stacked: true,
                            beginAtZero: true,
                            scaleLabel: {{
                                display: true,
                                labelString: 'Package Count'
                            }}
                        }}
                    }},
                    onClick: function(event, elements) {{
                        if (elements.length > 0) {{
                            const element = elements[0];
                            let runData = null;

                            // Try different ways to access the data based on Chart.js version
                            if (element.element && element.element.$context && element.element.$context.raw && element.element.$context.raw.runData) {{
                                runData = element.element.$context.raw.runData;
                            }} else if (element._model && element._model.runData) {{
                                runData = element._model.runData;
                            }} else if (element.element && element.element.runData) {{
                                runData = element.element.runData;
                            }} else {{
                                // Fallback: get data from the dataset
                                const datasetIndex = element.datasetIndex;
                                const index = element.index;
                                const dataset = timelineChart.data.datasets[datasetIndex];
                                if (dataset && dataset.data[index] && dataset.data[index].runData) {{
                                    runData = dataset.data[index].runData;
                                }}
                            }}

                            if (runData && runData.runId) {{
                                const runId = runData.runId;
                                console.log('Clicked on run:', runId);

                                // Switch to the selected run
                                document.getElementById('run-select').value = runId;
                                currentRun = runId;
                                loadResults(runId);
                                updateTimelineSelection(runId);
                            }} else {{
                                console.warn('Could not find run data for clicked element:', element);
                            }}
                        }}
                    }}
                }}
            }});

            // Debug: Log chart configuration after creation
            console.log('Chart created with config:');
            console.log('- Bar thickness setting:', timelineChart.options.elements.bar.barThickness);
            console.log('- Max bar thickness:', timelineChart.options.elements.bar.maxBarThickness);
            console.log('- Scale type:', timelineChart.options.scales.x.type);
            console.log('- Number of data points:', chartData.length);
            console.log('- Time range (days):', (chartData[chartData.length-1].x - chartData[0].x) / (1000 * 60 * 60 * 24));
        }}

        // Load and parse the JSON data
        async function loadResults(runId = 'current') {{
            try {{
                document.getElementById('loading').style.display = 'block';
                document.getElementById('results-table').style.display = 'none';
                document.getElementById('error').style.display = 'none';

                // Use embedded availableRuns data instead of fetching JSON files
                // This ensures log_exists field is available
                let targetRun;
                if (runId === 'current') {{
                    targetRun = availableRuns[0];
                }} else {{
                    targetRun = availableRuns.find(r => r.run_id === runId);
                }}

                if (!targetRun) {{
                    throw new Error('Run ' + runId + ' not found');
                }}

                // Using embedded data ensures log_exists field is available

                allResults = targetRun.results;
                filteredResults = [...allResults];
                currentRun = targetRun.run_id;

                updateStats();
                populatePlatformFilter();
                populateRunnerFilter();
                sortResults();  // Apply default sort (by package) on load
                renderTable();
                updateRunInfo(runId);

                document.getElementById('loading').style.display = 'none';
                document.getElementById('results-table').style.display = 'table';
                document.getElementById('pagination').style.display = 'block';
            }} catch (error) {{
                console.error('Error loading results:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
            }}
        }}

        function updateRunInfo(runId) {{
            const runInfo = document.getElementById('run-info');
            if (runId === 'current') {{
                const timestamp = runInfo.getAttribute('data-timestamp');
                const timestampSpan = runInfo.querySelector('.timestamp-display');
                if (timestamp && timestampSpan) {{
                    timestampSpan.textContent = formatTimestamp(parseInt(timestamp));
                }}
            }} else {{
                const run = availableRuns.find(r => r.run_id === runId);
                if (run) {{
                    const timestampSpan = runInfo.querySelector('.timestamp-display');
                    if (timestampSpan) {{
                        timestampSpan.textContent = formatTimestamp(run.timestamp);
                    }}
                    runInfo.childNodes[0].textContent = 'SHA: ' + run.sha.substring(0, 8) + ' | Generated: ';
                }}
            }}
        }}

        function updateStats() {{
            const total = allResults.length;
            const success = allResults.filter(r => r.status === 'success').length;
            const failed = allResults.filter(r => r.status === 'build_fail').length;
            const timeout = allResults.filter(r => r.status === 'timeout').length;
            const oom = allResults.filter(r => r.status === 'oom_killed').length;
            const successRate = total > 0 ? (success / total * 100).toFixed(1) : 0;

            document.getElementById('total-packages').textContent = total;
            document.getElementById('success-count').textContent = success;
            document.getElementById('failed-count').textContent = failed;
            document.getElementById('timeout-count').textContent = timeout;
            document.getElementById('oom-count').textContent = oom;
            document.getElementById('success-rate').textContent = successRate + '%';
        }}

        // Helper function to determine platform from result data (with fallback for historical data)
        function getPlatformFromResult(result) {{
            if (result.platform && result.platform !== 'unknown') {{
                return result.platform;
            }}
            // Fallback: infer from runner_label or runner name
            const runner = (result.runner_label || result.runner || '').toLowerCase();
            if (runner.startsWith('jat')) return 'thor';
            if (runner.startsWith('jao')) return 'orin';
            if (runner === 'orin' || runner === 'thor') return runner;
            return 'unknown';
        }}

        function populatePlatformFilter() {{
            const platforms = [...new Set(allResults.map(r => getPlatformFromResult(r)))].filter(p => p && p !== 'unknown').sort();
            const select = document.getElementById('platform-filter');
            select.innerHTML = '<option value="">All Platforms</option>';

            platforms.forEach(platform => {{
                const option = document.createElement('option');
                option.value = platform;
                option.textContent = platform.toUpperCase();
                select.appendChild(option);
            }});
        }}

        function populateRunnerFilter() {{
            const runners = [...new Set(allResults.map(r => r.runner_label || r.runner))].sort();
            const select = document.getElementById('runner-filter');
            select.innerHTML = '<option value="">All Runners</option>';

            runners.forEach(runner => {{
                const option = document.createElement('option');
                option.value = runner;
                option.textContent = runner;
                select.appendChild(option);
            }});
        }}

        function setupEventListeners() {{
            document.getElementById('search').addEventListener('input', filterResults);
            document.getElementById('status-filter').addEventListener('change', filterResults);
            document.getElementById('platform-filter').addEventListener('change', filterResults);
            document.getElementById('runner-filter').addEventListener('change', filterResults);
            document.getElementById('sort-by').addEventListener('change', sortResults);
            document.getElementById('run-select').addEventListener('change', function() {{
                currentRun = this.value;
                loadResults(currentRun);
                updateTimelineSelection(currentRun);
            }});
            document.getElementById('compare-btn').addEventListener('click', toggleComparison);

            // Timeline marker click handlers
            document.querySelectorAll('.timeline-marker').forEach(marker => {{
                marker.addEventListener('click', function() {{
                    const runId = this.getAttribute('data-run');
                    if (runId) {{
                        document.getElementById('run-select').value = runId;
                        currentRun = runId;
                        loadResults(runId);
                        updateTimelineSelection(runId);
                    }}
                }});
            }});
        }}

        function updateTimelineSelection(runId) {{
            // Remove active class from all markers
            document.querySelectorAll('.timeline-marker').forEach(marker => {{
                marker.classList.remove('active');
                const dot = marker.querySelector('.marker-dot');
                if (dot) {{
                    dot.style.transform = '';
                }}
            }});

            // Add active class to selected marker
            document.querySelectorAll('.timeline-marker').forEach(marker => {{
                if (marker.getAttribute('data-run') === runId) {{
                    marker.classList.add('active');
                    const dot = marker.querySelector('.marker-dot');
                    if (dot) {{
                        dot.style.transform = 'scale(1.3)';
                        dot.style.zIndex = '15';
                    }}
                }}
            }});
        }}

        function filterResults() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const statusFilter = document.getElementById('status-filter').value;
            const platformFilter = document.getElementById('platform-filter').value;
            const runnerFilter = document.getElementById('runner-filter').value;

            filteredResults = allResults.filter(result => {{
                const matchesSearch = !searchTerm ||
                    result.package.toLowerCase().includes(searchTerm) ||
                    result.tag.toLowerCase().includes(searchTerm) ||
                    (result.failure_point && result.failure_point.toLowerCase().includes(searchTerm));

                const matchesStatus = !statusFilter || result.status === statusFilter;
                const matchesPlatform = !platformFilter || getPlatformFromResult(result) === platformFilter;
                const matchesRunner = !runnerFilter || (result.runner_label || result.runner) === runnerFilter;

                return matchesSearch && matchesStatus && matchesPlatform && matchesRunner;
            }});

            currentPage = 1;
            renderTable();
        }}

        function sortResults() {{
            const sortBy = document.getElementById('sort-by').value;

            filteredResults.sort((a, b) => {{
                switch (sortBy) {{
                    case 'package':
                        return a.package.localeCompare(b.package);
                    case 'platform':
                        const platformA = getPlatformFromResult(a);
                        const platformB = getPlatformFromResult(b);
                        return platformA.localeCompare(platformB);
                    case 'status':
                        return a.status.localeCompare(b.status);
                    case 'duration_s':
                        return b.duration_s - a.duration_s; // Descending
                    case 'timestamp':
                        return b.timestamp - a.timestamp; // Descending
                    default:
                        return 0;
                }}
            }});

            currentPage = 1;
            renderTable();
        }}

        function renderTable() {{
            const tbody = document.getElementById('results-tbody');
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            const pageResults = filteredResults.slice(start, end);

            tbody.innerHTML = pageResults.map((result, index) => {{
                // Generate log file path based on current run and log_relpath
                const githubUrl = result.run_url;
                let logUrl = githubUrl; // Fallback to GitHub Actions

                if (result.log_relpath && result.log_exists) {{
                    // Use actual run ID from the result data
                    const actualRunId = result.run_id || 'current';
                    // Create runner-specific filename using the actual runner label
                    const runnerLabel = result.runner_label || result.runner || 'unknown';
                    const baseFileName = result.log_relpath.replace('logs/', '').replace('.log', '');

                    // Sanitize runner label for filename (match Python: re.sub(r'[^a-zA-Z0-9]', '-', runner_label))
                    const runnerSuffix = '_' + runnerLabel.replace(/[^a-zA-Z0-9]/g, '-');

                    // Prefer HTML log files for better viewing experience
                    const uniqueFileNameHtml = baseFileName + runnerSuffix + '.html';
                    const uniqueFileNameLog = baseFileName + runnerSuffix + '.log';

                    // Try HTML first, fallback to .log
                    logUrl = 'logs/run-' + actualRunId + '/' + uniqueFileNameHtml;
                }}

                const platformDisplay = getPlatformFromResult(result);
                const platformClass = 'platform platform-' + platformDisplay.toLowerCase();

                return '<tr>' +
                    '<td><span class="package-name">' + result.package + '</span></td>' +
                    '<td><span class="tag">' + result.tag + '</span></td>' +
                    '<td><span class="' + platformClass + '">' + platformDisplay + '</span></td>' +
                    '<td><span class="runner">' + (result.runner_label || result.runner || 'unknown') + '</span></td>' +
                    '<td style="text-align: left;"><span class="status ' + result.status + '">' + result.status + '</span></td>' +
                    '<td><span class="duration">' + formatDuration(result.duration_s) + '</span></td>' +
                    '<td><span class="failure-point">' + result.failure_point + '</span></td>' +
                    '<td>' +
                        '<a href="' + githubUrl + '" target="_blank" title="View GitHub Actions Log">GitHub Actions</a>' +
                        (result.log_relpath && result.log_exists ? ' | <a href="' + logUrl + '" target="_blank" title="View Enhanced HTML Log with Colors and Formatting">Enhanced Log</a>' : '') +
                    '</td>' +
                '</tr>';
            }}).join('');

            updatePagination();
        }}

        function updatePagination() {{
            const totalPages = Math.ceil(filteredResults.length / itemsPerPage);
            const pageInfo = document.getElementById('page-info');
            const prevBtn = document.getElementById('prev-page');
            const nextBtn = document.getElementById('next-page');

            pageInfo.textContent = 'Page ' + currentPage + ' of ' + totalPages;
            prevBtn.disabled = currentPage === 1;
            nextBtn.disabled = currentPage === totalPages;
        }}

        function changePage(direction) {{
            const totalPages = Math.ceil(filteredResults.length / itemsPerPage);
            const newPage = currentPage + direction;

            if (newPage >= 1 && newPage <= totalPages) {{
                currentPage = newPage;
                renderTable();
            }}
        }}

        function toggleComparison() {{
            const comparison = document.getElementById('comparison');
            const btn = document.getElementById('compare-btn');

            if (comparison.classList.contains('active')) {{
                comparison.classList.remove('active');
                btn.textContent = 'Compare Runs';
                btn.style.background = '#28a745';
            }} else {{
                comparison.classList.add('active');
                btn.textContent = 'Hide Comparison';
                btn.style.background = '#dc3545';
                showComparison();
            }}
        }}

        function showComparison() {{
            // Future: Implement comparison between different runs
            const comparisonStats = document.getElementById('comparison-stats');
            comparisonStats.innerHTML =
                '<div class="comparison-stat">' +
                    '<h4>Current Run</h4>' +
                    '<div class="comparison-value">' + allResults.length + '</div>' +
                    '<div>Total Packages</div>' +
                '</div>' +
                '<div class="comparison-stat">' +
                    '<h4>Success Rate</h4>' +
                    '<div class="comparison-value">' + (allResults.filter(r => r.status === 'success').length / allResults.length * 100).toFixed(1) + '%</div>' +
                    '<div>Current Run</div>' +
                '</div>' +
                '<div class="comparison-stat">' +
                    '<h4>Average Duration</h4>' +
                    '<div class="comparison-value">' + formatDuration(allResults.reduce((sum, r) => sum + r.duration_s, 0) / allResults.length) + '</div>' +
                    '<div>Current Run</div>' +
                '</div>';
        }}

        // Initialize
        setupEventListeners();
        initializeTimestamps();

        // Initialize Chart.js timeline with delay to ensure scripts are loaded
        setTimeout(() => {{
            try {{
                initializeTimelineChart();
            }} catch (error) {{
                console.warn('Chart.js timeline failed to initialize, falling back to original timeline:', error);
                document.getElementById('fallback-timeline').style.display = 'block';
            }}
        }}, 100);

        // Load the pre-selected run (first option with 'selected' attribute)
        const selectedOption = document.querySelector('#run-select option[selected]');
        const initialRun = selectedOption ? selectedOption.value : document.getElementById('run-select').value;
        loadResults(initialRun);
    </script>
</body>
</html>
'''

    return html


def main():
    """Main function to generate dashboard HTML."""
    print("🎨 Generating interactive HTML dashboard...")

    # Load all runs from the runs directory (everything is treated as historical)
    available_runs = load_historical_runs()

    if not available_runs:
        print("❌ No runs found - cannot generate dashboard")
        return

    print(f"📊 Total runs available: {len(available_runs)}")

    # Generate HTML
    html = generate_dashboard_html(available_runs)

    # Write HTML file
    with open('./dashboard.html', 'w') as f:
        f.write(html)

    print(f"✅ Generated dynamic dashboard with {len(available_runs)} total runs")
    print(f"📁 Output: ./dashboard.html")


if __name__ == '__main__':
    main()
