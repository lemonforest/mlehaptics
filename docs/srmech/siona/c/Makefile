# Makefile — build Siona's native plugin libsiona_native.so into the package's
# _native/ dir (so hatchling force-include ships it as package data, and srmech's
# profile_loader locates it via importlib.metadata.files("siona")).
#
# Pedantic by default (mirrors srmech's -Werror C discipline). A release builds
# platform wheels via cibuildwheel; this Makefile is the local/dev build + the
# JPL-clean smoke.

CC      ?= cc
CFLAGS  ?= -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic
LDFLAGS ?= -shared

PKG_NATIVE := ../siona/_native
LIB        := $(PKG_NATIVE)/libsiona_native.so
SRC        := siona_native.c
HDR        := siona_native.h

.PHONY: all clean
all: $(LIB)

$(LIB): $(SRC) $(HDR)
	@mkdir -p $(PKG_NATIVE)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(SRC)
	@echo "built $@"

clean:
	rm -f $(LIB)
