"""Spatial navigation shared by the TV screens (coordinates are widget centers)."""


def next_in_direction(current, points, direction):
    """Choose the nearest item in a directional cone; never wrap unexpectedly."""
    x, y = points[current]
    candidates = []
    for index, (px, py) in enumerate(points):
        if index == current:
            continue
        dx, dy = px - x, py - y
        along, across = {
            "right": (dx, abs(dy)), "left": (-dx, abs(dy)),
            "down": (dy, abs(dx)), "up": (-dy, abs(dx)),
        }[direction]
        if along > 1 and across <= along * 1.4:
            candidates.append((along + across * 2.5, index))
    return min(candidates)[1] if candidates else current
