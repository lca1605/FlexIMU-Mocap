import argparse
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from hand_tracker.processing import flexRawToState
from hand_tracker.protocol import SensorFrame
from hand_tracker.signal_processing import (
    GyroBiasEstimator,
    MadgwickFilter,
    sensorToBodyVector,
)
from hand_tracker.transport import SerialTransport


class ImuProcessor:
    """Đổi raw BNO055 thành quaternion và dữ liệu chẩn đoán cho web app."""

    def __init__(self):
        self._gyroBiasEstimator = GyroBiasEstimator()
        self._fusion = MadgwickFilter(beta=0.1)
        self._previousTimestampUs: int | None = None

    def process(self, frame: SensorFrame) -> dict:
        # Timestamp của ESP32 giữ dt đúng ngay cả khi HTTP hoặc UART bị trễ.
        dtS = 0.02 if self._previousTimestampUs is None else (
            frame.timestamp_us - self._previousTimestampUs) / 1_000_000.0
        self._previousTimestampUs = frame.timestamp_us

        # Scale raw theo datasheet BNO055 trước khi đưa gyro vào quaternion fusion.
        accel = sensorToBodyVector(tuple(value / 100.0 for value in frame.accel_raw))
        gyroDegS = sensorToBodyVector(tuple(value / 16.0 for value in frame.gyro_raw))
        gyroRadS = tuple(math.radians(value) for value in gyroDegS)
        mag = sensorToBodyVector(tuple(value / 16.0 for value in frame.mag_raw))
        gyroRadS = self._gyroBiasEstimator.update(accel, gyroRadS, dtS)
        gyroDegS = tuple(math.degrees(value) for value in gyroRadS)
        gyroBiasDegS = tuple(
            math.degrees(value) for value in self._gyroBiasEstimator.biasRadS)
        quaternion = self._fusion.update(accel, gyroRadS, mag, dtS)
        bends, _ = flexRawToState(frame.flex_raw)
        return {
            "connected": True,
            "sequence": frame.sequence,
            "quaternion": quaternion,
            "accel": accel,
            "gyroDegS": gyroDegS,
            "gyroBiasDegS": gyroBiasDegS,
            "mag": mag,
            "bends": bends,
            "flexRaw": frame.flex_raw,
            "error": "",
        }


class ImuStateStore:
    """Chia sẻ snapshot an toàn giữa thread đọc UART và HTTP server."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "connected": False,
            "sequence": 0,
            "quaternion": (1.0, 0.0, 0.0, 0.0),
            "accel": (0.0, 0.0, 0.0),
            "gyroDegS": (0.0, 0.0, 0.0),
            "gyroBiasDegS": (0.0, 0.0, 0.0),
            "mag": (0.0, 0.0, 0.0),
            "bends": (0.0, 0.0, 0.0, 0.0, 0.0),
            "flexRaw": (0, 0, 0, 0, 0),
            "error": "Đang chờ frame IMU",
        }

    def update(self, state: dict) -> None:
        with self._lock:
            self._state = state

    def setError(self, message: str) -> None:
        with self._lock:
            self._state = {**self._state, "connected": False, "error": message}

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._state)


def runSerial(port: str, stateStore: ImuStateStore) -> None:
    """Đọc frame UART liên tục; lỗi được đưa lên giao diện thay vì dừng HTTP."""
    transport = None
    try:
        transport = SerialTransport(port)
        processor = ImuProcessor()
        while True:
            stateStore.update(processor.process(transport.receive()))
    except Exception as error:
        stateStore.setError(f"UART {port}: {error}")
    finally:
        if transport is not None:
            transport.close()


def runDemo(stateStore: ImuStateStore) -> None:
    """Tạo quaternion chuyển động để kiểm tra web app khi chưa có phần cứng."""
    sequence = 0
    while True:
        elapsed = time.monotonic()
        yaw = 0.45 * elapsed
        pitch = 0.35 * math.sin(elapsed * 0.7)
        roll = 0.55 * math.sin(elapsed)
        cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
        cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
        cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
        quaternion = (
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        )
        bends = tuple(
            0.5 + 0.5 * math.sin(elapsed * 1.4 + index * 0.65)
            for index in range(5)
        )
        stateStore.update({
            "connected": True,
            "sequence": sequence,
            "quaternion": quaternion,
            "accel": (0.0, 0.0, 9.81),
            "gyroDegS": (0.0, 0.0, 25.8),
            "gyroBiasDegS": (0.0, 0.0, 0.0),
            "mag": (30.0, 0.0, 0.0),
            "bends": bends,
            "flexRaw": (0, 0, 0, 0, 0),
            "error": "",
        })
        sequence += 1
        time.sleep(0.02)


def createHandler(stateStore: ImuStateStore, page: bytes):
    class ImuRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/orientation":
                payload = json.dumps(stateStore.snapshot()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return
            self.send_error(404)

        def log_message(self, formatString, *args):
            # Không in một dòng log cho mỗi lần browser polling 20 Hz.
            pass

    return ImuRequestHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Test BNO055 bằng mô hình bàn tay phải 3D")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Cổng UART ESP32")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ web server")
    parser.add_argument("--web-port", type=int, default=8000, help="Cổng web server")
    parser.add_argument("--demo", action="store_true", help="Chạy mô phỏng không cần ESP32")
    args = parser.parse_args()

    stateStore = ImuStateStore()
    target = runDemo if args.demo else lambda store: runSerial(args.port, store)
    threading.Thread(target=target, args=(stateStore,), daemon=True).start()

    pagePath = Path(__file__).with_name("imu_web.html")
    page = pagePath.read_bytes()
    server = ThreadingHTTPServer((args.host, args.web_port), createHandler(stateStore, page))
    print(f"IMU 3D: http://{args.host}:{args.web_port}")
    print("Nhấn Ctrl+C để dừng.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
