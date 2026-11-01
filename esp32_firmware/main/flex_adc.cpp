#include "flex_adc.hpp"

#include <array>
#include <cstdint>

#include "esp_adc/adc_oneshot.h"
#include "esp_check.h"
#include "esp_timer.h"
#include "hardware_config.hpp"

esp_err_t FlexAdc::init()
{
  // D32–D35 và VP đều thuộc ADC1 nên không tranh chấp với Wi-Fi.
  adc_oneshot_unit_handle_t handle = nullptr;
  const adc_oneshot_unit_init_cfg_t unitConfig = {
    .unit_id = ADC_UNIT_1,
    .clk_src = ADC_RTC_CLK_SRC_DEFAULT,
    .ulp_mode = ADC_ULP_MODE_DISABLE,
  };
  ESP_RETURN_ON_ERROR(
    adc_oneshot_new_unit(&unitConfig, &handle), "flex_adc", "ADC1 init failed");

  // Attenuation 12 dB cho phép đo gần toàn dải 3,3 V của cầu phân áp.
  const adc_oneshot_chan_cfg_t channelConfig = {
    .atten = ADC_ATTEN_DB_12,
    .bitwidth = ADC_BITWIDTH_12,
  };
  for (const adc_channel_t channel : hand::config::kFlexChannels) {
    ESP_RETURN_ON_ERROR(
      adc_oneshot_config_channel(handle, channel, &channelConfig),
      "flex_adc",
      "ADC channel config failed");
  }
  handle_ = handle;

  // Queue một phần tử luôn giữ bộ trung bình mới nhất nếu phía gửi bị chậm.
  resultQueue_ = xQueueCreate(1, sizeof(std::array<int, 5>));
  if (resultQueue_ == nullptr) {
    return ESP_ERR_NO_MEM;
  }
  const esp_timer_create_args_t timerConfig = {
    .callback = &FlexAdc::sampleTimerCallback,
    .arg = this,
    .dispatch_method = ESP_TIMER_TASK,
    .name = "flex_adc",
    .skip_unhandled_events = true,
  };
  ESP_RETURN_ON_ERROR(
    esp_timer_create(&timerConfig, &sampleTimer_), "flex_adc", "sample timer init failed");
  return esp_timer_start_periodic(sampleTimer_, hand::config::kFlexSampleIntervalUs);
}

esp_err_t FlexAdc::read(std::array<int, 5> &rawValues)
{
  // Timer phát một kết quả mỗi 20 ms; timeout dài hơn một chu kỳ để phát hiện lỗi.
  return xQueueReceive(
    resultQueue_, &rawValues, pdMS_TO_TICKS(hand::config::kSamplePeriodMs * 2)) == pdTRUE
    ? ESP_OK : ESP_ERR_TIMEOUT;
}

void FlexAdc::sampleTimerCallback(void *context)
{
  static_cast<FlexAdc *>(context)->sampleOnce();
}

void FlexAdc::sampleOnce()
{
  const auto handle = static_cast<adc_oneshot_unit_handle_t>(handle_);
  std::array<int, 5> sampleValues{};

  // Năm phép đọc liên tiếp tạo một lượt; timer giữ các lượt cách nhau 1.250 us.
  for (std::size_t index = 0; index < sampleValues.size(); ++index) {
    if (adc_oneshot_read(
          handle, hand::config::kFlexChannels[index], &sampleValues[index]) != ESP_OK) {
      return;
    }
  }
  for (std::size_t index = 0; index < sums_.size(); ++index) {
    sums_[index] += static_cast<uint32_t>(sampleValues[index]);
  }
  ++sampleCount_;
  if (sampleCount_ < hand::config::kFlexSamplesPerFrame) {
    return;
  }

  std::array<int, 5> averagedValues{};
  for (std::size_t index = 0; index < averagedValues.size(); ++index) {
    // Cộng nửa mẫu số trước phép chia nguyên để làm tròn tới mã ADC gần nhất.
    averagedValues[index] = static_cast<int>(
      (sums_[index] + hand::config::kFlexSamplesPerFrame / 2)
      / hand::config::kFlexSamplesPerFrame);
  }
  sums_.fill(0);
  sampleCount_ = 0;
  xQueueOverwrite(resultQueue_, &averagedValues);
}
