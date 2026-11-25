# ESP32 Right Hand Tracker

Găng tay theo dõi độ gập của năm ngón và hướng xoay của bàn tay phải theo thời gian thực. ESP32 đọc năm cảm biến uốn (flex sensor) và BNO055, rồi gửi dữ liệu qua USB–serial. Python trên máy tính xử lý dữ liệu và dựng bàn tay 3D trên trình duyệt hoặc trong cửa sổ Matplotlib.

## Chạy thử trên máy mới

Mở terminal tại thư mục gốc của bản clone. Các lệnh dưới đây dùng Python 3.12 làm mốc cài đặt. Chế độ demo chạy bằng dữ liệu mô phỏng và chỉ cần Python cùng trình duyệt.

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pc_app/requirements.txt
.\.venv\Scripts\python.exe pc_app/imu_web.py --demo
```

**Linux (Bash)**

```bash
bash hand_tracker.sh setup
bash hand_tracker.sh imu-demo
```

Mở [http://127.0.0.1:8000](http://127.0.0.1:8000) để xem mô hình. Dừng bằng `Ctrl+C`. Trên Linux, script dùng `python3` để tạo môi trường ảo. Nếu máy thiếu module `venv`, cài gói tương ứng với bản Python đang dùng. Các thư viện PC được khai báo trong [pc_app/requirements.txt](pc_app/requirements.txt).

## Chuẩn bị găng tay

- ESP32 DevKit dùng ESP32-D0WD-V3 (target ESP-IDF là `esp32`), cáp USB truyền dữ liệu và driver USB–serial phù hợp với board nếu hệ điều hành chưa nhận cổng.
- Breakout BNO055 được cấu hình giao tiếp UART. Nối TX cảm biến vào GPIO16 (RX2), RX cảm biến vào GPIO17 (TX2), cấp 3,3 V và nối chung GND. Xem [chân nguồn và tín hiệu BNO055](docs/imu_test.md).
- Năm flex sensor, năm điện trở 220 kΩ và năm tụ 0,22 µF. Chân ADC theo thứ tự từ ngón cái đến ngón út là GPIO36 (VP), GPIO33, GPIO32, GPIO35 và GPIO34. Mỗi flex nối từ 3,3 V đến nút ADC. Điện trở và tụ mắc song song từ nút đó xuống GND. Xem [sơ đồ đấu nối đầy đủ](docs/wiring.md).

Có thể thử xoay bàn tay 3D chỉ với ESP32 và BNO055. Cần đấu đủ flex sensor để kiểm tra độ gập của từng ngón.

## Build và nạp firmware

Nếu ESP32 đã chạy firmware Hand Tracker tương thích, chuyển thẳng sang bước kết nối. Để build, cần bộ công cụ ESP-IDF cho target `esp32`. Bản build tham chiếu của repo dùng nhánh ESP-IDF 6.1. Build lại từ mã nguồn trên máy mới vì cache CMake có thể chứa đường dẫn tuyệt đối của máy đã tạo nó.

Trên Windows, mở terminal đã kích hoạt môi trường ESP-IDF. Trên Linux, cũng có thể chạy trực tiếp trong terminal đã nạp `export.sh`. Từ thư mục gốc repo, chạy:

```text
cd esp32_firmware
idf.py -B build-local -DHAND_TRACKER_BLINK_TEST=OFF -DHAND_TRACKER_I2C_SCANNER=OFF build
idf.py -B build-local -p COM3 flash
cd ..
```

Thay `COM3` bằng cổng thực tế, ví dụ `/dev/ttyUSB0` hoặc `/dev/ttyACM0` trên Linux. Lệnh `build` biên dịch firmware. Lệnh `flash` ghi firmware lên ESP32.

Trên Linux, `bash hand_tracker.sh help` liệt kê các lệnh rút gọn, gồm `build`, `flash`, `monitor` và `i2c-scan`. Nếu script chưa tìm được ESP-IDF, đặt `ESP_IDF_EXPORT` trỏ đến `export.sh` trên máy. Lệnh `i2c-scan` nạp firmware chẩn đoán riêng cho thiết bị đang nối I²C. Nạp lại Hand Tracker sau khi dùng scanner.

## Kết nối và sử dụng

Đóng serial monitor trước khi mở ứng dụng. Từ thư mục gốc repo, liệt kê các cổng bằng `python -m serial.tools.list_ports` với Python trong môi trường ảo, rồi chọn cổng của ESP32.

| Giao diện | Windows (PowerShell) | Linux (Bash) |
|---|---|---|
| Bàn tay 3D trên web | `.\.venv\Scripts\python.exe pc_app/imu_web.py --port COM3` | `bash hand_tracker.sh imu-test /dev/ttyUSB0` |
| Cửa sổ Matplotlib | `.\.venv\Scripts\python.exe pc_app/main.py --port COM3` | `bash hand_tracker.sh run /dev/ttyUSB0` |

Với giao diện web, mở [http://127.0.0.1:8000](http://127.0.0.1:8000). Giữ găng tay đứng yên ít nhất 0,5 giây để PC học độ lệch gyro. Đặt tay úp, hướng các đầu ngón về phía màn hình, rồi nhấn **Đặt tư thế chuẩn** để lấy hướng hiện tại làm mốc hiển thị. Nút này chỉ đặt mốc cho mô hình 3D. Bộ lọc vẫn tiếp tục cập nhật hướng từ dữ liệu cảm biến.

- Nếu cổng không xuất hiện, kiểm tra cáp USB và driver của board. Nếu cổng bận, đóng ứng dụng serial khác. Nếu Linux báo thiếu quyền, kiểm tra quyền truy cập cổng serial của tài khoản.
- Nếu trang không nhận dữ liệu, kiểm tra cổng đã chọn và firmware đang chạy. Nếu mô hình nhận frame nhưng xoay sai, kiểm tra hướng lắp và đường UART của BNO055 theo [sơ đồ đấu nối](docs/wiring.md).
- Nếu độ gập của ngón không khớp, kiểm tra giá trị ADC và cầu phân áp, rồi hiệu chuẩn mốc duỗi và gập trong [config.py](pc_app/hand_tracker/config.py). Mốc điện trở của cả năm ngón được quy đổi từ trung vị ADC đo trên găng khi duỗi thẳng và khi gập hết.

## Repo có gì?

| Vị trí | Nội dung |
|---|---|
| [esp32_firmware/main/](esp32_firmware/main/) | `main.cpp` điều phối thu thập mẫu. `hardware_config.hpp` giữ cấu hình chân và tần số. Các module riêng đọc ADC, giao tiếp BNO055 và đóng gói UART. |
| [pc_app/main.py](pc_app/main.py) | Entrypoint của ứng dụng Matplotlib. |
| [pc_app/imu_web.py](pc_app/imu_web.py), [imu_web.html](pc_app/imu_web.html) | Server web cục bộ và giao diện bàn tay phải 3D, dùng serial thật hoặc dữ liệu demo. |
| [pc_app/hand_tracker/](pc_app/hand_tracker/) | Đọc serial, giải mã frame, quy đổi flex, ước lượng quaternion và dựng hình học tay. |
| [pc_app/tests/](pc_app/tests/) | Kiểm thử protocol, xử lý flex, orientation và dữ liệu web. |
| [hand_tracker.sh](hand_tracker.sh), [docs/](docs/) | Lệnh tiện ích cho Linux và tài liệu đấu nối. |

## Luồng dữ liệu và giao thức

Firmware lấy 800 mẫu ADC/giây trên mỗi kênh, lấy trung bình 16 mẫu rồi gửi một frame ở 50 Hz. PC đổi ADC trung bình thành điện trở, sau đó dùng mốc riêng của từng ngón để chuẩn hóa độ gập về 0–1.

BNO055 chạy chế độ AMG. PC áp dụng cùng phép đổi trục `(x, y, z) → (y, x, -z)` cho gia tốc, gyro và từ kế. Sau khi trừ độ lệch gyro đã học, Madgwick 9-DOF ước lượng hướng dưới dạng quaternion `(w, x, y, z)` và chuyển sang 6-DOF khi thiếu dữ liệu từ kế. Hướng cảm biến và hình học bàn tay được xử lý ở các lớp riêng.

ESP32 gửi frame ASCII qua serial ở 115200 baud, 8 bit dữ liệu, không parity, 1 bit stop.

```text
HAND,seq,time_us,f0,f1,f2,f3,f4,ax,ay,az,gx,gy,gz,mx,my,mz*CCCC\n
```

`seq` là số thứ tự frame và `time_us` là thời gian từ lúc ESP32 khởi động, tính bằng micro giây. `f0..f4` là ADC 12 bit theo thứ tự cái đến út. Chín trường IMU là số thô có dấu 16 bit. `CCCC` là bốn chữ số hex của CRC-16/CCITT-FALSE (giá trị đầu `0xFFFF`, đa thức `0x1021`) tính trên phần trước dấu `*`. Mỗi frame kết thúc bằng LF.

## Kiểm thử

Chạy từ thư mục gốc repo. Bộ test PC dùng pytest và chạy được khi chưa cắm ESP32.

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest
```

```bash
.venv/bin/python -m pip install pytest
bash hand_tracker.sh test
```
