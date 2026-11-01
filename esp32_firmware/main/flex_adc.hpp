#pragma once

#include <array>
#include <cstdint>

#include "esp_err.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

class FlexAdc
{
public:
  // Cấu hình ADC1 và timer 800 Hz lấy mẫu đều năm kênh flex.
  esp_err_t init();
  // Chờ và trả về trung bình 16 lượt theo thứ tự cái, trỏ, giữa, áp út và út.
  esp_err_t read(std::array<int, 5> &rawValues);

private:
  static void sampleTimerCallback(void *context);
  void sampleOnce();

  void *handle_{nullptr};
  esp_timer_handle_t sampleTimer_{nullptr};
  QueueHandle_t resultQueue_{nullptr};
  std::array<uint32_t, 5> sums_{};
  int sampleCount_{0};
};
