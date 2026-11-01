#pragma once

#include <array>
#include <cstdint>

#include "bno055.hpp"
#include "esp_err.h"

struct SensorFrame
{
  // Metadata dùng phát hiện mất frame và tính đúng khoảng thời gian lọc trên PC.
  uint32_t sequence;
  int64_t timestampUs;
  // Payload cảm biến giữ nguyên raw để firmware không phụ thuộc calibration.
  std::array<int, 5> flexRaw;
  ImuRawSample imu;
};

class UartTransport
{
public:
  // Mở UART0 ở cấu hình 115200-8-N-1.
  esp_err_t init();
  // Mã hóa frame ASCII, gắn CRC-16 rồi truyền trọn frame.
  esp_err_t send(const SensorFrame &frame);
};
