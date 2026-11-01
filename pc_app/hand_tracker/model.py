import math

import numpy as np

from .config import FINGER_MAX_ANGLES_DEG
from .signal_processing import quaternionToRotationMatrix
from .processing import HandState

# Hình học dùng mét; mỗi ngón gồm ba đốt bắt đầu tại một điểm trên lòng bàn tay.
BASES = np.array([[-0.055, 0.005, 0.0], [-0.032, -0.02, 0.0], [0.0, -0.025, 0.0],
                  [0.03, -0.02, 0.0], [0.055, -0.005, 0.0]])
LENGTHS = ((0.045, 0.032, 0.025), (0.05, 0.032, 0.024), (0.055, 0.036, 0.026),
           (0.052, 0.034, 0.024), (0.043, 0.028, 0.021))
SPREAD_DEG = (-55.0, -10.0, 0.0, 8.0, 18.0)


def hand_lines(state: HandState) -> list[np.ndarray]:
    """Tạo polyline 3D của lòng bàn tay và năm ngón trong hệ world."""
    # Lòng bàn tay là đường bao khép kín trong mặt phẳng local XY.
    lines = []
    palm = np.array([[-0.065, 0.04, 0], [0.065, 0.04, 0], [0.06, -0.025, 0],
                     [-0.05, -0.025, 0], [-0.065, 0.04, 0]], dtype=float)
    lines.append(palm)
    # Tính nối tiếp ba khớp; bend=0 là duỗi và bend=1 là gập cực đại.
    for base, lengths, spread, max_angles, bend in zip(
            BASES, LENGTHS, SPREAD_DEG, FINGER_MAX_ANGLES_DEG, state.bends):
        points = [base.copy()]
        position = base.copy()
        cumulative_bend = 0.0
        spread_rad = math.radians(spread)
        for length, max_angle in zip(lengths, max_angles):
            cumulative_bend += math.radians(max_angle * bend)
            direction = np.array([
                math.sin(spread_rad) * math.cos(cumulative_bend),
                -math.cos(spread_rad) * math.cos(cumulative_bend),
                -math.sin(cumulative_bend),
            ])
            position = position + length * direction
            points.append(position.copy())
        lines.append(np.array(points))
    # Hình học gốc dùng X ngang/Y dọc; đổi sang X dọc/Y ngang và đảo Z để giữ
    # tam diện thuận trước khi quay theo orientation đo được của mu bàn tay.
    lines = [line[:, [1, 0, 2]] * np.array([1.0, 1.0, -1.0]) for line in lines]
    rotation = np.array(quaternionToRotationMatrix(state.orientationQuaternion))
    return [line @ rotation.T for line in lines]
