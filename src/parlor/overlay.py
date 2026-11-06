"""Pure geometry mapping functions for camera landmark overlays.

Maps normalized landmark coordinates [0, 1] from camera frames to canvas
pixel coordinates, correctly handling:
- Object fit modes ('cover' and 'contain')
- Video mirroring (CSS scaleX(-1))
- Optional bounding box crop
- High-DPI scaling
"""

from typing import Any, Dict, Optional, Tuple, Union


def map_landmark_to_canvas(
    norm_x: float,
    norm_y: float,
    src_w: float,
    src_h: float,
    dst_w: float,
    dst_h: float,
    object_fit: str = "cover",
    mirrored: bool = False,
    crop: Optional[Union[Dict[str, float], Tuple[float, float, float, float]]] = None,
) -> Tuple[float, float]:
    """Map normalized landmark coordinate to canvas pixel space.

    Args:
        norm_x: Normalized horizontal coordinate in [0, 1].
        norm_y: Normalized vertical coordinate in [0, 1].
        src_w: Width of source camera frame (pixels).
        src_h: Height of source camera frame (pixels).
        dst_w: Width of destination canvas (pixels).
        dst_h: Height of destination canvas (pixels).
        object_fit: 'cover' (fill destination, crop excess) or 'contain' (fit within, letterbox).
        mirrored: If True, flip horizontally to match CSS scaleX(-1) video transform.
        crop: Optional normalized crop box (x, y, w, h) or dict {'x': ..., 'y': ..., 'w': ..., 'h': ...}.

    Returns:
        (canvas_x, canvas_y) in canvas pixel coordinates.
    """
    if src_w <= 0 or src_h <= 0 or dst_w <= 0 or dst_h <= 0:
        return (0.0, 0.0)

    # 1. Apply crop if specified
    if crop is not None:
        if isinstance(crop, dict):
            cx = crop.get("x", 0.0)
            cy = crop.get("y", 0.0)
            cw = crop.get("w", crop.get("width", 1.0))
            ch = crop.get("h", crop.get("height", 1.0))
        elif isinstance(crop, (list, tuple)) and len(crop) >= 4:
            cx, cy, cw, ch = crop[0], crop[1], crop[2], crop[3]
        else:
            cx, cy, cw, ch = 0.0, 0.0, 1.0, 1.0
        x_src = cx + norm_x * cw
        y_src = cy + norm_y * ch
    else:
        x_src = norm_x
        y_src = norm_y

    # 2. Apply horizontal mirroring if camera is mirrored
    if mirrored:
        x_src = 1.0 - x_src

    # 3. Calculate aspect ratios and scale factor
    scale_x = dst_w / src_w
    scale_y = dst_h / src_h

    if object_fit == "contain":
        scale = min(scale_x, scale_y)
    else:  # default 'cover'
        scale = max(scale_x, scale_y)

    rendered_w = src_w * scale
    rendered_h = src_h * scale

    # Centering offsets
    offset_x = (dst_w - rendered_w) / 2.0
    offset_y = (dst_h - rendered_h) / 2.0

    canvas_x = offset_x + x_src * rendered_w
    canvas_y = offset_y + y_src * rendered_h

    return (canvas_x, canvas_y)

