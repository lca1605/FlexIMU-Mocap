# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/lecongcomputer/ARM_Car/.tools/esp-idf/components/bootloader/subproject"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/tmp"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/src/bootloader-stamp"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/src"
  "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/lecongcomputer/esp32_right_hand_tracker/esp32_firmware/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
