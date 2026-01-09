# Define minimal required version of CMake.
cmake_minimum_required(VERSION "3.25")

# Project definition
project(
	rail_soc_empty
	VERSION 1.0
	LANGUAGES C CXX ASM
)

# Include the definition of the slc_rail_soc_empty target,
# which contains the content of the SLC project
include(rail_soc_empty.cmake)

add_executable(rail_soc_empty
    # Add additional sources here
)

target_include_directories(rail_soc_empty PUBLIC
    # Add additional include paths here
)

target_compile_definitions(rail_soc_empty PUBLIC
    # Add additional macros here
)

target_compile_options(rail_soc_empty PUBLIC
    # Set additional compiler flags here
)

target_link_options(rail_soc_empty PUBLIC
    # Set additional linker flags here
)

# Link with the content defined in the SLC project
target_link_libraries(rail_soc_empty PRIVATE
    slc
)

# Include managed project content if available
include(rail_soc_empty_project.cmake OPTIONAL RESULT_VARIABLE managed_project)
if(managed_project)
    message(STATUS "Using managed project content from ${managed_project}")
endif()

# Force the gcc linker command
set_target_properties(rail_soc_empty PROPERTIES LINKER_LANGUAGE C)

# Create .bin, .hex and .s37 artifacts after building the project
add_custom_command(TARGET rail_soc_empty
    POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} ${OBJCOPY_SREC_CMD} "$<TARGET_FILE:rail_soc_empty>" "$<TARGET_FILE_DIR:rail_soc_empty>/$<TARGET_FILE_BASE_NAME:rail_soc_empty>.s37"
    COMMAND ${CMAKE_OBJCOPY} ${OBJCOPY_IHEX_CMD} "$<TARGET_FILE:rail_soc_empty>" "$<TARGET_FILE_DIR:rail_soc_empty>/$<TARGET_FILE_BASE_NAME:rail_soc_empty>.hex"
    COMMAND ${CMAKE_OBJCOPY} ${OBJCOPY_BIN_CMD}  "$<TARGET_FILE:rail_soc_empty>" "$<TARGET_FILE_DIR:rail_soc_empty>/$<TARGET_FILE_BASE_NAME:rail_soc_empty>.bin" 
)

# Run post-build pipeline to perform additional post-processing
if(post_build_command)
add_custom_command(TARGET rail_soc_empty
    POST_BUILD
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/..
    COMMAND ${post_build_command}
)
endif()