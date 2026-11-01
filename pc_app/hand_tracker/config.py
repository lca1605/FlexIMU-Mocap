from dataclasses import dataclass

# Thông số cầu phân áp dùng đổi ADC raw thành điện trở flex sensor.
VOLTAGE_REFERENCE_V = 3.3
ADC_MAX_CODE = 4095
FIXED_RESISTOR_OHM = 220_000.0


@dataclass(frozen=True)
class FlexCalibration:
    name: str
    straight_ohm: float
    bent_ohm: float


# Hai mốc điện trở ánh xạ tuyến tính thành độ gập chuẩn hóa 0..1 của từng ngón.
FLEX_CALIBRATIONS = (
    FlexCalibration("thumb", 200_000.0, 340_000.0),
    FlexCalibration("index", 150_000.0, 230_000.0),
    FlexCalibration("middle", 130_000.0, 310_000.0),
    FlexCalibration("ring", 100_000.0, 270_000.0),
    FlexCalibration("little", 230_000.0, 425_000.0),
)

# Tổng góc MCP/PIP/DIP tại độ gập cực đại. Có thể chỉnh sau khi thử găng thật.
FINGER_MAX_ANGLES_DEG = (
    (35.0, 45.0, 25.0),
    (70.0, 90.0, 65.0),
    (70.0, 95.0, 65.0),
    (70.0, 95.0, 65.0),
    (65.0, 90.0, 60.0),
)
