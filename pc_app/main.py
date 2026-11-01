import argparse

from hand_tracker.processing import HandProcessor
from hand_tracker.transport import SerialTransport
from hand_tracker.visualizer import HandVisualizer


def main() -> None:
    # Tham số dòng lệnh chỉ chọn cổng; xử lý chi tiết nằm trong các module riêng.
    parser = argparse.ArgumentParser(description="Hiển thị găng tay ESP32/BNO055")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Cổng UART của ESP32")
    args = parser.parse_args()

    # Ghép pipeline: UART -> xử lý cảm biến -> mô hình Matplotlib 3D.
    transport = SerialTransport(args.port)
    processor = HandProcessor()
    visualizer = HandVisualizer()
    try:
        # Mỗi frame hợp lệ tạo một trạng thái tay mới để cập nhật cửa sổ.
        while True:
            visualizer.update(processor.process(transport.receive()))
    except KeyboardInterrupt:
        pass
    finally:
        # Luôn nhả cổng serial để lần chạy tiếp theo có thể mở lại ngay.
        transport.close()


if __name__ == "__main__":
    main()
