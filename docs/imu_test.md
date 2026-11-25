# Test riêng BNO055 bằng bàn tay phải 3D

Phần test này chỉ cần ESP32 và BNO055 để kiểm tra hướng xoay. Web app
đọc cả IMU và flex. Cần đấu các flex sensor để kiểm tra độ gập.

## Sơ đồ chân

| BNO055 | ESP32 DevKit | Chức năng                              |
|:------:|:------------:|----------------------------------------|
| `VIN`  | `3V3`        | Nguồn 3,3 V                            |
| `GND`  | `GND`        | Mass chung                              |
| `SDA/TX` | `GPIO16`   | TX BNO055 nối chéo vào RX UART2 ESP32   |
| `SCL/RX` | `GPIO17`   | RX BNO055 nối chéo vào TX UART2 ESP32   |
| `BOOT` | `3V3`        | Không vào bootloader                     |
| `REST` | `3V3`        | Không giữ cảm biến trong reset           |

```text
ESP32 DevKit                         BNO055

3V3  ------------------------------- VIN
GND  ------------------------------- GND
GPIO16 (RX2) ------------------------ SDA/TX
GPIO17 (TX2) ------------------------ SCL/RX
3V3  ------------------------------- BOOT
3V3  ------------------------------- REST
```

Không cấp 5 V nếu breakout BNO055 không có bộ ổn áp. Breakout thường đã có điện
trở kéo lên SDA/SCL; các điện trở này không ảnh hưởng khi module chạy UART.
Firmware dùng UART `115200-8-N-1`; `AD0` và `INT` không cần nối trong chế độ này.

## Chạy test

Firmware đọc BNO055 và gửi dữ liệu ở 50 Hz. Chạy các lệnh dưới đây từ thư mục gốc repo trên Linux. Xem [README](../README.md) để cài môi trường và chạy trên Windows.

```bash
bash hand_tracker.sh build
bash hand_tracker.sh flash /dev/ttyUSB0
```

Chạy web app với ESP32 thật:

```bash
bash hand_tracker.sh imu-test /dev/ttyUSB0
```

Mở `http://127.0.0.1:8000` trên trình duyệt. Khi xoay BNO055, bàn tay phải sẽ xoay
theo quaternion. Các trục là `+X` từ đầu ngón về lòng bàn tay, `+Y` từ ngón cái
sang ngón út và `+Z` hướng lên. Đặt tay úp, các đầu ngón hướng vào màn hình rồi
nhấn **Đặt tư thế chuẩn** để lấy góc hiện tại làm mốc. Dừng server bằng `Ctrl+C`.
Giữ IMU đứng yên ít nhất 0,5 giây để chương trình nhận diện trạng thái tĩnh, học
bias gyro và trừ bias trước bộ lọc Madgwick; giá trị bias hiện ở bảng bên phải.

Muốn kiểm tra giao diện trước khi cắm ESP32:

```bash
bash hand_tracker.sh imu-demo
```

Nếu không mở được UART, kiểm tra tên cổng bằng `ls /dev/ttyUSB* /dev/ttyACM*` và
đảm bảo tài khoản hiện tại có quyền truy cập cổng serial.
