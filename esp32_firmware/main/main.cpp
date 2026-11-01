#include <cstdint>

#include "bno055.hpp"
#include "esp_check.h"
#include "esp_timer.h"
#include "flex_adc.hpp"
#include "uart_transport.hpp"

extern "C" void app_main()
{
  // Entry point chỉ sở hữu và nối ba module phần cứng/transport.
  FlexAdc flexAdc;
  Bno055 imu;
  UartTransport transport;

  // Dừng khởi động ngay nếu một thiết bị bắt buộc không khởi tạo được.
  ESP_ERROR_CHECK(flexAdc.init());
  ESP_ERROR_CHECK(imu.init());
  ESP_ERROR_CHECK(transport.init());

  uint32_t sequence = 0;
  while (true) {
    SensorFrame frame{};
    frame.sequence = sequence++;
    // Kết quả flex 20 ms đóng vai trò nhịp 50 Hz cho acquisition và truyền frame.
    if (flexAdc.read(frame.flexRaw) == ESP_OK) {
      frame.timestampUs = esp_timer_get_time();
    }
    if (frame.timestampUs != 0 && imu.read(frame.imu) == ESP_OK) {
      transport.send(frame);
    }
  }
}
