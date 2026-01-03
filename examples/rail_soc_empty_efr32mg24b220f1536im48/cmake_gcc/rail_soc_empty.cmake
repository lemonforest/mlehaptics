####################################################################
# Automatically-generated file. Do not edit!                       #
####################################################################

set(SDK_PATH "C:/Users/sckir/.silabs/slt/installs/conan/p/simpleb526998f4a4d/p")
set(COPIED_SDK_PATH "simplicity_sdk_2025.6.2")
set(PKG_PATH "C:/Users/sckir/.silabs/slt/installs")

add_library(slc OBJECT
    "../${COPIED_SDK_PATH}/platform/common/src/sl_assert.c"
    "../${COPIED_SDK_PATH}/platform/common/src/sl_core_cortexm.c"
    "../${COPIED_SDK_PATH}/platform/common/src/sl_syscalls.c"
    "../${COPIED_SDK_PATH}/platform/Device/SiliconLabs/EFR32MG24/Source/startup_efr32mg24.c"
    "../${COPIED_SDK_PATH}/platform/Device/SiliconLabs/EFR32MG24/Source/system_efr32mg24.c"
    "../${COPIED_SDK_PATH}/platform/driver/gpio/src/sl_gpio.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_cmu.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_emu.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_gpio.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_ldma.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_msc.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_prs.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_system.c"
    "../${COPIED_SDK_PATH}/platform/emlib/src/em_timer.c"
    "../${COPIED_SDK_PATH}/platform/peripheral/src/sl_hal_gpio.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/pa-conversions/pa_conversions_efr32.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/pa-conversions/pa_curves_efr32.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ble_config_38M4Hz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ble_config_39MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ble_config_40MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ieee802154_config_38M4Hz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ieee802154_config_39MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_ieee802154_config_40MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_rfsense_ook_config_38M4Hz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_rfsense_ook_config_39MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24/sl_rail_rfsense_ook_config_40MHz.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/sl_rail_phy_overrides.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_protocol/sl_rail_util_protocol.c"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_sequencer/sl_rail_util_sequencer.c"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/src/sl_clock_manager.c"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/src/sl_clock_manager_hal_s2.c"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/src/sl_clock_manager_init.c"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/src/sl_clock_manager_init_hal_s2.c"
    "../${COPIED_SDK_PATH}/platform/service/device_init/src/sl_device_init_dcdc_s2.c"
    "../${COPIED_SDK_PATH}/platform/service/device_init/src/sl_device_init_emu_s2.c"
    "../${COPIED_SDK_PATH}/platform/service/device_manager/clocks/sl_device_clock_efr32xg24.c"
    "../${COPIED_SDK_PATH}/platform/service/device_manager/src/sl_device_clock.c"
    "../${COPIED_SDK_PATH}/platform/service/device_manager/src/sl_device_gpio.c"
    "../${COPIED_SDK_PATH}/platform/service/interrupt_manager/src/sl_interrupt_manager_cortexm.c"
    "../${COPIED_SDK_PATH}/platform/service/memory_manager/src/sl_memory_manager_region.c"
    "../${COPIED_SDK_PATH}/platform/service/mpu/src/sl_mpu_s2.c"
    "../${COPIED_SDK_PATH}/platform/service/sl_main/src/sl_main_init.c"
    "../${COPIED_SDK_PATH}/platform/service/sl_main/src/sl_main_init_memory.c"
    "../${COPIED_SDK_PATH}/platform/service/sl_main/src/sl_main_process_action.c"
    "../app_init.c"
    "../app_process.c"
    "../autogen/rail_config.c"
    "../autogen/sl_event_handler.c"
    "../autogen/sl_rail_util_callbacks.c"
    "../autogen/sl_rail_util_init.c"
    "../main.c"
)

target_include_directories(slc PUBLIC
   "../autogen"
   "../config"
   "../config/rail"
   "../."
    "../${COPIED_SDK_PATH}/platform/Device/SiliconLabs/EFR32MG24/Include"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/inc"
    "../${COPIED_SDK_PATH}/platform/service/clock_manager/src"
    "../${COPIED_SDK_PATH}/platform/CMSIS/Core/Include"
    "../${COPIED_SDK_PATH}/platform/common/inc"
    "../${COPIED_SDK_PATH}/platform/service/device_manager/inc"
    "../${COPIED_SDK_PATH}/platform/service/device_init/inc"
    "../${COPIED_SDK_PATH}/platform/emlib/inc"
    "../${COPIED_SDK_PATH}/platform/driver/gpio/inc"
    "../${COPIED_SDK_PATH}/platform/peripheral/inc"
    "../${COPIED_SDK_PATH}/platform/service/interrupt_manager/inc"
    "../${COPIED_SDK_PATH}/platform/service/interrupt_manager/src"
    "../${COPIED_SDK_PATH}/platform/service/interrupt_manager/inc/arm"
    "../${COPIED_SDK_PATH}/platform/service/memory_manager/inc"
    "../${COPIED_SDK_PATH}/platform/service/mpu/inc"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/common"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/protocol/ble"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/protocol/ieee802154"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/protocol/wmbus"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/protocol/zwave"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/chip/efr32/efr32xg2x"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/protocol/sidewalk"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_built_in_phys/efr32xg24"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_callbacks"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/pa-conversions"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/pa-conversions/efr32xg24"
    "../${COPIED_SDK_PATH}/platform/radio/rail_lib/plugin/rail_util_protocol"
    "../${COPIED_SDK_PATH}/platform/service/sl_main/inc"
    "../${COPIED_SDK_PATH}/platform/service/sl_main/src"
)

target_compile_definitions(slc PUBLIC
    "EFR32MG24B220F1536IM48=1"
    "SL_CODE_COMPONENT_SYSTEM=system"
    "SL_CLOCK_MANAGER_AUTO_BAND_VALID=1"
    "SL_CODE_COMPONENT_CLOCK_MANAGER=clock_manager"
    "SL_COMPONENT_CATALOG_PRESENT=1"
    "SL_CODE_COMPONENT_GPIO=gpio"
    "SL_CODE_COMPONENT_HAL_COMMON=hal_common"
    "SL_CODE_COMPONENT_HAL_GPIO=hal_gpio"
    "SL_CODE_COMPONENT_INTERRUPT_MANAGER=interrupt_manager"
    "CMSIS_NVIC_VIRTUAL=1"
    "CMSIS_NVIC_VIRTUAL_HEADER_FILE=\"cmsis_nvic_virtual.h\""
    "SL_RAIL_LIB_MULTIPROTOCOL_SUPPORT=0"
    "SL_RAIL_UTIL_PA_CONFIG_HEADER=<sl_rail_util_pa_config.h>"
    "SL_CODE_COMPONENT_CORE=core"
    "SL_RAIL_3_API=1"
)

target_link_libraries(slc PUBLIC
    "-Wl,--start-group"
    "gcc"
    "c"
    "m"
    "nosys"
   "${CMAKE_CURRENT_LIST_DIR}/../${COPIED_SDK_PATH}/platform/radio/rail_lib/autogen/librail_release/librail_efr32xg24_gcc_release.a"
    "-Wl,--end-group"
)
target_compile_options(slc PUBLIC
    $<$<COMPILE_LANGUAGE:C>:-mcpu=cortex-m33>
    $<$<COMPILE_LANGUAGE:C>:-mthumb>
    $<$<COMPILE_LANGUAGE:C>:-mfpu=fpv5-sp-d16>
    $<$<COMPILE_LANGUAGE:C>:-mfloat-abi=hard>
    $<$<COMPILE_LANGUAGE:C>:-mcmse>
    $<$<COMPILE_LANGUAGE:C>:-Wall>
    $<$<COMPILE_LANGUAGE:C>:-Wextra>
    $<$<COMPILE_LANGUAGE:C>:-Og>
    $<$<COMPILE_LANGUAGE:C>:-fdata-sections>
    $<$<COMPILE_LANGUAGE:C>:-ffunction-sections>
    $<$<COMPILE_LANGUAGE:C>:-fomit-frame-pointer>
    $<$<COMPILE_LANGUAGE:C>:-g>
    $<$<COMPILE_LANGUAGE:C>:-fno-lto>
    $<$<COMPILE_LANGUAGE:C>:--specs=nano.specs>
    $<$<COMPILE_LANGUAGE:CXX>:-mcpu=cortex-m33>
    $<$<COMPILE_LANGUAGE:CXX>:-mthumb>
    $<$<COMPILE_LANGUAGE:CXX>:-mfpu=fpv5-sp-d16>
    $<$<COMPILE_LANGUAGE:CXX>:-mfloat-abi=hard>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions>
    $<$<COMPILE_LANGUAGE:CXX>:-mcmse>
    $<$<COMPILE_LANGUAGE:CXX>:-Wall>
    $<$<COMPILE_LANGUAGE:CXX>:-Wextra>
    $<$<COMPILE_LANGUAGE:CXX>:-Og>
    $<$<COMPILE_LANGUAGE:CXX>:-fdata-sections>
    $<$<COMPILE_LANGUAGE:CXX>:-ffunction-sections>
    $<$<COMPILE_LANGUAGE:CXX>:-fomit-frame-pointer>
    $<$<COMPILE_LANGUAGE:CXX>:-g>
    $<$<COMPILE_LANGUAGE:CXX>:-fno-lto>
    $<$<COMPILE_LANGUAGE:CXX>:--specs=nano.specs>
    $<$<COMPILE_LANGUAGE:ASM>:-mcpu=cortex-m33>
    $<$<COMPILE_LANGUAGE:ASM>:-mthumb>
    $<$<COMPILE_LANGUAGE:ASM>:-mfpu=fpv5-sp-d16>
    $<$<COMPILE_LANGUAGE:ASM>:-mfloat-abi=hard>
    "$<$<COMPILE_LANGUAGE:ASM>:SHELL:-x assembler-with-cpp>"
)

set(post_build_command )
set_property(TARGET slc PROPERTY C_STANDARD 17)
set_property(TARGET slc PROPERTY CXX_STANDARD 17)
set_property(TARGET slc PROPERTY CXX_EXTENSIONS OFF)

target_link_options(slc INTERFACE
    -mcpu=cortex-m33
    -mthumb
    -mfpu=fpv5-sp-d16
    -mfloat-abi=hard
    -T${CMAKE_CURRENT_LIST_DIR}/../autogen/linkerfile.ld
    --specs=nano.specs
    "SHELL:-Xlinker -Map=$<TARGET_FILE_DIR:rail_soc_empty>/rail_soc_empty.map"
    -fno-lto
    -Wl,--gc-sections
)

# BEGIN_SIMPLICITY_STUDIO_METADATA=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=END_SIMPLICITY_STUDIO_METADATA