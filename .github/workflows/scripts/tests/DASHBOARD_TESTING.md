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
├── index.html              # Main dashboard (open this in browser!)
├── report.md               # Markdown summary report
├── results-data/
│   └── results.json        # Current build results
├── runs/
│   ├── results-*.json      # Historical run data
│   └── ...
└── logs/
    ├── *.log              # Raw log files
    ├── *.html             # Enhanced HTML logs
    └── ...
```

## 🔧 How It Works

1. **Environment Setup**: Creates test directory structure
2. **Data Fetching**: Uses your PAT to pull from `nvidia-ai-iot/jetson-containers`
3. **Script Execution**: Runs our local dashboard scripts:
   - `dashboard_download_current_artifacts.py`
   - `dashboard_download_historical_runs.py`
   - `dashboard_process_log_files.py`
   - `log_to_html_converter.py`
   - `dashboard_generate_html.py`
   - `dashboard_generate_report.py`
4. **Output Generation**: Creates complete dashboard with new timeline

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

## 🎯 What to Look For

When testing the new timeline design:

1. **Positioning**: Markers should be positioned chronologically along the axis
2. **Colors**: Health status colors should reflect actual success rates
3. **Interactivity**: Smooth hover effects and clickable functionality
4. **Data Accuracy**: Popup stats should match the actual build results
5. **Responsiveness**: Timeline should work on different screen sizes

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
