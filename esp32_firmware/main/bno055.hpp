#pragma once

#include <cstddef>
#include <cstdint>

#include "esp_err.h"

struct ImuRawSample
{
  // Giá trị raw theo scale của BNO055; PC chịu trách nhiệm đổi sang đơn vị SI.
  int16_t accelX;
  int16_t accelY;
  int16_t accelZ;
  int16_t gyroX;
  int16_t gyroY;
  int16_t gyroZ;
  int16_t magX;
  int16_t magY;
  int16_t magZ;
};

class Bno055
{
public:
  // Khởi tạo UART2, kiểm tra chip ID và đưa cảm biến vào chế độ AMG.
  esp_err_t init();
  // Đọc đồng thời accel, gyro và từ kế để các trục cùng một thời điểm lấy mẫu.
  esp_err_t read(ImuRawSample &sample);

private:
  esp_err_t readRegisters(uint8_t address, uint8_t *data, std::size_t length);
  esp_err_t writeRegister(uint8_t address, uint8_t value);
};
