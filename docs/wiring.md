# Sơ đồ chân và đấu nối

## ESP32 DevKit / ESP32-D0WD-V3

| Tín hiệu       |                GPIO | Ghi chú                                      |
|----------------|--------------------:|----------------------------------------------|
| Flex ngón cái  | VP / GPIO36 / ADC1_CH0 | GPIO chỉ input                            |
| Flex ngón trỏ  | GPIO33 / ADC1_CH5   | Nút giữa cầu phân áp                         |
| Flex ngón giữa | GPIO32 / ADC1_CH4   | Nút giữa cầu phân áp                         |
| Flex ngón áp út | GPIO35 / ADC1_CH7   | GPIO chỉ input                               |
| Flex ngón út   | GPIO34 / ADC1_CH6   | GPIO chỉ input                               |
| BNO055 SDA/TX  | GPIO16 / RX2        | UART TX cảm biến nối chéo vào RX ESP32       |
| BNO055 SCL/RX  | GPIO17 / TX2        | UART RX cảm biến nối chéo vào TX ESP32       |
| BNO055 VIN     | 3V3                 | Không cấp 5 V nếu board không có regulator   |
| BNO055 GND     | GND                 | Chung mass với ESP32 và các cầu phân áp      |

Mỗi cảm biến flex mắc riêng như sau:

```text
3V3 ---- flex sensor ----+---- GPIO ADC
                         |
                     +---+---+
                     |       |
                   220 kΩ  0,22 µF
                     |       |
GND -----------------+-------+
```

Mỗi ngón dùng một tụ 0,22 µF riêng từ GPIO ADC xuống GND để giảm nhiễu; tụ gốm
không phân cực. Không đưa điện áp cao hơn 3.3 V vào GPIO. ADC dùng attenuation
12 dB và độ phân giải 12-bit. Cả năm chân đều thuộc ADC1 nên không xung đột với
Wi-Fi. `VP` là GPIO36/ADC1_CH0 và chỉ dùng làm input.

## Hướng gắn BNO055

Gắn chắc breakout trên mu bàn tay và căn các trục in trên breakout trùng hệ tay:

- `+X`: từ đầu ngón tay xuống lòng bàn tay/cổ tay.
- `+Y`: từ ngón cái sang ngón út.
- `+Z`: vuông góc hướng lên khỏi lòng bàn tay, tạo tam diện thuận.

Phần mềm giữ nguyên hình học bàn tay và chỉ đổi dữ liệu accel, gyro, từ kế theo
`(Y cảm biến, X cảm biến, -Z cảm biến)`. Việc tách riêng hai lớp này tránh trường
hợp đổi cảm biến và đổi mô hình đồng thời rồi vô tình triệt tiêu hiệu quả sửa trục.
