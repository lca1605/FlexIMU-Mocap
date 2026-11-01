#include <array>
#include <cstdint>

#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "hardware_config.hpp"

namespace {
constexpr char kLogTag[] = "i2c_scanner";
constexpr uint8_t kFirstAddress = 0x03;
constexpr uint8_t kLastAddress = 0x77;
constexpr TickType_t kScanInterval = pdMS_TO_TICKS(2000);
constexpr int kProbeTimeoutMs = 20;
}  // namespace

extern "C" void app_main()
{
  // Scanner dùng đúng bus và tốc độ của firmware thật để kết quả có thể so sánh.
  const i2c_master_bus_config_t busConfig = {
    .i2c_port = hand::config::kI2cPort,
    .sda_io_num = hand::config::kI2cSdaPin,
    .scl_io_num = hand::config::kI2cSclPin,
    .clk_source = I2C_CLK_SRC_DEFAULT,
    .glitch_ignore_cnt = 7,
    .intr_priority = 0,
    .trans_queue_depth = 0,
    .flags = {.enable_internal_pullup = true, .allow_pd = false},
  };
  i2c_master_bus_handle_t bus = nullptr;
  ESP_ERROR_CHECK(i2c_new_master_bus(&busConfig, &bus));

  std::array<uint32_t, 128> seenCount{};
  uint32_t scanCount = 0;
  while (true) {
    ++scanCount;
    int foundCount = 0;
    ESP_LOGI(kLogTag, "Scan %lu: SDA=GPIO%d, SCL=GPIO%d, 100 kHz",
      static_cast<unsigned long>(scanCount),
      hand::config::kI2cSdaPin,
      hand::config::kI2cSclPin);

    for (uint8_t address = kFirstAddress; address <= kLastAddress; ++address) {
      if (i2c_master_probe(bus, address, kProbeTimeoutMs) == ESP_OK) {
        ++seenCount[address];
        ++foundCount;
        // Tỉ lệ số lần xuất hiện giúp nhận biết ACK thật với địa chỉ nhiễu chập chờn.
        ESP_LOGI(kLogTag, "  ACK 0x%02X, ổn định %lu/%lu vòng",
          address,
          static_cast<unsigned long>(seenCount[address]),
          static_cast<unsigned long>(scanCount));
      }
    }

    if (foundCount == 0) {
      ESP_LOGW(kLogTag, "  Không tìm thấy thiết bị I2C");
    }
    vTaskDelay(kScanInterval);
  }
}
