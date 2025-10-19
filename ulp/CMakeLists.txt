# ULP RISC-V CMake Configuration
# Compiles ULP C code for ESP32-C6 LP (Low Power) core

# Set ULP source file
set(ulp_sources "ulp_motor_control.c")

# Set ULP application name
set(ulp_app_name ulp_motor_control)

# Compile ULP binary
ulp_embed_binary(
    ${ulp_app_name}
    ${ulp_sources}
    "ulp_riscv"
)

# Make ULP binary available to main component
target_add_binary_data(${COMPONENT_TARGET} 
    "${CMAKE_CURRENT_BINARY_DIR}/${ulp_app_name}.bin" 
    BINARY
)
