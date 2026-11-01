#pragma once

#include <array>
#include <cstdint>

#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_adc/adc_oneshot.h"

namespace hand::config {

// Chu kỳ lấy mẫu và cấu hình đường truyền chung giữa acquisition và UART.
inline constexpr uart_port_t kUartPort = UART_NUM_0;
inline constexpr int kBaudRate = 115200;
inline constexpr int kSampleRateHz = 50;
inline constexpr int kSamplePeriodMs = 1000 / kSampleRateHz;
// 16 lượt cách nhau 1,25 ms phủ đều một frame 20 ms của năm kênh flex.
inline constexpr int kFlexSamplesPerFrame = 16;
inline constexpr int64_t kFlexSampleIntervalUs =
  1'000'000 / (kSampleRateHz * kFlexSamplesPerFrame);
static_assert(1'000'000 % (kSampleRateHz * kFlexSamplesPerFrame) == 0);

// Bus I2C nối BNO055; địa chỉ 0x28 ứng với chân ADR ở mức thấp.
inline constexpr int kI2cPort = 0;
inline constexpr gpio_num_t kI2cSdaPin = GPIO_NUM_21;
inline constexpr gpio_num_t kI2cSclPin = GPIO_NUM_22;
// 100 kHz ổn định hơn với dây jumper dài khi thử trên breadboard.
inline constexpr uint32_t kI2cFrequencyHz = 100000;
inline constexpr uint8_t kBno055PrimaryAddress = 0x28;
inline constexpr uint8_t kBno055SecondaryAddress = 0x29;

// UART2 dành riêng cho BNO055; UART0 vẫn gửi frame qua cổng USB của ESP32.
inline constexpr uart_port_t kBnoUartPort = UART_NUM_2;
inline constexpr gpio_num_t kBnoUartRxPin = GPIO_NUM_16;
inline constexpr gpio_num_t kBnoUartTxPin = GPIO_NUM_17;
inline constexpr int kBnoUartBaudRate = 115200;

// Thứ tự: ngón cái, trỏ, giữa, áp út, út. VP là nhãn trên board của GPIO36.
// Cả năm chân thuộc ADC1 nên vẫn đọc được khi Wi-Fi đang hoạt động.
inline constexpr std::array<adc_channel_t, 5> kFlexChannels = {
  ADC_CHANNEL_0,  // VP / GPIO36 / ADC1_CH0
  ADC_CHANNEL_5,  // GPIO33 / ADC1_CH5
  ADC_CHANNEL_4,  // GPIO32 / ADC1_CH4
  ADC_CHANNEL_7,  // GPIO35 / ADC1_CH7
  ADC_CHANNEL_6,  // GPIO34 / ADC1_CH6
};

}  // namespace hand::config
