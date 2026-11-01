import math
from dataclasses import dataclass

from .config import ADC_MAX_CODE, FIXED_RESISTOR_OHM, FLEX_CALIBRATIONS, VOLTAGE_REFERENCE_V
from .signal_processing import (
    GyroBiasEstimator,
    MadgwickFilter,
    Quaternion,
    sensorToBodyVector,
)
from .protocol import SensorFrame


@dataclass(frozen=True)
class HandState:
    """Trạng thái đã xử lý mà model 3D sử dụng, không còn phụ thuộc ADC raw."""
    bends: tuple[float, float, float, float, float]
    orientationQuaternion: Quaternion
    resistances_ohm: tuple[float, float, float, float, float]


def adc_to_resistance(raw_code: int) -> float:
    # 3.3V -> flex -> ADC -> 220k -> GND; vẫn viết theo điện áp để thể hiện Vref.
    voltage = raw_code * VOLTAGE_REFERENCE_V / ADC_MAX_CODE
    if voltage <= 0.0:
        return float("inf")
    return FIXED_RESISTOR_OHM * (VOLTAGE_REFERENCE_V / voltage - 1.0)


def flexRawToState(
        rawValues: tuple[int, int, int, int, int],
) -> tuple[tuple[float, float, float, float, float],
           tuple[float, float, float, float, float]]:
    """Đổi năm mã ADC thành độ gập 0..1 và điện trở theo thứ tự cái -> út."""
    resistances = tuple(adc_to_resistance(value) for value in rawValues)
    bends = []
    for resistance, calibration in zip(resistances, FLEX_CALIBRATIONS):
        normalized = (resistance - calibration.straight_ohm) / (
            calibration.bent_ohm - calibration.straight_ohm)
        bends.append(min(1.0, max(0.0, normalized)))
    return tuple(bends), resistances


class HandProcessor:
    def __init__(self):
        self._gyroBiasEstimator = GyroBiasEstimator()
        self._orientationFusion = MadgwickFilter(beta=0.1)
        self._previous_timestamp_us: int | None = None

    def process(self, frame: SensorFrame) -> HandState:
        # Timestamp ESP32 phản ánh chu kỳ lấy mẫu, không phụ thuộc trễ UART.
        dt_s = 0.02 if self._previous_timestamp_us is None else (
            frame.timestamp_us - self._previous_timestamp_us) / 1_000_000.0
        self._previous_timestamp_us = frame.timestamp_us

        # PC chỉ hiệu chuẩn; lọc nhiễu flex đã được thực hiện trên ESP32.
        bends, resistances = flexRawToState(frame.flex_raw)

        # Đổi raw BNO055: accel 100 LSB/(m/s²), gyro 16 LSB/(°/s), mag 16 LSB/µT.
        accel = sensorToBodyVector(tuple(value / 100.0 for value in frame.accel_raw))
        gyroRadS = sensorToBodyVector(tuple(
            math.radians(value / 16.0) for value in frame.gyro_raw))
        mag = sensorToBodyVector(tuple(value / 16.0 for value in frame.mag_raw))
        gyroRadS = self._gyroBiasEstimator.update(accel, gyroRadS, dt_s)
        orientation = self._orientationFusion.update(accel, gyroRadS, mag, dt_s)
        return HandState(bends, orientation, resistances)
