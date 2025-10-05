#!/usr/bin/env python3
"""
Local Dashboard Testing Script for nvidia-ai-iot/jetson-containers

This script allows you to test the dashboard locally by:
1. Fetching real GitHub Actions data from nvidia-ai-iot/jetson-containers using your PAT
2. Using our local dashboard scripts to process the data
3. Generating the HTML dashboard locally with real data
4. Testing the new timeline redesign with actual build history

Usage:
    python3 test_dashboard_local.py --token YOUR_GITHUB_PAT [--output-dir DIR]

The script will:
- Pull real data from nvidia-ai-iot/jetson-containers
- Use our local dashboard_*.py scripts
- Generate a local test directory with the dashboard
- Allow you to preview the new timeline design with real data
"""

import os
import sys
import json
import argparse
import tempfile
import shutil
import socket
import threading
import webbrowser
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add the scripts directory to Python path (go up from tests to scripts)
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

def setup_test_environment(output_dir: str, github_token: str, repo: str = "nvidia-ai-iot/jetson-containers"):
    """Set up local test environment with real data from nvidia-ai-iot/jetson-containers."""

    print(f"🚀 Setting up local dashboard test environment...")
    print(f"📁 Output directory: {output_dir}")
    print(f"🔗 Source repository: {repo}")
    print(f"🔧 Using local dashboard scripts from current directory")

    # Create output directory structure
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories matching expected structure
    (output_path / 'runs').mkdir(exist_ok=True)
    (output_path / 'logs').mkdir(exist_ok=True)

    # Set environment variables for the scripts to pull from nvidia-ai-iot/jetson-containers
    os.environ['GITHUB_TOKEN'] = github_token
    os.environ['GITHUB_REPOSITORY'] = repo

    print(f"✅ Environment configured to pull data from {repo}")

    return output_path

def run_dashboard_scripts(output_path: Path):
    """Run the dashboard generation scripts with real nvidia-ai-iot/jetson-containers data."""

    print("📊 Running dashboard scripts with real data from nvidia-ai-iot/jetson-containers...")

    # Change to output directory
    original_cwd = os.getcwd()
    os.chdir(output_path)

    try:
        # Import and run the dashboard scripts
        print("1️⃣ Creating minimal current data for testing...")
        try:
            create_minimal_current_data(Path('.'))
            print("✅ Minimal current data created")
        except Exception as e:
            print(f"❌ Failed to create current data: {e}")
            raise

        print("2️⃣ Downloading historical runs from nvidia-ai-iot/jetson-containers...")
        try:
            # Clean up any dummy data that might have been created
            runs_dir = Path('./runs')
            if runs_dir.exists():
                dummy_files = list(runs_dir.glob('results-current.json'))
                if dummy_files:
                    print(f"🧹 Cleaning up {len(dummy_files)} dummy run files before downloading real data...")
                    for dummy_file in dummy_files:
                        dummy_file.unlink()
                    print("✅ Dummy data cleaned up")

            # Add timeout to prevent hanging
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Historical runs download timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(300)  # 5 minute timeout for historical download

            from dashboard_download_historical_runs import main as download_historical
            download_historical()
            signal.alarm(0)  # Cancel timeout
            print("✅ Historical runs downloaded from nvidia-ai-iot/jetson-containers")
        except TimeoutError:
            print("⚠️ Historical runs download timed out after 5 minutes - using test data")
            print("   This might be due to API rate limits or network issues")
            # Only create dummy data if we don't already have real data
            runs_dir = Path('./runs')
            if not runs_dir.exists() or len(list(runs_dir.glob('results-*.json'))) == 0:
                print("   Creating minimal test data for historical runs...")
                create_minimal_test_data(Path('.'))
            else:
                print("   Real historical data already available, skipping dummy data creation")
        except Exception as e:
            print(f"❌ Historical runs download failed: {e}")
            print("   Using test data for historical runs...")
            # Only create dummy data if we don't already have real data
            runs_dir = Path('./runs')
            if not runs_dir.exists() or len(list(runs_dir.glob('results-*.json'))) == 0:
                print("   Creating minimal test data for historical runs...")
                create_minimal_test_data(Path('.'))
            else:
                print("   Real historical data already available, skipping dummy data creation")

        print("3️⃣ Processing log files...")
        try:
            from dashboard_process_log_files import main as process_logs
            # Add timeout to prevent hanging
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Log processing timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 60 second timeout

            process_logs()
            signal.alarm(0)  # Cancel timeout
            print("✅ Log files processed")
        except TimeoutError:
            print("⚠️ Log processing timed out after 60 seconds - skipping")
            print("   Dashboard will still work, but logs might not be organized optimally")
        except Exception as e:
            print(f"⚠️ Log processing failed: {e}")
            print("   Dashboard will still work, but logs might not be organized optimally")

        print("4️⃣ Converting logs to HTML (with our enhanced converter)...")
        try:
            from log_to_html_converter import convert_logs_in_directory
            convert_logs_in_directory('./logs/')
            print("✅ Logs converted to HTML with ANSI colors and box drawing")
        except Exception as e:
            print(f"⚠️ Log conversion failed: {e}")
            print("   Raw logs will still be available")

        print("5️⃣ Generating HTML dashboard (with new timeline design)...")
        try:
            # Add timeout to prevent hanging
            import signal
            def dashboard_timeout_handler(signum, frame):
                raise TimeoutError("Dashboard generation timed out")

            signal.signal(signal.SIGALRM, dashboard_timeout_handler)
            signal.alarm(60)  # 1 minute timeout for dashboard generation

            from dashboard_generate_html import main as generate_html
            generate_html()
            signal.alarm(0)  # Cancel timeout
            print("✅ HTML dashboard generated with mathematical timeline!")
        except TimeoutError:
            print("⚠️ Dashboard generation timed out after 1 minute")
            print("   This might be due to processing too many runs or performance issues")
            # Check if dashboard was partially created
            if Path('./dashboard.html').exists():
                print("   Dashboard file exists - generation may have completed despite timeout")
            else:
                print("   Dashboard generation failed - no output file found")
                raise
        except Exception as e:
            print(f"❌ HTML generation failed: {e}")
            print("   This is the main output - check the error above")
            raise

        print("6️⃣ Generating markdown report...")
        try:
            from dashboard_generate_report import main as generate_report
            generate_report()
            print("✅ Markdown report generated")
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")
            print("   Dashboard HTML is still available")

    finally:
        os.chdir(original_cwd)


def find_free_port():
    """Find a free port starting from 8000."""
    for port in range(8000, 8100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def get_local_ip():
    """Get the local LAN IP address of this machine."""
    try:
        import socket
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to Google's DNS server (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except:
        # Fallback: try to get IP from hostname
        try:
            import subprocess
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                # Get the first IP address
                ips = result.stdout.strip().split()
                return ips[0] if ips else 'localhost'
        except:
            pass
        return 'localhost'

def cleanup_existing_servers():
    """Kill any existing web servers on common ports."""
    try:
        import subprocess
        # Kill any existing http.server processes
        subprocess.run(['pkill', '-f', 'http.server'], capture_output=True)
        # Also try to kill processes on common ports
        for port in range(8000, 8100):
            try:
                subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, check=True)
                subprocess.run(['kill', '-9', f'$(lsof -ti :{port})'], shell=True, capture_output=True)
            except:
                pass
    except Exception as e:
        print(f"⚠️ Could not cleanup existing servers: {e}")

def start_web_server(output_path: Path, port: int):
    """Start a web server to serve the dashboard."""

    # Cleanup any existing servers first
    cleanup_existing_servers()

    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(output_path), **kwargs)

        def end_headers(self):
            # Add CORS headers to allow local development
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()

    try:
        server = HTTPServer(('', port), CustomHandler)
        print(f"🌐 Starting web server on port {port}...")

        # Start server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        return server, server_thread
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        return None, None

def create_minimal_current_data(output_path):
    """Create minimal current results data as a historical run."""

    print("🎭 Creating minimal current results data...")

    import time
    current_time = int(time.time())

    # Ensure directories exist
    (output_path / 'runs').mkdir(exist_ok=True)
    (output_path / 'logs').mkdir(exist_ok=True)

    # Create current results as a historical run
    current_run_id = "current"
    current_results = [{
        "package": "timeline-test",
        "tag": "test-timeline-design",
        "status": "success",
        "duration_s": 180.0,
        "timestamp": current_time,
        "run_id": current_run_id,
        "run_url": "https://github.com/nvidia-ai-iot/jetson-containers/actions/runs/current",
        "sha": "timeline1",
        "runner": "test-runner",
        "runner_label": "test",
        "log_relpath": "logs/timeline_test.log",
        "failure_point": None
    }]

    # Save current results as a historical run file
    results_file = output_path / 'runs' / f'results-{current_run_id}.json'
    with open(results_file, 'w') as f:
        json.dump(current_results, f, indent=2)

    # Create a sample log file
    logs_dir = output_path / 'logs'
    sample_log = logs_dir / 'timeline_test.log'
    with open(sample_log, 'w') as f:
        f.write("""[16:00:00] 🧪 Timeline Test Build Started
[16:00:01] ✅ This is a test build for timeline design verification
[16:00:02] 🎨 Testing mathematical timeline with positioned markers

┌─────────────────────────────────────────────────┐
│ TIMELINE DESIGN TEST                            │
│ This build demonstrates the new timeline UI     │
│ with color-coded markers and hover popups       │
└─────────────────────────────────────────────────┘

[16:00:03] ✅ Timeline test completed successfully!
""")

    print(f"✅ Created minimal current data:")
    print(f"   • 1 current result")
    print(f"   • Sample log file")
    print(f"   • Ready for real historical data download!")

def create_minimal_test_data(output_path):
    """Create minimal test data to demonstrate the timeline design."""

    print("🎭 Creating minimal test data for timeline demonstration...")

    import time
    current_time = int(time.time())

    # Ensure directories exist
    (output_path / 'results-data').mkdir(exist_ok=True)
    (output_path / 'runs').mkdir(exist_ok=True)
    (output_path / 'logs').mkdir(exist_ok=True)

    # Create current results
    current_results = [{
        "package": "timeline-test",
        "tag": "test-timeline-design",
        "status": "success",
        "duration_s": 180.0,
        "timestamp": current_time,
        "run_id": "current",
        "run_url": "https://github.com/nvidia-ai-iot/jetson-containers/actions/runs/current",
        "sha": "timeline1",
        "runner": "test-runner",
        "runner_label": "test",
        "log_relpath": "logs/timeline_test.log",
        "failure_point": None
    }]

    # Save current results
    results_file = output_path / 'results-data' / 'results.json'
    with open(results_file, 'w') as f:
        json.dump(current_results, f, indent=2)

    # Create historical runs for timeline testing with 10 runs at varied intervals
    historical_runs = []
    time_intervals = [1, 2, 4, 8, 15, 25, 40, 60, 90, 150]  # 10 runs with varied spacing

    for i, days_ago in enumerate(time_intervals):
        timestamp = current_time - (86400 * days_ago)  # Days ago

        # Vary success rates for visual testing across all 10 runs
        success_patterns = [
            (48, 50),   # i=0: Good (96%)
            (50, 50),   # i=1: Perfect (100%)
            (35, 48),   # i=2: Partial (73%)
            (20, 45),   # i=3: Poor (44%)
            (42, 47),   # i=4: Good (89%)
            (25, 52),   # i=5: Poor (48%)
            (46, 49),   # i=6: Good (94%)
            (30, 51),   # i=7: Partial (59%)
            (44, 46),   # i=8: Good (96%)
            (15, 48),   # i=9: Poor (31%)
        ]
        success, total = success_patterns[i]

        failed = total - success

        # Create dummy results for this historical run
        run_results = []
        for j in range(total):
            status = "success" if j < success else "build_fail"
            run_results.append({
                "package": f"package-{j:03d}",
                "status": status,
                "timestamp": timestamp,
                "run_id": f"1000000{i:03d}",
                "sha": f"hist{i:03d}abc"
            })

        # Save historical run
        runs_dir = output_path / 'runs'
        run_file = runs_dir / f'results-1000000{i:03d}.json'
        with open(run_file, 'w') as f:
            json.dump(run_results, f, indent=2)

        historical_runs.append({
            "run_id": f"1000000{i:03d}",
            "timestamp": timestamp,
            "total": total,
            "success": success,
            "failed": failed
        })

    # Create a sample log file
    logs_dir = output_path / 'logs'
    sample_log = logs_dir / 'timeline_test.log'
    with open(sample_log, 'w') as f:
        f.write("""[16:00:00] 🧪 Timeline Test Build Started
[16:00:01] ✅ This is a test build for timeline design verification
[16:00:02] 🎨 Testing mathematical timeline with positioned markers

┌─────────────────────────────────────────────────┐
│ TIMELINE DESIGN TEST                            │
│ This build demonstrates the new timeline UI     │
│ with color-coded markers and hover popups       │
└─────────────────────────────────────────────────┘

[16:00:03] ✅ Timeline test completed successfully!
""")

    print(f"✅ Created minimal test data:")
    print(f"   • 1 current result")
    print(f"   • {len(historical_runs)} historical runs")
    print(f"   • Sample log file")
    print(f"   • Ready for timeline testing!")

def main():
    parser = argparse.ArgumentParser(
        description='Test dashboard locally with real data from nvidia-ai-iot/jetson-containers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with your GitHub PAT:
  python3 test_dashboard_local.py --token ghp_your_token_here

  # Custom output directory:
  python3 test_dashboard_local.py --token ghp_your_token_here --output-dir ./my-test

This will:
1. Pull real build data from nvidia-ai-iot/jetson-containers
2. Use our local dashboard scripts (with the new timeline design)
3. Generate a complete dashboard locally for testing
4. Show you the mathematical timeline with real build history!
        """
    )
    parser.add_argument('--token', required=True, help='GitHub Personal Access Token (with repo read access)')
    parser.add_argument('--output-dir', default='./dashboard-test', help='Output directory for test files (default: ./dashboard-test)')

    args = parser.parse_args()

    # Add overall timeout to prevent hanging
    import signal
    def overall_timeout_handler(signum, frame):
        print("\n⚠️ Overall test timeout reached (10 minutes) - stopping test")
        print("   This might be due to API rate limits or network issues")
        print("   Try running with a different token or check your network connection")
        exit(1)

    signal.signal(signal.SIGALRM, overall_timeout_handler)
    signal.alarm(600)  # 10 minute overall timeout

    try:
        print("🚀 JETSON CONTAINERS DASHBOARD LOCAL TESTING")
        print("=" * 50)

        # Setup test environment
        output_path = setup_test_environment(args.output_dir, args.token)

        # Run full dashboard pipeline with real data from nvidia-ai-iot/jetson-containers
        run_dashboard_scripts(output_path)

        # Show results
        dashboard_file = output_path / 'dashboard.html'
        if dashboard_file.exists():
            print("\n" + "=" * 50)
            print("🎉 DASHBOARD GENERATED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📁 Test directory: {output_path.absolute()}")

            # Find a free port and start web server
            port = find_free_port()
            if port is None:
                print("❌ No free ports available (8000-8099)")
                return 1

            server, server_thread = start_web_server(output_path, port)
            if server is None:
                print("❌ Failed to start web server")
                return 1

            # Get local LAN IP
            local_ip = get_local_ip()

            # Create URLs
            local_url = f"http://localhost:{port}/dashboard.html"
            lan_url = f"http://{local_ip}:{port}/dashboard.html"

            print(f"\n🌐 DASHBOARD IS NOW LIVE!")
            print(f"   📱 Local access:  {local_url}")
            print(f"   🏠 LAN access:    {lan_url}")
            print(f"   🔧 Server running on port {port}")

            print(f"\n🎯 Key features to test:")
            print(f"   • Mathematical timeline with positioned markers")
            print(f"   • Color-coded build health indicators")
            print(f"   • Hover popups with detailed stats")
            print(f"   • Enhanced HTML logs with ANSI colors")
            print(f"   • Real data from nvidia-ai-iot/jetson-containers")

            print(f"\n📋 Generated files:")
            key_files = ['dashboard.html', 'build-report.md', 'results-data/results.json']
            for key_file in key_files:
                file_path = output_path / key_file
                if file_path.exists():
                    size = file_path.stat().st_size
                    print(f"   ✅ {key_file} ({size:,} bytes)")
                else:
                    print(f"   ❌ {key_file} (missing)")

            # Count log files
            logs_dir = output_path / 'logs'
            if logs_dir.exists():
                log_files = list(logs_dir.rglob('*.log'))
                html_files = list(logs_dir.rglob('*.html'))
                print(f"   📝 {len(log_files)} log files, {len(html_files)} HTML conversions")

            print(f"\n⏹️  Press Ctrl+C to stop the server and exit")

            try:
                # Keep the server running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n⏹️  Stopping web server...")
                server.shutdown()
                print(f"✅ Server stopped. Dashboard files remain in: {output_path.absolute()}")

        else:
            print("❌ Dashboard generation failed - dashboard.html not found")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        signal.alarm(0)  # Cancel timeout
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        signal.alarm(0)  # Cancel timeout
        import traceback
        traceback.print_exc()
        return 1
    finally:
        signal.alarm(0)  # Ensure timeout is cancelled

    return 0

if __name__ == '__main__':
    main()
