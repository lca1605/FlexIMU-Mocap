import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from hand_tracker.config import (
    ADC_MAX_CODE,
    FIXED_RESISTOR_OHM,
    FLEX_CALIBRATIONS,
    VOLTAGE_REFERENCE_V,
)
from hand_tracker.model import hand_lines
from hand_tracker.processing import HandProcessor, HandState, adc_to_resistance, flexRawToState
from hand_tracker.protocol import SensorFrame


def raw_for_resistance(resistance: float) -> int:
    voltage = VOLTAGE_REFERENCE_V * FIXED_RESISTOR_OHM / (resistance + FIXED_RESISTOR_OHM)
    return round(voltage / VOLTAGE_REFERENCE_V * ADC_MAX_CODE)


def test_voltage_divider_recovers_flex_resistance():
    expected = 200_000.0
    recovered = adc_to_resistance(raw_for_resistance(expected))
    assert math.isclose(recovered, expected, rel_tol=0.002)


def test_flex_sample_is_not_temporally_filtered_on_pc():
    processor = HandProcessor()
    straightRaw = tuple(
        raw_for_resistance(calibration.straight_ohm)
        for calibration in FLEX_CALIBRATIONS
    )
    bentRaw = (
        raw_for_resistance(FLEX_CALIBRATIONS[0].bent_ohm),
        *straightRaw[1:],
    )
    common = {
        "accel_raw": (0, 0, 981),
        "gyro_raw": (0, 0, 0),
        "mag_raw": (160, 0, 0),
    }

    processor.process(SensorFrame(0, 0, straightRaw, **common))
    state = processor.process(SensorFrame(1, 20_000, bentRaw, **common))

    assert state.bends[0] > 0.99


def test_flex_raw_to_state_calibrates_each_finger():
    rawValues = tuple(
        raw_for_resistance(calibration.bent_ohm)
        for calibration in FLEX_CALIBRATIONS
    )

    bends, _ = flexRawToState(rawValues)

    assert bends == pytest.approx((1.0, 1.0, 1.0, 1.0, 1.0), abs=0.01)


def test_straight_fingers_extend_toward_negative_x():
    state = HandState((0, 0, 0, 0, 0), (1, 0, 0, 0), (0, 0, 0, 0, 0))
    index_finger = hand_lines(state)[2]
    assert index_finger[-1, 0] < index_finger[0, 0]
    assert math.isclose(index_finger[-1, 2], 0.0, abs_tol=1e-9)


def test_bent_finger_moves_toward_positive_z():
    state = HandState((0, 1, 0, 0, 0), (1, 0, 0, 0), (0, 0, 0, 0, 0))
    index_finger = hand_lines(state)[2]
    assert index_finger[-1, 2] > 0.0
