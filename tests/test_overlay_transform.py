"""Unit tests for camera landmark overlay coordinate transformation.

Verifies mathematical accuracy of map_landmark_to_canvas across:
- 16:9 source (1920x1080, 1280x720)
- 4:3 source (640x480)
- Portrait source (720x1280)
- Mirror on / off (CSS scaleX(-1) parity)
- Object-fit 'cover' vs 'contain'
- Bounding box crop transformations
"""

import pytest
from parlor.overlay import map_landmark_to_canvas


def test_center_preservation():
    """Frame center (0.5, 0.5) must map to canvas center regardless of aspect ratio or mirror."""
    viewports = [
        # (src_w, src_h, dst_w, dst_h)
        (1920, 1080, 640, 360),   # 16:9 to 16:9
        (1920, 1080, 800, 600),   # 16:9 to 4:3
        (640, 480, 1280, 720),    # 4:3 to 16:9
        (720, 1280, 640, 360),    # Portrait to landscape
        (1280, 720, 400, 800),    # Landscape to portrait
    ]
    for src_w, src_h, dst_w, dst_h in viewports:
        for mode in ["cover", "contain"]:
            for mirrored in [False, True]:
                cx, cy = map_landmark_to_canvas(0.5, 0.5, src_w, src_h, dst_w, dst_h, object_fit=mode, mirrored=mirrored)
                assert pytest.approx(cx, abs=1e-3) == dst_w / 2.0
                assert pytest.approx(cy, abs=1e-3) == dst_h / 2.0


def test_16_9_cover_and_mirror():
    """Verify 16:9 source with cover and mirror on 16:9 canvas."""
    src_w, src_h = 1280, 720
    dst_w, dst_h = 640, 360

    # Without mirror: (0.2, 0.4) -> (0.2 * 640, 0.4 * 360) = (128, 144)
    x1, y1 = map_landmark_to_canvas(0.2, 0.4, src_w, src_h, dst_w, dst_h, object_fit="cover", mirrored=False)
    assert pytest.approx(x1) == 128.0
    assert pytest.approx(y1) == 144.0

    # With mirror: x flips to (1.0 - 0.2) * 640 = 0.8 * 640 = 512, y stays 144
    x2, y2 = map_landmark_to_canvas(0.2, 0.4, src_w, src_h, dst_w, dst_h, object_fit="cover", mirrored=True)
    assert pytest.approx(x2) == 512.0
    assert pytest.approx(y2) == 144.0


def test_4_3_to_16_9_cover():
    """Verify 4:3 camera feed displayed in 16:9 video frame under object-fit: cover."""
    src_w, src_h = 640, 480  # AR = 1.333
    dst_w, dst_h = 1600, 900  # AR = 1.777

    # Since dst is wider than src, scale is driven by width: scale = 1600 / 640 = 2.5
    # Rendered height = 480 * 2.5 = 1200 > 900
    # Vertical crop offset = (900 - 1200) / 2 = -150 px
    # At y = 0.0 (top edge of camera): canvas_y = -150 (cropped off top)
    # At y = 1.0 (bottom edge of camera): canvas_y = -150 + 1200 = 1050 (cropped off bottom)
    # At y = 0.5 (center): canvas_y = 450 (exact center of 900)
    top_x, top_y = map_landmark_to_canvas(0.5, 0.0, src_w, src_h, dst_w, dst_h, object_fit="cover", mirrored=False)
    assert pytest.approx(top_y) == -150.0

    bot_x, bot_y = map_landmark_to_canvas(0.5, 1.0, src_w, src_h, dst_w, dst_h, object_fit="cover", mirrored=False)
    assert pytest.approx(bot_y) == 1050.0


def test_portrait_to_landscape_cover():
    """Verify portrait camera (e.g. mobile 720x1280) displayed in landscape container under cover."""
    src_w, src_h = 720, 1280
    dst_w, dst_h = 640, 360

    # dst_w / src_w = 640 / 720 = 0.8888
    # dst_h / src_h = 360 / 1280 = 0.28125
    # Cover scale = max(0.8888, 0.28125) = 640 / 720 = 8/9
    # Rendered width = 640, rendered height = 1280 * (8/9) = 1137.77 px
    # Center y maps to 180 (exact center)
    cx, cy = map_landmark_to_canvas(0.5, 0.5, src_w, src_h, dst_w, dst_h, object_fit="cover", mirrored=True)
    assert pytest.approx(cx) == 320.0
    assert pytest.approx(cy) == 180.0


def test_crop_subregion():
    """Verify landmark mapping when a face bounding crop box is applied."""
    src_w, src_h = 1000, 1000
    dst_w, dst_h = 500, 500
    crop = {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6}

    # Center of crop is (0.5, 0.5) inside crop -> normalized (0.2 + 0.5 * 0.6) = 0.5
    cx, cy = map_landmark_to_canvas(0.5, 0.5, src_w, src_h, dst_w, dst_h, crop=crop)
    assert pytest.approx(cx) == 250.0
    assert pytest.approx(cy) == 250.0

    # (0, 0) inside crop -> normalized (0.2, 0.2) -> canvas (100, 100)
    ox, oy = map_landmark_to_canvas(0.0, 0.0, src_w, src_h, dst_w, dst_h, crop=crop)
    assert pytest.approx(ox) == 100.0
    assert pytest.approx(oy) == 100.0

