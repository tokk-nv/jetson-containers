# Dashboard Local Testing Guide

This guide helps you test the dashboard UI improvements locally using real data from `nvidia-ai-iot/jetson-containers`.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- GitHub Personal Access Token (PAT) with repo read access
- Internet connection to fetch data from GitHub

### Usage

```bash
# Test with your GitHub PAT (from project root)
python3 .github/workflows/scripts/tests/test_dashboard_local.py --token ghp_your_token_here

# Custom output directory
python3 .github/workflows/scripts/tests/test_dashboard_local.py --token ghp_your_token_here --output-dir ./my-test
```

## 🎯 What This Tests

### New Timeline Design
- **Mathematical timeline**: Real X-axis with positioned markers based on actual timestamps
- **Color-coded health indicators**:
  - 🟢 Green (Perfect): 100% success rate
  - 🟡 Yellow (Good): 80-99% success rate
  - 🟠 Orange (Partial): 50-79% success rate
  - 🔴 Red (Poor): <50% success rate
- **Interactive markers**: Hover for detailed stats, click to view results
- **Current run pulse**: Animated current run indicator

### Enhanced Features
- **Real data**: Pulls from `nvidia-ai-iot/jetson-containers` GitHub Actions
- **HTML log conversion**: ANSI colors and box drawing characters preserved
- **Local testing**: Complete dashboard generated locally for development

## 📁 Generated Structure

```
dashboard-test/
├── dashboard.html          # Main dashboard (open this in browser!)
├── dashboard-generation.log # Full generation log for debugging
├── build-report.md         # Markdown summary report
├── runs/
│   ├── results-*.json      # All run data (unified approach)
│   └── ...
└── logs/
    ├── run-*/             # Organized by run ID
    │   ├── *.log          # Raw log files
    │   └── *.html         # Enhanced HTML logs with ANSI colors
    └── ...
```

## 🔧 How It Works

1. **Environment Setup**: Creates test directory structure
2. **Data Fetching**: Uses your PAT to pull from `nvidia-ai-iot/jetson-containers`
3. **Script Execution**: Runs our local dashboard scripts:
   - `dashboard_download_historical_runs.py` (with pagination & chunk merging)
   - `dashboard_process_log_files.py` (with pagination support)
   - `log_to_html_converter.py` (ANSI color conversion)
   - `dashboard_generate_html.py` (Chart.js timeline + auto-sort)
   - `dashboard_generate_report.py` (unified data loading)
4. **Output Generation**: Creates complete dashboard with Chart.js timeline
5. **Comprehensive Logging**: All output saved to `dashboard-generation.log`

## 🎨 Testing Timeline Features

### Visual Elements to Check:
- [ ] Timeline axis line (gradient from gray to blue)
- [ ] Positioned markers based on actual timestamps
- [ ] Color-coded dots reflecting build success rates
- [ ] Hover popups with detailed statistics
- [ ] Current run marker with pulsing animation
- [ ] Smooth hover animations and scaling effects

### Interactive Elements:
- [ ] Click markers to switch between runs
- [ ] Hover for popup details without clicking
- [ ] Timeline integrates with run selector dropdown
- [ ] Active marker highlighting when selected

## 🐛 Troubleshooting

### Common Issues:

**"Current artifacts download failed"**
- Check your GitHub token has repo read access
- Verify `nvidia-ai-iot/jetson-containers` has recent workflow runs
- Check network connectivity

**"Import could not be resolved" warnings**
- These are normal linter warnings
- The script uses dynamic imports that work at runtime

**Empty timeline**
- Historical runs might not be available
- Dashboard will still work with current run only
- Check if `runs/` directory has `results-*.json` files

## 🐛 Debugging with Generation Logs

The test script now saves **all output** to `dashboard-generation.log` for debugging:

```bash
# View the full log
cat ./dashboard-test/dashboard-generation.log

# Search for specific run
grep "18254053839" ./dashboard-test/dashboard-generation.log

# Check pagination details
grep "📄 Page" ./dashboard-test/dashboard-generation.log

# See chunk merging progress
grep "chunk" ./dashboard-test/dashboard-generation.log
```

**What's in the log:**
- Artifact pagination (pages fetched, counts)
- Chunk artifact merging details
- Package counts per run
- API response status codes
- Error messages and warnings

## 🎯 What to Look For

When testing the dashboard:

1. **Timeline Positioning**: Markers positioned chronologically with proper spacing
2. **Run Selection**: All runs appear in dropdown (check pagination worked)
3. **Package Count**: Verify runs show correct package counts (e.g., run 18254053839 should have 481 packages)
4. **Alphabetical Sorting**: Packages automatically sorted A-Z on load
5. **Colors**: Health status colors reflect actual success rates
6. **Interactivity**: Smooth hover effects and clickable timeline markers
7. **Chunk Merging**: Incomplete runs (without sweep-results artifact) still display results

## 🚀 Next Steps

After testing locally:
1. Verify timeline appears correctly
2. Test interactivity (hover, click)
3. Check that real data loads properly
4. Confirm enhanced logs display correctly
5. Ready to commit and push changes!

---

**Happy Testing!** 🎉

The mathematical timeline brings a much more elegant and space-efficient way to visualize build history compared to the old card-based approach.
