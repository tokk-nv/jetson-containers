import requests
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import statistics

# CLI ARGUMENTS
parser = argparse.ArgumentParser(description="High-concurrency stress test for a PyPI JSON endpoint")
parser.add_argument('--package', type=str, default='transformers', help='PyPI package name')
parser.add_argument('--requests', type=int, default=1000, help='Total number of requests')
parser.add_argument('--concurrency', type=int, default=250, help='Number of concurrent threads')
parser.add_argument('--timeout', type=float, default=10, help='Request timeout (in seconds)')
parser.add_argument('--retries', type=int, default=10, help='Number of retries per request')
parser.add_argument('--url', type=str, help='Custom full PyPI JSON URL to test (overrides package name)')
args = parser.parse_args()

# CONFIGURATION
PACKAGE = args.package
PYPI_JSON_URL = args.url or f"https://pypi.org/pypi/{PACKAGE}/json"
NUM_REQUESTS = args.requests
MAX_CONCURRENCY = args.concurrency
REQUEST_TIMEOUT = args.timeout
RETRIES = args.retries

# Stats
stats = {
    "success": 0,
    "fail": 0,
    "errors": 0,
    "latencies": []
}

def fetch_once(index):
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRIES,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        start = time.time()
        response = session.get(PYPI_JSON_URL, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start

        if response.status_code == 200:
            return ("success", elapsed)
        else:
            return ("fail", elapsed)

    except Exception as e:
        return ("error", str(e))

# RUN
print(f"🚀 High-Concurrency Stress Test: {NUM_REQUESTS} requests @ {MAX_CONCURRENCY} threads")
start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
    futures = {executor.submit(fetch_once, i): i for i in range(NUM_REQUESTS)}
    for future in as_completed(futures):
        result, info = future.result()
        if result == "success":
            stats["success"] += 1
            stats["latencies"].append(info)
        elif result == "fail":
            stats["fail"] += 1
            stats["latencies"].append(info)
        else:
            stats["errors"] += 1
            print(f"[{futures[future]+1:04d}] ERROR: {info}")

duration = time.time() - start_time

# SUMMARY
print("\n📊 Test Summary")
print(f"  ✅ Success: {stats['success']}")
print(f"  ❌ Failures: {stats['fail']}")
print(f"  💥 Exceptions: {stats['errors']}")
print(f"  ⏱️ Duration: {duration:.2f}s")

if stats["latencies"]:
    print(f"  ⏱️ Avg latency: {statistics.mean(stats['latencies']):.3f}s")
    print(f"  ⏱️ 95th percentile: {statistics.quantiles(stats['latencies'], n=100)[94]:.3f}s")
    print(f"  🚨 Max latency: {max(stats['latencies']):.3f}s")
