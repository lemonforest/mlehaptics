# UTLP C64 HAL - cc65 Build System
#
# Prerequisites:
#   - cc65 toolchain installed (https://cc65.github.io/)
#   - VICE emulator for testing (https://vice-emu.sourceforge.io/)
#
# Usage:
#   make          - Build utlp_c64.prg
#   make run      - Build and run in VICE
#   make clean    - Remove build artifacts
#   make debug    - Build with debug symbols
#
# The magic: utlp_skeleton.c is copied UNCHANGED from the main project.
# If this builds, UTLP is truly Universal.

# cc65 toolchain
CC = cl65
AS = ca65
LD = ld65

# Target system
SYSTEM = c64

# Compiler flags
# -t c64:         Target Commodore 64
# -O:             Enable optimization
# -Oi:            Inline more functions
# -Or:            Enable register variables
# --standard cc65: Enable cc65 extensions (64-bit types)
CFLAGS = -t $(SYSTEM) -O -Oi -Or --standard cc65

# Debug flags (use: make CFLAGS="$(DEBUG_CFLAGS)")
DEBUG_CFLAGS = -t $(SYSTEM) -g --debug-info

# Source files
# NOTE: utlp_skeleton.c is copied from parent project - UNCHANGED!
SRCS = utlp_skeleton.c utlp_hal_c64.c utlp_main_c64.c

# Object files
OBJS = $(SRCS:.c=.o)

# Output program
TARGET = utlp_c64.prg

# VICE emulator (adjust path for your system)
VICE = x64sc

#============================================================================
# Build rules
#============================================================================

.PHONY: all clean run debug copy-skeleton

all: copy-skeleton $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

#============================================================================
# Copy and transform skeleton from main project
# THE MAGIC: C99→C89 automatic transformation
#============================================================================

copy-skeleton: utlp_skeleton.c utlp_hal.h

utlp_skeleton.c: ../utlp_skeleton/utlp_skeleton.c c89_transform.py
	@echo "Transforming utlp_skeleton.c (C99→C89)..."
	python3 c89_transform.py ../utlp_skeleton/utlp_skeleton.c utlp_skeleton.c
	@echo "If this builds, UTLP is truly Universal!"

utlp_hal.h: ../utlp_skeleton/utlp_hal.h c89_transform.py
	@echo "Transforming utlp_hal.h (C99→C89)..."
	python3 c89_transform.py ../utlp_skeleton/utlp_hal.h utlp_hal.h

#============================================================================
# Clean
#============================================================================

clean:
	rm -f $(OBJS) $(TARGET)
	rm -f utlp_skeleton.c utlp_hal.h  # Transformed files
	rm -f *.map *.lbl

#============================================================================
# Run in VICE emulator
#============================================================================

run: all
	@echo "Starting VICE with $(TARGET)..."
	@echo "Press STOP+RESTORE in VICE to exit"
	$(VICE) $(TARGET)

#============================================================================
# Debug build
#============================================================================

debug: CFLAGS = $(DEBUG_CFLAGS)
debug: clean all

#============================================================================
# Disk image for real hardware
#============================================================================

disk: all
	@echo "Creating D64 disk image..."
	c1541 -format "utlp,01" d64 utlp_c64.d64 -write $(TARGET) "utlp"
	@echo "Disk image created: utlp_c64.d64"
	@echo "Transfer to real C64 using SD2IEC, 1541 Ultimate, etc."

#============================================================================
# Info
#============================================================================

info:
	@echo "UTLP C64 HAL Build System"
	@echo "========================="
	@echo "Target:    $(TARGET)"
	@echo "Compiler:  $(CC)"
	@echo "Sources:   $(SRCS)"
	@echo ""
	@echo "Commands:"
	@echo "  make       - Build program"
	@echo "  make run   - Build and run in VICE"
	@echo "  make clean - Remove build files"
	@echo "  make disk  - Create D64 disk image"
	@echo "  make debug - Build with debug symbols"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - cc65 toolchain"
	@echo "  - VICE emulator (for 'make run')"
	@echo "  - c1541 (for 'make disk')"
