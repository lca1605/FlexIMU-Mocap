# ESP32 Right Hand Tracker

Găng tay gồm 5 flex sensor và BNO055. ESP32 đọc ADC/IMU rồi gửi UART;
Python trên máy tính kiểm CRC, đổi điện trở flex, ước lượng
orientation bằng quaternion và dựng mô hình tay phải 3D.

## Kiến trúc

```text
Flex ADC + BNO055 -> ESP32 acquisition -> UART frame + CRC
                                               |
                                               v
SerialTransport -> decoder -> flex/quaternion filter -> hand model -> Matplotlib 3D
```

`SensorTransport` là interface độc lập; khi chuyển sang Wi-Fi chỉ cần bổ sung
transport mới. Firmware không giữ calibration và không tính góc tay.

### Bắt đầu đọc code từ đâu?

| Phần       | Điểm bắt đầu                                      | Vai trò                                             |
|------------|----------------------------------------------------|-----------------------------------------------------|
| Linux      | `hand_tracker.sh`                                  | Một cửa cho setup, build, flash, chạy 3D và test    |
| ESP32      | `esp32_firmware/main/main.cpp`                      | Khởi tạo cảm biến và gửi frame theo chu kỳ          |
| PC         | `pc_app/main.py`                                   | Nhận frame rồi cập nhật cửa sổ 3D                   |
| Test IMU   | `pc_app/imu_web.py`                               | Máy bay 3D trên web để thử riêng BNO055             |
| Xử lý      | `pc_app/hand_tracker/processing.py`                | Đổi dữ liệu cảm biến thành `HandState`              |
| Thuật toán | `pc_app/hand_tracker/signal_processing.py`         | Gyro bias và quaternion fusion                      |
| Hiển thị   | `pc_app/hand_tracker/model.py`, `visualizer.py`     | Hình học bàn tay và Matplotlib                      |
| Test PC    | `pc_app/tests/`                                    | Kiểm tra protocol, bộ lọc và mô hình                |

Firmware được gom trong `esp32_firmware/main/`: mỗi driver vẫn có cặp `.cpp/.hpp`
riêng, nhưng tất cả dùng chung một `main/CMakeLists.txt`. Cách này giảm số thư mục
và gần cấu trúc project STM32CubeMX hơn mà `main.cpp` vẫn chỉ làm nhiệm vụ điều phối.

## Đấu nối

Xem [docs/wiring.md](docs/wiring.md). Thứ tự cái→út dùng lần lượt GPIO36/VP,
GPIO33, GPIO32, GPIO35 và GPIO34; cả năm đều thuộc ADC1 nên dùng được cùng Wi-Fi.
BNO055 dùng UART2: `SDA/TX → GPIO16`, `SCL/RX → GPIO17`; xem riêng
[sơ đồ test IMU](docs/imu_test.md). Mỗi flex nối từ 3.3 V tới ADC; điện trở cố định
220 kΩ và tụ 0,22 µF riêng nối từ ADC xuống GND.

Điện trở duỗi/gập cực đại đang cấu hình:

| Ngón  |   Duỗi | Gập cực đại |
|-------|-------:|------------:|
| Cái   | 200 kΩ |      340 kΩ |
| Trỏ   | 150 kΩ |      230 kΩ |
| Giữa  | 130 kΩ |      310 kΩ |
| Áp út | 100 kΩ |      270 kΩ |
| Út    | 230 kΩ |      425 kΩ |

## Protocol UART

115200-8-N-1, 50 Hz:

```text
HAND,seq,time_us,f0,f1,f2,f3,f4,ax,ay,az,gx,gy,gz,mx,my,mz*CCCC\n
```

`f0..f4` là ADC 12-bit theo thứ tự cái→út. IMU là raw signed 16-bit. `CCCC` là
CRC-16/CCITT-FALSE của phần trước dấu `*` (init `0xFFFF`, polynomial `0x1021`).

## Lệnh Linux nhanh

```bash
cd /home/lecongcomputer/esp32_right_hand_tracker
./hand_tracker.sh setup
./hand_tracker.sh build
./hand_tracker.sh flash /dev/ttyUSB0
./hand_tracker.sh imu-test /dev/ttyUSB0
./hand_tracker.sh run /dev/ttyUSB0
```

`build` chỉ biên dịch và không nạp phần cứng. `flash` mới ghi firmware vào ESP32.
Dùng `./hand_tracker.sh help` để xem cả lệnh `monitor`, `flash-monitor` và `test`.
Script tự tìm ESP-IDF và `IDF_TOOLS_PATH` trên máy hiện tại; nếu chuyển máy, đặt
biến `ESP_IDF_EXPORT=/đường/dẫn/esp-idf/export.sh`.

Để thử riêng giao diện bàn tay phải 3D khi chưa cắm ESP32, chạy
`./hand_tracker.sh imu-demo` rồi mở `http://127.0.0.1:8000`.

### Test LED D12

Mắc `GPIO12 → điện trở 220–1000 Ω → cực dương LED`, cực âm LED nối `GND`, rồi chạy:

```bash
./hand_tracker.sh blink-flash /dev/ttyUSB0
```

LED đổi trạng thái mỗi 500 ms. GPIO12 là chân strapping của ESP32, vì vậy không
nối nó lên 3V3 khi reset. Muốn trở lại firmware Hand Tracker, chạy lại lệnh
`./hand_tracker.sh flash /dev/ttyUSB0`.

### Dò địa chỉ I²C

Nạp scanner và xem kết quả liên tục:

```bash
./hand_tracker.sh i2c-scan /dev/ttyUSB0
```

Scanner quét `0x03–0x77` ở 100 kHz mỗi hai giây. Mỗi địa chỉ được in cùng số lần
ACK trên tổng số vòng; BNO055 bình thường phải xuất hiện ổn định tại `0x28` hoặc
`0x29`. Thoát bằng `Ctrl+]`, sau đó dùng `./hand_tracker.sh flash` để trở lại
firmware Hand Tracker.

## Chạy Python

```bash
./hand_tracker.sh setup
./hand_tracker.sh run /dev/ttyUSB0
```

Timer độ phân giải microsecond trên ESP32 lấy một lượt năm kênh flex mỗi 1,25 ms
(800 Hz). Đủ 16 lượt trong mỗi chu kỳ 20 ms, firmware gửi trung bình cộng đã làm
tròn, tức mỗi ngón có 800 lần chuyển đổi ADC/giây và 50 giá trị đầu ra/giây. Lịch
lấy mẫu ADC chạy độc lập với thời gian giao dịch UART của BNO055. PC dùng trực
tiếp từng giá trị này, chỉ đổi ADC sang điện trở rồi chuẩn hóa độ gập; PC không
lọc thêm để tránh lọc hai lần và tăng độ trễ.
Trang web IMU nhận năm độ gập và dựng ba đốt cho từng ngón, vì vậy mô hình vừa
xoay theo quaternion BNO055 vừa gập độc lập theo các flex sensor.
Orientation được lưu dưới dạng quaternion `(w, x, y, z)`. Bộ lọc Madgwick 9-DOF
tích phân gyro trực tiếp trên quaternion, rồi dùng gradient từ accel và mag để
khử drift với `beta = 0,1`. Khi từ kế mất dữ liệu, bộ lọc tự chuyển sang 6-DOF.
Trước khi lọc, dữ liệu BNO055 được đổi thành `(Y, X, -Z)` trong khi hình học bàn
tay được giữ nguyên; nhờ vậy chuyển động dọc và ngang không còn bị đổi chéo. Bias gyro được tự động học sau
0,5 s đứng yên và cập nhật chậm để bù thay đổi nhiệt độ trước khi vào Madgwick.
Vì không chuyển qua roll/pitch/yaw nên pipeline
không gặp gimbal lock. BNO055 chạy chế độ AMG, vì vậy fusion nội bộ của chip không
được dùng. Các góc cực đại từng khớp nằm trong `pc_app/hand_tracker/config.py`.

## Test

```bash
./hand_tracker.sh test
```

Test bao phủ CRC/parser, công thức cầu phân áp, đường dữ liệu flex không lọc trên
PC và quy ước trục mô hình.
