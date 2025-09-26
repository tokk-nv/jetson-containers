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


def load_current_results() -> List[Dict[str, Any]]:
    """Load current build results."""
    try:
        with open('./results-data/results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No current results found at ./results-data/results.json")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing results.json: {e}")
        return []


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
                    'timeout': sum(1 for r in run_data if r['status'] == 'timeout'),
                    'oom': sum(1 for r in run_data if r['status'] == 'oom_killed')
                })
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    # Sort runs by timestamp (newest first)
    available_runs.sort(key=lambda x: x['timestamp'], reverse=True)

    print(f"✅ Found {len(available_runs)} available runs for timeline")
    if len(available_runs) == 0:
        print("❌ No historical runs available - timeline will only show current run")
        print("ℹ️  This is normal for the first few runs until we build up history")
    else:
        print(f"📊 Timeline will show: {[r['run_id'] for r in available_runs[:5]]}...")
    print(f"🎯 Total runs that will appear in dashboard: {len(available_runs) + 1}")  # +1 for current

    return available_runs


def generate_dashboard_html(current_results: List[Dict[str, Any]], available_runs: List[Dict[str, Any]]) -> str:
    """Generate the complete HTML dashboard."""

    # Get current run info
    current_run_id = current_results[0]['run_id'] if current_results else 'unknown'
    current_run_url = current_results[0]['run_url'] if current_results else '#'
    current_sha = current_results[0]['sha'] if current_results else 'unknown'
    current_timestamp = current_results[0]['timestamp'] if current_results else 0

    # Debug: Show log_relpath values from current results
    print(f"🔍 Debug: Current results log_relpath values:")
    for i, result in enumerate(current_results[:3]):
        log_path = result.get('log_relpath', 'N/A')
        runner = result.get('runner_label', result.get('runner', 'unknown'))
        print(f"  {i+1}. {result['package']} ({runner}): {log_path}")

    # Generate timeline items for available runs (mathematical axis approach)
    timeline_items = []

    # Calculate positions for timeline markers based on actual time differences
    if available_runs:
        # Use only historical run timestamps for range calculation
        all_timestamps = [run["timestamp"] for run in available_runs[:10]]

        oldest_timestamp = min(all_timestamps)
        newest_timestamp = max(all_timestamps)
        time_range = newest_timestamp - oldest_timestamp if newest_timestamp != oldest_timestamp else 86400  # Default to 1 day if same

        print(f"🕐 Timeline range: {time_range/86400:.1f} days ({oldest_timestamp} to {newest_timestamp})")

        for i, run in enumerate(available_runs[:10]):
            # Calculate position percentage based on actual time difference
            # Map to 10% - 90% range to leave more space before oldest and after latest
            if time_range > 0:
                time_ratio = (run["timestamp"] - oldest_timestamp) / time_range
                position_percent = 10 + (time_ratio * 80)  # 10% to 90% range
            else:
                # Fallback to equal spacing if timestamps are identical
                position_percent = 10 + (i * (80 / len(available_runs[:10])))

            print(f"   📍 Run {run['run_id']}: {time_ratio:.3f} ratio → {position_percent:.1f}% position")

            # Determine build health status
            success_rate = (run["success"] / run["total"]) * 100 if run["total"] > 0 else 0
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
                health_color = "#fd7e14"  # Orange
                health_label = "Partial Failure"
            else:
                health_status = "poor"
                health_color = "#dc3545"  # Red
                health_label = "Major Issues"

            # Check if this is the most recent run (first in the sorted list)
            is_latest = (i == 0)
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
                                {f'<span class="timeout-count">{run["timeout"]} ⏱️</span>' if run["timeout"] > 0 else ''}
                                {f'<span class="oom-count">{run["oom"]} 💥</span>' if run["oom"] > 0 else ''}
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
            background: #fd7e14;
            box-shadow: 0 0 0 3px rgba(253, 126, 20, 0.3);
        }}

        .marker-dot.poor {{
            background: #dc3545;
            box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.3);
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
        .stat-value.partial {{ color: #fd7e14; }}
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
        .oom-count {{ color: #fd7e14; }}

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
            <div class="timeline-axis-container">
                <div class="timeline-axis">
                    <div class="axis-line"></div>
                    <div class="axis-labels">
                        <span class="axis-label-left">Oldest</span>
                        <span class="axis-label-right">Latest</span>
                    </div>
                    <!-- Current run marker removed - latest historical run is highlighted instead -->
                    {timeline_html}
                </div>
            </div>
            <div style="color: #6c757d; font-size: 12px; margin-top: 15px;">
                💡 Hover over markers to see details • Click to view results • Timeline shows last 10 runs
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
            <select id="runner-filter" class="filter-select">
                <option value="">All Runners</option>
            </select>
            <select id="sort-by" class="filter-select">
                <option value="package">Sort by Package</option>
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
                        <th>Runner</th>
                        <th>Status</th>
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
            <p>Run ID: <a href="{current_run_url}" target="_blank">{current_run_id}</a> | SHA: {current_sha[:8]}</p>
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
                const timestamp = parseInt(element.getAttribute('data-timestamp'));
                element.textContent = formatTimelineDate(timestamp);
            }});

            // Update all timestamp displays
            document.querySelectorAll('.timestamp-display[data-timestamp]').forEach(element => {{
                const timestamp = parseInt(element.getAttribute('data-timestamp'));
                element.textContent = formatTimestamp(timestamp);
            }});

            // Update run selector options with local times
            document.querySelectorAll('#run-select option[data-timestamp]').forEach(option => {{
                const timestamp = parseInt(option.getAttribute('data-timestamp'));
                const runId = option.value;
                option.textContent = `Run ${{runId}}${{formatRunOptionDate(timestamp)}}`;
            }});

            // Update current run info
            updateRunInfo(currentRun);
        }}

        // Available runs data
        const availableRuns = {json.dumps(available_runs, separators=(',', ':'))};

        // Load and parse the JSON data
        async function loadResults(runId = 'current') {{
            try {{
                document.getElementById('loading').style.display = 'block';
                document.getElementById('results-table').style.display = 'none';
                document.getElementById('error').style.display = 'none';

                let response;
                if (runId === 'current') {{
                    response = await fetch('results.json');
                }} else {{
                    response = await fetch('runs/results-' + runId + '.json');
                }}

                if (!response.ok) {{
                    throw new Error('Failed to load results for run ' + runId);
                }}

                allResults = await response.json();
                filteredResults = [...allResults];
                currentRun = runId;

                updateStats();
                populateRunnerFilter();
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
            const runnerFilter = document.getElementById('runner-filter').value;

            filteredResults = allResults.filter(result => {{
                const matchesSearch = !searchTerm ||
                    result.package.toLowerCase().includes(searchTerm) ||
                    result.tag.toLowerCase().includes(searchTerm) ||
                    (result.failure_point && result.failure_point.toLowerCase().includes(searchTerm));

                const matchesStatus = !statusFilter || result.status === statusFilter;
                const matchesRunner = !runnerFilter || (result.runner_label || result.runner) === runnerFilter;

                return matchesSearch && matchesStatus && matchesRunner;
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

            tbody.innerHTML = pageResults.map(result => {{
                // Generate log file path based on current run and log_relpath
                const githubUrl = result.run_url;
                let logUrl = githubUrl; // Fallback to GitHub Actions

                if (result.log_relpath) {{
                    // Use actual run ID from the result data
                    const actualRunId = result.run_id || 'current';
                    // Create runner-specific filename
                    const runnerLabel = result.runner_label || result.runner || 'unknown';
                    const baseFileName = result.log_relpath.replace('logs/', '').replace('.log', '');
                    let runnerSuffix = '';

                    if (runnerLabel.toLowerCase().includes('orin')) {{
                        runnerSuffix = '_orin';
                    }} else if (runnerLabel.toLowerCase().includes('thor')) {{
                        runnerSuffix = '_thor';
                    }} else {{
                        runnerSuffix = '_' + runnerLabel.toLowerCase();
                    }}

                    // Prefer HTML log files for better viewing experience
                    const uniqueFileNameHtml = baseFileName + runnerSuffix + '.html';
                    const uniqueFileNameLog = baseFileName + runnerSuffix + '.log';

                    // Try HTML first, fallback to .log
                    logUrl = 'logs/run-' + actualRunId + '/' + uniqueFileNameHtml;
                    // Note: We assume HTML files exist since we generate them in the workflow
                    // If needed, we could add a check here, but for now we'll default to HTML
                }}

                return '<tr>' +
                    '<td><span class="package-name">' + result.package + '</span></td>' +
                    '<td><span class="tag">' + result.tag + '</span></td>' +
                    '<td><span class="runner">' + (result.runner_label || result.runner || 'unknown') + '</span></td>' +
                    '<td><span class="status ' + result.status + '">' + result.status + '</span></td>' +
                    '<td><span class="duration">' + formatDuration(result.duration_s) + '</span></td>' +
                    '<td><span class="failure-point">' + result.failure_point + '</span></td>' +
                    '<td>' +
                        '<a href="' + githubUrl + '" target="_blank" title="View GitHub Actions Log">GitHub Actions</a>' +
                        (result.log_relpath ? ' | <a href="' + logUrl + '" target="_blank" title="View Enhanced HTML Log with Colors and Formatting">Enhanced Log</a>' : '') +
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

    # Load data
    current_results = load_current_results()
    print(f"🔍 DEBUG: Loaded {len(current_results)} current results")
    if not current_results:
        print("⚠️ No current results available - generating dashboard with empty results")
        print("ℹ️ This may indicate all build jobs were cancelled due to timeouts")
        # Continue with empty results instead of exiting

    available_runs = load_historical_runs()

    # Generate HTML
    html = generate_dashboard_html(current_results, available_runs)

    # Write HTML file
    with open('./dashboard.html', 'w') as f:
        f.write(html)

    print(f"✅ Generated dynamic dashboard with {len(current_results)} results")
    print(f"📊 Dashboard includes {len(available_runs)} historical runs")
    print(f"📁 Output: ./dashboard.html")


if __name__ == '__main__':
    main()
