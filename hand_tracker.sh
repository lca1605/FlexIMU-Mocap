#!/usr/bin/env bash
set -euo pipefail

projectDir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
firmwareDir="${projectDir}/esp32_firmware"
defaultPort="/dev/ttyUSB0"

# In toàn bộ lệnh công khai để file này là điểm bắt đầu duy nhất trên Linux.
showHelp() {
  cat <<'EOF'
ESP32 Right Hand Tracker - lệnh dùng trên Linux

  ./hand_tracker.sh setup               Tạo .venv và cài thư viện Python
  ./hand_tracker.sh run [PORT]          Mở mô hình tay 3D
  ./hand_tracker.sh imu-test [PORT]     Test BNO055 bằng máy bay 3D trên web
  ./hand_tracker.sh imu-demo            Xem thử máy bay 3D không cần phần cứng
  ./hand_tracker.sh build               Build firmware ESP32
  ./hand_tracker.sh flash [PORT]        Nạp firmware vào ESP32
  ./hand_tracker.sh blink-build         Build firmware blink LED tại D12
  ./hand_tracker.sh blink-flash [PORT]  Nạp firmware blink LED tại D12
  ./hand_tracker.sh i2c-scan-build      Build firmware scanner I2C
  ./hand_tracker.sh i2c-scan [PORT]     Nạp scanner rồi hiển thị địa chỉ I2C
  ./hand_tracker.sh monitor [PORT]      Xem log UART bằng ESP-IDF
  ./hand_tracker.sh flash-monitor [PORT] Nạp firmware rồi xem log
  ./hand_tracker.sh test                Chạy toàn bộ pytest phía PC

PORT mặc định là /dev/ttyUSB0.
Có thể đặt ESP_IDF_EXPORT=/đường/dẫn/export.sh nếu ESP-IDF nằm ở nơi khác.
EOF
}

loadIdf() {
  # Ưu tiên đường dẫn do người dùng đặt, sau đó mới thử các vị trí quen thuộc.
  local exportScript="${ESP_IDF_EXPORT:-}"
  if [[ -z "${exportScript}" && -n "${IDF_PATH:-}" ]]; then
    exportScript="${IDF_PATH}/export.sh"
  fi
  if [[ -z "${exportScript}" ]]; then
    for candidate in \
      "/home/lecongcomputer/ARM_Car/.tools/esp-idf/export.sh" \
      "${HOME}/esp/esp-idf/export.sh"; do
      if [[ -f "${candidate}" ]]; then
        exportScript="${candidate}"
        break
      fi
    done
  fi
  if [[ -z "${exportScript}" || ! -f "${exportScript}" ]]; then
    echo "Không tìm thấy ESP-IDF export.sh." >&2
    echo "Hãy đặt: ESP_IDF_EXPORT=/đường/dẫn/esp-idf/export.sh" >&2
    exit 1
  fi
  local bundledToolsDir
  bundledToolsDir="$(dirname -- "$(dirname -- "${exportScript}")")/espressif"
  # Bản ESP-IDF portable giữ compiler và Python env cạnh source trong .tools.
  if [[ -z "${IDF_TOOLS_PATH:-}" && -d "${bundledToolsDir}" ]]; then
    export IDF_TOOLS_PATH="${bundledToolsDir}"
  fi
  # ESP-IDF thiết lập PATH và biến môi trường cho idf.py trong shell hiện tại.
  source "${exportScript}" >/dev/null
}

pythonCommand() {
  # Dùng virtualenv của project nếu đã setup, nếu không dùng Python hệ thống.
  if [[ -x "${projectDir}/.venv/bin/python" ]]; then
    printf '%s\n' "${projectDir}/.venv/bin/python"
  else
    printf '%s\n' "python3"
  fi
}

commandName="${1:-help}"
# Mỗi nhánh chỉ điều phối công cụ; build/flash luôn chạy từ thư mục firmware.
case "${commandName}" in
  setup)
    python3 -m venv "${projectDir}/.venv"
    "${projectDir}/.venv/bin/python" -m pip install --upgrade pip
    "${projectDir}/.venv/bin/python" -m pip install -r "${projectDir}/pc_app/requirements.txt"
    ;;
  run)
    port="${2:-${defaultPort}}"
    "$(pythonCommand)" "${projectDir}/pc_app/main.py" --port "${port}"
    ;;
  imu-test)
    port="${2:-${defaultPort}}"
    "$(pythonCommand)" "${projectDir}/pc_app/imu_web.py" --port "${port}"
    ;;
  imu-demo)
    "$(pythonCommand)" "${projectDir}/pc_app/imu_web.py" --demo
    ;;
  build)
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=OFF -DHAND_TRACKER_I2C_SCANNER=OFF build)
    ;;
  flash)
    port="${2:-${defaultPort}}"
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=OFF -DHAND_TRACKER_I2C_SCANNER=OFF -p "${port}" flash)
    ;;
  blink-build)
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=ON -DHAND_TRACKER_I2C_SCANNER=OFF build)
    ;;
  blink-flash)
    port="${2:-${defaultPort}}"
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=ON -DHAND_TRACKER_I2C_SCANNER=OFF -p "${port}" flash)
    ;;
  i2c-scan-build)
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=OFF -DHAND_TRACKER_I2C_SCANNER=ON build)
    ;;
  i2c-scan)
    port="${2:-${defaultPort}}"
    loadIdf
    (cd "${firmwareDir}" && idf.py -DHAND_TRACKER_BLINK_TEST=OFF -DHAND_TRACKER_I2C_SCANNER=ON -p "${port}" flash monitor)
    ;;
  monitor)
    port="${2:-${defaultPort}}"
    loadIdf
    (cd "${firmwareDir}" && idf.py -p "${port}" monitor)
    ;;
  flash-monitor)
    port="${2:-${defaultPort}}"
    loadIdf
    (cd "${firmwareDir}" && idf.py -p "${port}" flash monitor)
    ;;
  test)
    cd "${projectDir}"
    "$(pythonCommand)" -m pytest
    ;;
  help|-h|--help)
    showHelp
    ;;
  *)
    echo "Lệnh không hợp lệ: ${commandName}" >&2
    showHelp >&2
    exit 2
    ;;
esac
