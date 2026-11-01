#include "bno055.hpp"

#include <array>

#include "driver/uart.h"
#include "esp_check.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "hardware_config.hpp"

namespace {
constexpr uint8_t kChipIdRegister = 0x00;
constexpr uint8_t kExpectedChipId = 0xA0;
constexpr uint8_t kAccelDataRegister = 0x08;
constexpr uint8_t kOperationModeRegister = 0x3D;
constexpr uint8_t kPowerModeRegister = 0x3E;
constexpr uint8_t kPageRegister = 0x07;
constexpr uint8_t kConfigMode = 0x00;
constexpr uint8_t kAmgMode = 0x07;
constexpr uint8_t kCommandStart = 0xAA;
constexpr uint8_t kReadCommand = 0x01;
constexpr uint8_t kWriteCommand = 0x00;
constexpr uint8_t kReadResponse = 0xBB;
constexpr uint8_t kWriteResponse = 0xEE;
constexpr uint8_t kWriteSuccess = 0x01;
constexpr TickType_t kUartTimeout = pdMS_TO_TICKS(150);

int16_t readInt16(const uint8_t *bytes)
{
  // BNO055 truyền số signed 16-bit theo thứ tự little-endian.
  return static_cast<int16_t>(
    static_cast<uint16_t>(bytes[0]) |
    (static_cast<uint16_t>(bytes[1]) << 8));
}

esp_err_t readExact(uint8_t *data, std::size_t length)
{
  std::size_t received = 0;
  while (received < length) {
    const int count = uart_read_bytes(
      hand::config::kBnoUartPort, data + received, length - received, kUartTimeout);
    if (count <= 0) {
      return ESP_ERR_TIMEOUT;
    }
    received += static_cast<std::size_t>(count);
  }
  return ESP_OK;
}
}  // namespace

esp_err_t Bno055::init()
{
  const uart_config_t uartConfig = {
    .baud_rate = hand::config::kBnoUartBaudRate,
    .data_bits = UART_DATA_8_BITS,
    .parity = UART_PARITY_DISABLE,
    .stop_bits = UART_STOP_BITS_1,
    .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    .rx_flow_ctrl_thresh = 0,
    .rx_glitch_filt_thresh = 0,
    .source_clk = UART_SCLK_DEFAULT,
    .flags = {},
  };
  ESP_RETURN_ON_ERROR(
    uart_param_config(hand::config::kBnoUartPort, &uartConfig), "bno055", "UART config failed");
  ESP_RETURN_ON_ERROR(
    uart_set_pin(hand::config::kBnoUartPort,
      hand::config::kBnoUartTxPin,
      hand::config::kBnoUartRxPin,
      UART_PIN_NO_CHANGE,
      UART_PIN_NO_CHANGE),
    "bno055", "UART pin config failed");
  ESP_RETURN_ON_ERROR(
    uart_driver_install(hand::config::kBnoUartPort, 512, 0, 0, nullptr, 0),
    "bno055", "UART driver install failed");

  // Cảm biến cần hoàn tất boot trước khi nhận gói lệnh UART đầu tiên.
  vTaskDelay(pdMS_TO_TICKS(700));
  uint8_t chipId = 0;
  ESP_RETURN_ON_ERROR(readRegisters(kChipIdRegister, &chipId, 1), "bno055", "UART chip ID read failed");
  if (chipId != kExpectedChipId) {
    return ESP_ERR_INVALID_RESPONSE;
  }

  // UART dùng cùng register map với I2C nên trình tự cấu hình mode không đổi.
  ESP_RETURN_ON_ERROR(writeRegister(kOperationModeRegister, kConfigMode), "bno055", "config mode failed");
  vTaskDelay(pdMS_TO_TICKS(25));
  ESP_RETURN_ON_ERROR(writeRegister(kPageRegister, 0), "bno055", "page select failed");
  ESP_RETURN_ON_ERROR(writeRegister(kPowerModeRegister, 0), "bno055", "power mode failed");
  ESP_RETURN_ON_ERROR(writeRegister(kOperationModeRegister, kAmgMode), "bno055", "AMG mode failed");
  vTaskDelay(pdMS_TO_TICKS(20));
  return ESP_OK;
}

esp_err_t Bno055::read(ImuRawSample &sample)
{
  // Burst-read 18 byte tránh lệch thời điểm giữa ba loại cảm biến.
  std::array<uint8_t, 18> bytes{};
  ESP_RETURN_ON_ERROR(
    readRegisters(kAccelDataRegister, bytes.data(), bytes.size()), "bno055", "sensor read failed");

  // Thanh ghi BNO055 xếp accel, mag, gyro; struct/protocol xếp accel, gyro, mag.
  sample = {
    .accelX = readInt16(&bytes[0]), .accelY = readInt16(&bytes[2]), .accelZ = readInt16(&bytes[4]),
    .gyroX = readInt16(&bytes[12]), .gyroY = readInt16(&bytes[14]), .gyroZ = readInt16(&bytes[16]),
    .magX = readInt16(&bytes[6]), .magY = readInt16(&bytes[8]), .magZ = readInt16(&bytes[10]),
  };
  return ESP_OK;
}

esp_err_t Bno055::readRegisters(uint8_t address, uint8_t *data, std::size_t length)
{
  if (length == 0 || length > 128) {
    return ESP_ERR_INVALID_SIZE;
  }
  const uint8_t command[] = {kCommandStart, kReadCommand, address, static_cast<uint8_t>(length)};
  uart_flush_input(hand::config::kBnoUartPort);
  if (uart_write_bytes(hand::config::kBnoUartPort, command, sizeof(command)) != sizeof(command)) {
    return ESP_FAIL;
  }
  ESP_RETURN_ON_ERROR(
    uart_wait_tx_done(hand::config::kBnoUartPort, kUartTimeout), "bno055", "UART TX timeout");

  uint8_t header[2]{};
  ESP_RETURN_ON_ERROR(readExact(header, sizeof(header)), "bno055", "UART response timeout");
  if (header[0] != kReadResponse || header[1] != length) {
    return ESP_ERR_INVALID_RESPONSE;
  }
  return readExact(data, length);
}

esp_err_t Bno055::writeRegister(uint8_t address, uint8_t value)
{
  const uint8_t command[] = {kCommandStart, kWriteCommand, address, 1, value};
  uart_flush_input(hand::config::kBnoUartPort);
  if (uart_write_bytes(hand::config::kBnoUartPort, command, sizeof(command)) != sizeof(command)) {
    return ESP_FAIL;
  }
  ESP_RETURN_ON_ERROR(
    uart_wait_tx_done(hand::config::kBnoUartPort, kUartTimeout), "bno055", "UART TX timeout");

  uint8_t response[2]{};
  ESP_RETURN_ON_ERROR(readExact(response, sizeof(response)), "bno055", "UART write response timeout");
  return response[0] == kWriteResponse && response[1] == kWriteSuccess
    ? ESP_OK : ESP_ERR_INVALID_RESPONSE;
}
