from dataclasses import dataclass


@dataclass(frozen=True)
class SensorFrame:
    """Một frame UART đã kiểm CRC và tách thành các nhóm cảm biến raw."""
    sequence: int
    timestamp_us: int
    flex_raw: tuple[int, int, int, int, int]
    accel_raw: tuple[int, int, int]
    gyro_raw: tuple[int, int, int]
    mag_raw: tuple[int, int, int]


def crc16_ccitt(data: bytes) -> int:
    """Tính CRC-16/CCITT-FALSE giống implementation trên ESP32."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def decode_frame(line: bytes) -> SensorFrame:
    """Giải mã một frame HAND; phát sinh ValueError nếu format/CRC sai."""
    # Tách CRC khỏi payload trước khi decode ASCII để frame lỗi bị loại sớm.
    text = line.strip()
    payload, separator, crc_text = text.rpartition(b"*")
    if not separator or len(crc_text) != 4:
        raise ValueError("frame không có CRC 4 ký tự")
    try:
        expected_crc = int(crc_text, 16)
    except ValueError as error:
        raise ValueError("CRC không phải số hex") from error
    if crc16_ccitt(payload) != expected_crc:
        raise ValueError("CRC không khớp")

    # Sau khi CRC đúng mới kiểm prefix, số trường và kiểu dữ liệu.
    fields = payload.decode("ascii").split(",")
    if len(fields) != 17 or fields[0] != "HAND":
        raise ValueError("frame HAND phải có 16 trường dữ liệu")
    try:
        values = [int(value) for value in fields[1:]]
    except ValueError as error:
        raise ValueError("frame chứa giá trị không nguyên") from error
    if not all(0 <= value <= 4095 for value in values[2:7]):
        raise ValueError("ADC nằm ngoài miền 12-bit")
    # Chia 16 số theo đúng thứ tự protocol đã công bố trong README.
    return SensorFrame(
        sequence=values[0], timestamp_us=values[1],
        flex_raw=tuple(values[2:7]),
        accel_raw=tuple(values[7:10]),
        gyro_raw=tuple(values[10:13]),
        mag_raw=tuple(values[13:16]),
    )
