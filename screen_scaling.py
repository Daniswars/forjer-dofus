BASE_RESOLUTION = (3840, 2160)

_base_resolution = BASE_RESOLUTION
_target_resolution = None


def configure_resolution(base_resolution=BASE_RESOLUTION, target_resolution=None):
    global _base_resolution, _target_resolution
    _base_resolution = (int(base_resolution[0]), int(base_resolution[1]))
    if target_resolution is None:
        _target_resolution = None
    else:
        _target_resolution = (int(target_resolution[0]), int(target_resolution[1]))


def _resolve_target_resolution():
    if _target_resolution is not None:
        return _target_resolution

    try:
        import pyautogui

        size = pyautogui.size()
        return (int(size.width), int(size.height))
    except Exception:
        return _base_resolution


def get_scale_factors():
    base_w, base_h = _base_resolution
    target_w, target_h = _resolve_target_resolution()
    if not base_w or not base_h:
        return 1.0, 1.0
    return float(target_w) / float(base_w), float(target_h) / float(base_h)


def scale_x(value):
    scale_w, _ = get_scale_factors()
    return int(round(float(value) * scale_w))


def scale_y(value):
    _, scale_h = get_scale_factors()
    return int(round(float(value) * scale_h))


def scale_point(x, y=None):
    if y is None:
        x, y = x
    return scale_x(x), scale_y(y)


def scale_points(points):
    return [scale_point(point) for point in points]


def scale_region(region):
    x, y, width, height = region
    return scale_x(x), scale_y(y), scale_x(width), scale_y(height)


def scale_box(top_left, bottom_right):
    return scale_point(top_left), scale_point(bottom_right)


def get_resolution_info():
    target = _resolve_target_resolution()
    scale_w, scale_h = get_scale_factors()
    return {
        "base": _base_resolution,
        "target": target,
        "scale": (scale_w, scale_h),
    }