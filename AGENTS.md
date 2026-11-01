# Ngữ cảnh phát triển Hand Tracker

Project độc lập, tái sử dụng phong cách kiến trúc của ARM Car:

- `esp32_firmware/`: ESP-IDF trên ESP32-D0WD-V3, chỉ thu thập ADC/BNO055 và gửi UART.
- `pc_app/`: Python nhận frame, kiểm CRC, lọc flex, fusion orientation bằng
  quaternion và dựng tay 3D.

Giữ entrypoint chỉ để khởi tạo và điều phối. Tách phần cứng, protocol, transport,
xử lý tín hiệu và visualization thành module. Tên mới dùng `camelCase`, type dùng
`PascalCase`, constant dùng `kPascalCase`. Comment tiếng Việt giải thích đơn vị,
giao thức và lý do. Mọi thay đổi protocol/đấu nối phải cập nhật README và test.

Không flash phần cứng nếu người dùng chưa yêu cầu. Chạy `pytest` cho phía PC và
`idf.py build` cho firmware khi toolchain khả dụng.

## Ngữ cảnh orientation đã chốt

- BNO055 chạy chế độ AMG; Python dùng Madgwick 9-DOF và tự học gyro bias khi đứng
  yên. ESP32 chỉ đọc dữ liệu thô và truyền UART.
- Ánh xạ hiện tại trước gyro bias/Madgwick phải giữ đúng:
  `X xử lý = Y cảm biến`, `Y xử lý = X cảm biến`, `Z xử lý = -Z cảm biến`, tức
  `sensorToBodyVector((x, y, z)) -> (y, x, -z)`.
- Áp dụng cùng ánh xạ cho accelerometer, gyroscope và magnetometer. Không đổi riêng
  một loại cảm biến.
- Hình học bàn tay và camera là lớp độc lập với ánh xạ cảm biến. Không đổi đồng
  thời cả hình học/camera và ánh xạ cảm biến vì hai thay đổi có thể triệt tiêu nhau.
- Không tự thêm phép nghịch đảo quaternion ở đầu ra. Thử nghiệm này đã được
  rollback vì không giải quyết lỗi chuyển động dọc/ngang.
- Web hiển thị bàn tay phải 3D và có nút `Đặt tư thế chuẩn`; nút chỉ đặt mốc hiển
  thị, không thay đổi ánh xạ cảm biến hoặc state của Madgwick.
