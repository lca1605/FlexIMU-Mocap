#include "uart_transport.hpp"

#include <array>
#include <cstdio>
#include <cstring>

#include "driver/uart.h"
#include "hardware_config.hpp"

namespace {
uint16_t crc16Ccitt(const char *data, std::size_t length)
{
  // CRC-16/CCITT-FALSE: init 0xFFFF, polynomial 0x1021, không reflect.
  uint16_t crc = 0xFFFF;
  for (std::size_t index = 0; index < length; ++index) {
    crc ^= static_cast<uint16_t>(static_cast<uint8_t>(data[index])) << 8;
    for (int bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000U) != 0U ? static_cast<uint16_t>((crc << 1) ^ 0x1021U)
                                  : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}
}  // namespace

esp_err_t UartTransport::init()
{
  // UART0 dùng chung cổng USB serial của board, không bật flow control.
  const uart_config_t config = {
    .baud_rate = hand::config::kBaudRate,
    .data_bits = UART_DATA_8_BITS,
    .parity = UART_PARITY_DISABLE,
    .stop_bits = UART_STOP_BITS_1,
    .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    .rx_flow_ctrl_thresh = 0,
    .rx_glitch_filt_thresh = 0,
    .source_clk = UART_SCLK_DEFAULT,
    .flags = {},
  };
  ESP_RETURN_ON_ERROR(uart_param_config(hand::config::kUartPort, &config), "uart", "UART config failed");
  return uart_driver_install(hand::config::kUartPort, 256, 1024, 0, nullptr, 0);
}

esp_err_t UartTransport::send(const SensorFrame &frame)
{
  // Payload ASCII giúp kiểm tra trực tiếp bằng serial monitor khi chẩn đoán.
  std::array<char, 256> buffer{};
  const ImuRawSample &i = frame.imu;
  const int payloadLength = std::snprintf(buffer.data(), buffer.size(),
    "HAND,%lu,%lld,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
    static_cast<unsigned long>(frame.sequence), static_cast<long long>(frame.timestampUs),
    frame.flexRaw[0], frame.flexRaw[1], frame.flexRaw[2], frame.flexRaw[3], frame.flexRaw[4],
    i.accelX, i.accelY, i.accelZ, i.gyroX, i.gyroY, i.gyroZ, i.magX, i.magY, i.magZ);
  if (payloadLength <= 0 || static_cast<std::size_t>(payloadLength) + 7 >= buffer.size()) {
    return ESP_ERR_INVALID_SIZE;
  }
  // CRC chỉ phủ payload trước dấu '*'; bốn chữ số hex và newline kết thúc frame.
  const uint16_t crc = crc16Ccitt(buffer.data(), payloadLength);
  const int totalLength = payloadLength + std::snprintf(
    buffer.data() + payloadLength, buffer.size() - payloadLength, "*%04X\n", crc);
  return uart_write_bytes(hand::config::kUartPort, buffer.data(), totalLength) == totalLength
    ? ESP_OK : ESP_FAIL;
}
