import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from hand_tracker.signal_processing import (
    GyroBiasEstimator,
    MadgwickFilter,
    quaternionToRotationMatrix,
    sensorToBodyVector,
)


def test_sensor_axes_are_swapped_and_z_is_negated():
    assert sensorToBodyVector((1.0, 2.0, 3.0)) == (2.0, 1.0, -3.0)


def test_gyro_bias_is_removed_after_sensor_stays_still():
    estimator = GyroBiasEstimator(minimumStationaryS=0.1)
    gyro = tuple(math.radians(value) for value in (0.4, -0.25, 0.1))

    for _ in range(5):
        corrected = estimator.update((0.0, 0.0, 9.81), gyro, 0.02)

    assert corrected == pytest.approx((0.0, 0.0, 0.0), abs=1e-12)
    assert estimator.biasRadS == pytest.approx(gyro)


def test_gyro_bias_does_not_learn_while_sensor_moves():
    estimator = GyroBiasEstimator(minimumStationaryS=0.1)
    movingGyro = (0.0, 0.0, math.radians(20.0))

    for _ in range(20):
        corrected = estimator.update((0.0, 0.0, 9.81), movingGyro, 0.02)

    assert corrected == pytest.approx(movingGyro)
    assert estimator.biasRadS == (0.0, 0.0, 0.0)


def test_level_north_facing_measurement_is_identity():
    fusion = MadgwickFilter()

    quaternion = fusion.update((0.0, 0.0, 9.81), (0.0, 0.0, 0.0),
                               (30.0, 0.0, 0.0), 0.02)

    assert quaternion == pytest.approx((1.0, 0.0, 0.0, 0.0))


def test_quaternion_represents_ninety_degree_yaw_without_euler_angles():
    fusion = MadgwickFilter()
    quaternion = fusion.update((0.0, 0.0, 9.81), (0.0, 0.0, 0.0),
                               (0.0, -30.0, 0.0), 0.02)

    rotation = quaternionToRotationMatrix(quaternion)

    assert rotation[0][0] == pytest.approx(0.0, abs=1e-9)
    assert rotation[1][0] == pytest.approx(1.0, abs=1e-9)
    assert rotation[2][0] == pytest.approx(0.0, abs=1e-9)


def test_gyro_integration_keeps_unit_quaternion():
    fusion = MadgwickFilter()
    for _ in range(100):
        quaternion = fusion.update((0.0, 0.0, 0.0),
                                   (0.0, math.radians(90.0), 0.0),
                                   (0.0, 0.0, 0.0), 0.01)

    norm = math.sqrt(sum(component * component for component in quaternion))
    assert norm == pytest.approx(1.0, abs=1e-12)
    rotation = quaternionToRotationMatrix(quaternion)
    assert rotation[0][0] == pytest.approx(0.0, abs=2e-3)
    assert rotation[2][0] == pytest.approx(-1.0, abs=2e-3)


def test_rejects_negative_beta():
    with pytest.raises(ValueError, match="beta"):
        MadgwickFilter(beta=-0.01)


def test_allows_zero_beta_for_gyro_only_operation():
    fusion = MadgwickFilter(beta=0.0)

    quaternion = fusion.update((0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                               (0.0, 0.0, 0.0), 0.02)

    assert quaternion == pytest.approx((1.0, 0.0, 0.0, 0.0))
