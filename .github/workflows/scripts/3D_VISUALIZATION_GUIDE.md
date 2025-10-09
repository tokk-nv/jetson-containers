# 3D Timeline Visualization Guide

## Overview

The dashboard now supports **interactive 3D visualization** using Plotly.js, making it easier to see and interact with individual build instances across multiple runs.

## Features

### 🎲 3D Interactive Mode
- **Rotate**: Click and drag to rotate the 3D view
- **Zoom**: Scroll to zoom in/out
- **Pan**: Right-click and drag to pan
- **Click Bars**: Click on any bar to jump to that run's details
- **Hover**: Hover over bars to see detailed statistics

### 📊 2D Chart Mode (Original)
- Traditional stacked bar chart using Chart.js
- Compact view for quick overview
- Click bars to select runs

## Visualization Comparison

### 2D Mode
- **Pros**: Compact, familiar interface, good for quick overview
- **Cons**: Bars can overlap, harder to distinguish individual runs when many are displayed
- **Best for**: Quick status checks, overview of trends

### 3D Mode
- **Pros**:
  - Each status type (Success, Failed, Timeout, OOM, Started) is on a separate layer
  - Easy to see individual instances without overlap
  - Interactive rotation makes it easy to focus on specific data
  - Better for detailed analysis
- **Cons**: Takes slightly more screen space
- **Best for**: Detailed analysis, identifying specific problem runs

## Technical Implementation

### Libraries Used
- **Plotly.js 2.27.0**: For 3D bar chart rendering
- **Chart.js 3.9.1**: For 2D chart (existing)

### Data Structure
The 3D visualization uses 5 separate traces (layers):
1. **Success** (Green) - Bottom layer
2. **Failed** (Red) - Second layer
3. **Timeout** (Yellow) - Third layer
4. **OOM** (Orange) - Fourth layer
5. **Started** (Gray) - Top layer

Each trace contains:
- X-axis: Run date
- Y-axis: Status type
- Z-axis: Package count
- Custom data: Run ID for click handling

### Key Features

#### Interactive Controls
```javascript
// Toggle between modes
switchVisualization('2d')  // Switch to 2D
switchVisualization('3d')  // Switch to 3D
```

#### Click Handling
When you click a bar in 3D mode:
1. Extracts the run ID from the clicked bar
2. Updates the run selector dropdown
3. Loads the detailed results for that run
4. Updates the timeline selection

#### Camera Settings
Default view angle:
- Eye position: (1.5, 1.5, 1.3)
- Provides optimal viewing angle for all data

## Usage Tips

### For Best 3D Experience
1. **Start with default view**: The initial camera angle is optimized
2. **Rotate to see layers**: Drag to rotate and see how status types stack
3. **Zoom in on specific runs**: Scroll to focus on particular time periods
4. **Use Reset View button**: Click the home icon in the toolbar to reset camera

### When to Use Each Mode

**Use 2D Mode when:**
- You want a quick overview
- You're familiar with the data
- Screen space is limited

**Use 3D Mode when:**
- You need to analyze specific runs in detail
- You want to see the relationship between different status types
- You have many runs and need to distinguish between them
- You're investigating patterns across multiple runs

## Performance Considerations

- 3D chart is initialized **only when first viewed** (lazy loading)
- Handles up to 25 runs efficiently (configurable via `TIMELINE_RUNS_LIMIT`)
- Responsive design adapts to different screen sizes

## Browser Compatibility

- **Chrome/Edge**: Full support, best performance
- **Firefox**: Full support
- **Safari**: Full support (may have slight performance differences)
- **Mobile**: Touch gestures supported (pinch to zoom, drag to rotate)

## Customization

### Adjusting Camera Angle
Edit the `camera` settings in `initialize3DChart()`:
```javascript
camera: {
    eye: { x: 1.5, y: 1.5, z: 1.3 },  // Viewing position
    center: { x: 0, y: 0, z: 0 }       // Look-at point
}
```

### Changing Colors
Modify the `marker.color` values in each trace:
```javascript
marker: {
    color: '#28a745',  // Change this hex color
    line: {
        color: '#1e7e34',  // Border color
        width: 1
    }
}
```

### Adjusting Bar Spacing
Modify the layout scene settings:
```javascript
scene: {
    xaxis: { ... },
    yaxis: {
        categoryorder: 'array',
        categoryarray: ['Success', 'Failed', 'Timeout', 'OOM', 'Started']
    },
    zaxis: { ... }
}
```

## Troubleshooting

### 3D Chart Not Showing
1. Check browser console for Plotly loading errors
2. Verify Plotly CDN is accessible
3. Try clicking the "3D Interactive" button again

### Performance Issues
1. Reduce `TIMELINE_RUNS_LIMIT` in the Python script
2. Close other browser tabs
3. Try 2D mode for better performance

### Click Not Working
1. Ensure you're clicking directly on a bar (not empty space)
2. Check browser console for JavaScript errors
3. Verify `customdata` is properly set in traces

## Future Enhancements

Possible improvements:
- [ ] Add animation between time periods
- [ ] Support for comparing two runs side-by-side in 3D
- [ ] Export 3D view as image
- [ ] Custom color schemes
- [ ] Filter by status type in 3D view
- [ ] Timeline scrubber for animated playback

## Code Structure

### Files Modified
- `dashboard_generate_html.py`: Main dashboard generation script
  - Added Plotly.js CDN link
  - Added 3D visualization styles
  - Added toggle buttons HTML
  - Added `initialize3DChart()` JavaScript function
  - Added `switchVisualization()` JavaScript function

### Key Functions

#### `initialize3DChart()`
- Creates 5 separate 3D bar traces
- Configures layout and camera
- Sets up click handlers
- Initializes Plotly chart

#### `switchVisualization(mode)`
- Toggles between '2d' and '3d' modes
- Updates button states
- Lazy-loads 3D chart on first view

## Examples

### Typical Workflow
1. Open dashboard (defaults to 2D mode)
2. Click "🎲 3D Interactive" button
3. Rotate view to see status layers
4. Click on a red (Failed) bar to investigate
5. View detailed logs for that run
6. Switch back to 2D for quick overview

### Analysis Scenario
**Goal**: Find which runs had the most timeouts

1. Switch to 3D mode
2. Rotate to view the "Timeout" layer (yellow bars)
3. Identify tallest yellow bars
4. Click on those bars to investigate
5. Review timeout logs for patterns

## Support

For issues or questions:
1. Check browser console for errors
2. Verify all CDN resources load successfully
3. Test with a smaller dataset first
4. Compare with 2D mode to isolate issues

---

**Version**: 1.0
**Last Updated**: October 6, 2025
**Compatibility**: All modern browsers with WebGL support
