if(HAND_TRACKER_I2C_SCANNER)
  set(appSources "i2c_scanner.cpp")
elseif(HAND_TRACKER_BLINK_TEST)
  set(appSources "blink_led.cpp")
else()
  set(appSources
    "main.cpp"
    "bno055.cpp"
    "flex_adc.cpp"
    "uart_transport.cpp")
endif()

idf_component_register(
  SRCS ${appSources}
  INCLUDE_DIRS "."
  REQUIRES
    driver
    esp_adc
    esp_driver_gpio
    esp_driver_i2c
    esp_driver_uart
    esp_timer
)
