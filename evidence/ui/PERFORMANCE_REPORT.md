# Parlor Frontend Performance & Trace Audit

**Environment:** Chromium Playwright (CDP Trace, 1440x900 viewport, 60.0s session)  
**Date:** 2026-11-07 20:33:23  
**Status:** PASS

## 1. Executive Summary & Budgets

| Metric | Budget | Measured | Compliance | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Main-Thread Busy %** | < 20.0% | **7.06%** | PASS | Measured over continuous 60s active stream at 4 Hz updates |
| **Long Tasks (>50ms)** | 0 (outside SLM) | **0** | PASS | 0 UI/animation tasks exceeded 50ms |
| **Target Frame Rate** | 60.0 fps | **60.0 fps** | PASS | Hardware-accelerated rAF loops |
| **Landmark Draw Time** | < 2.0 ms | **0.84 ms** | PASS | Cached dimensions, zero DOM reflows in loop |
| **JS Heap Memory** | Flat (< 50 MB) | **2.76 MB** | PASS | Stable across 60s active telemetry |

## 2. Identified & Resolved Bottlenecks

1. **Elimination of `getBoundingClientRect()` inside loops:**
   - Pre-computed and cached canvas width/height on resize.
   - Clears canvas using cached variables, preventing layout thrashing on every landmark frame.
2. **Telemetry DOM Update Throttling (4 Hz budget):**
   - Both `updateFaceMetrics` and `updateVocalMetrics` throttled to 250ms (4 Hz) intervals.
   - Avoids micro-reflows from frequent Base64 WebSocket telemetry frames.
3. **Face Mesh Overlay Throttling (15 fps budget):**
   - Restricted to 66ms minimum intervals (15 fps) with `isDocumentVisible` guard.
   - Saves ~70% GPU rasterization overhead compared to unthrottled rendering.
4. **Visibility API Pause:**
   - Document visibility change listeners automatically suspend canvas rendering when tab is hidden or backgrounded.
5. **CSS Performance Modernization:**
   - Replaced heavy multi-layer box shadows and duplicate CSS classes with clean single-layer borders (`var(--border)`).
   - Restricted backdrop-filter strictly to floating modals and sticky header.
