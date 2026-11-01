from abc import ABC, abstractmethod

from .protocol import SensorFrame, decode_frame


class SensorTransport(ABC):
    """Ranh giới transport để UART có thể được thay bằng Wi-Fi sau này."""

    @abstractmethod
    def receive(self) -> SensorFrame:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class SerialTransport(SensorTransport):
    def __init__(self, port: str, baud_rate: int = 115200, timeout_s: float = 1.0):
        # Import tại đây để module vẫn đọc và test được khi máy chưa cài pyserial.
        import serial
        self._serial = serial.Serial(port, baud_rate, timeout=timeout_s)

    def receive(self) -> SensorFrame:
        # Bỏ qua boot log và frame hỏng; chỉ trả dữ liệu đã qua kiểm tra protocol.
        while True:
            line = self._serial.readline()
            if not line:
                raise TimeoutError("không nhận được frame UART")
            try:
                return decode_frame(line)
            except (UnicodeError, ValueError):
                # Boot log hoặc frame hỏng không được đưa vào pipeline.
                continue

    def close(self) -> None:
        self._serial.close()
