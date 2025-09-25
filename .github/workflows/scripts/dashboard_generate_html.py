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

    # Generate timeline items for available runs
    timeline_items = []
    for run in available_runs[:10]:
        timeline_item = f'''
            <div class="timeline-item" data-run="{run["run_id"]}">
                <div class="timeline-date">{datetime.fromtimestamp(run["timestamp"]).strftime("%Y-%m-%d %H:%M")} UTC</div>
                <div class="timeline-stats">Run {run["run_id"]} | {run["total"]} packages | {run["success"]}✅ {run["failed"]}❌</div>
            </div>'''
        timeline_items.append(timeline_item)

    timeline_html = ''.join(timeline_items)

    # Generate run options for select dropdown
    run_options = []
    for run in available_runs:
        option = f'<option value="{run["run_id"]}">Run {run["run_id"]} - {datetime.fromtimestamp(run["timestamp"]).strftime("%Y-%m-%d %H:%M")} UTC</option>'
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
            opacity: 0.8;
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
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            max-height: 120px;
            overflow-y: auto;
        }}

        .timeline-item {{
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 12px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
        }}

        .timeline-item:hover {{
            background: #e9ecef;
            border-color: #007bff;
        }}

        .timeline-item.active {{
            background: #007bff;
            color: white;
            border-color: #007bff;
        }}

        .timeline-date {{
            font-weight: bold;
            color: #495057;
        }}

        .timeline-stats {{
            color: #6c757d;
            font-size: 11px;
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
            max-height: 70vh;
            overflow-y: auto;
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
                <option value="current">Current Run ({current_run_id})</option>
                {run_options_html}
            </select>
            <div class="run-info" id="run-info">
                SHA: {current_sha[:8]} | Generated: {datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC') if current_timestamp else 'Unknown'}
            </div>
        </div>

        <div class="timeline" id="timeline">
            <div style="font-weight: bold; margin-bottom: 10px; color: #495057;">Recent Runs Timeline:</div>
            <div class="timeline-item active" data-run="current">
                <div class="timeline-date">Current Run</div>
                <div class="timeline-stats">Run ID: {current_run_id} | {len(current_results)} packages</div>
            </div>
            {timeline_html}
            <div style="color: #6c757d; font-size: 12px; margin-top: 10px;">
                💡 Click on any run to view its results and logs • Showing last 10 runs
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
            <p>Generated on {datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC') if current_timestamp else 'Unknown'}</p>
            <p>Run ID: <a href="{current_run_url}" target="_blank">{current_run_id}</a> | SHA: {current_sha[:8]}</p>
        </div>
    </div>

    <script>
        let allResults = [];
        let filteredResults = [];
        let currentPage = 1;
        let currentRun = 'current';
        const itemsPerPage = 50;

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
                runInfo.textContent = `SHA: {current_sha[:8]} | Generated: {datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC') if current_timestamp else 'Unknown'}`;
            }} else {{
                const run = availableRuns.find(r => r.run_id === runId);
                if (run) {{
                    const date = new Date(run.timestamp * 1000).toISOString().replace('T', ' ').replace('.000Z', ' UTC');
                    runInfo.textContent = 'SHA: ' + run.sha.substring(0, 8) + ' | Generated: ' + date;
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

            // Timeline click handlers
            document.querySelectorAll('.timeline-item').forEach(item => {{
                item.addEventListener('click', function() {{
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
            document.querySelectorAll('.timeline-item').forEach(item => {{
                item.classList.remove('active');
                if (item.getAttribute('data-run') === runId) {{
                    item.classList.add('active');
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
                    '<td><span class="duration">' + result.duration_s + 's</span></td>' +
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
                    '<div class="comparison-value">' + (allResults.reduce((sum, r) => sum + r.duration_s, 0) / allResults.length).toFixed(1) + 's</div>' +
                    '<div>Current Run</div>' +
                '</div>';
        }}

        // Initialize
        setupEventListeners();
        loadResults();
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
    if not current_results:
        print("❌ No current results available - cannot generate dashboard")
        sys.exit(1)

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
