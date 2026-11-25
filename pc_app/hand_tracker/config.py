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
    # Mốc quy đổi từ trung vị ADC của 32 mẫu duỗi và 31 mẫu gập ngày 21/11/2026.
    FlexCalibration("thumb", 433_063.0, 834_918.0),
    FlexCalibration("index", 301_203.0, 532_003.0),
    FlexCalibration("middle", 313_077.0, 592_353.0),
    FlexCalibration("ring", 342_711.0, 750_797.0),
    FlexCalibration("little", 538_653.0, 865_422.0),
)

# Tổng góc MCP/PIP/DIP tại độ gập cực đại. Có thể chỉnh sau khi thử găng thật.
FINGER_MAX_ANGLES_DEG = (
    (35.0, 45.0, 25.0),
    (70.0, 90.0, 65.0),
    (70.0, 95.0, 65.0),
    (70.0, 95.0, 65.0),
    (65.0, 90.0, 60.0),
)
