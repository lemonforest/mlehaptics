# srmech C library — Makefile
#
# Mirrors docs/antikythera-maths/ephemerides-spectral/c/Makefile.
# Same flags, same layout, same parity discipline so the monorepo's
# two C trees share one mental model.
#
# Targets:
#   all      build the static library + smoke test binary
#   lib      build only libsrmech.a
#   test     build + run the C smoke tests
#   parity   build + run the cross-language parity test (needs Python)
#   clean    delete build/
#
# Phase B1 (current): all source files are placeholder .gitkeeps.
# `make` succeeds vacuously (no .c files → no .o files → no .a file
# is produced; the test/parity targets noop). The Makefile becomes
# load-bearing at Phase B3 when the first .c file lands.

CC      ?= cc
STD     ?= c17
CFLAGS  ?= -std=$(STD) -Wall -Wextra -Wpedantic -O2 -fPIC
LDFLAGS ?=

BUILD   := build
SRCDIR  := src
INCDIR  := include
TESTDIR := test

SRCS := $(filter-out $(SRCDIR)/.gitkeep,$(wildcard $(SRCDIR)/*.c))
OBJS := $(patsubst $(SRCDIR)/%.c,$(BUILD)/%.o,$(SRCS))

LIB     := $(BUILD)/libsrmech.a
TESTBIN := $(BUILD)/test_srmech

.PHONY: all lib test parity clean

all: lib test

lib: $(LIB)

$(LIB): $(OBJS) | $(BUILD)
	@if [ -z "$(OBJS)" ]; then \
		echo "(Phase B1: no .c files yet — skipping ar)"; \
	else \
		$(AR) rcs $@ $^; \
	fi

$(BUILD)/%.o: $(SRCDIR)/%.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(INCDIR) -c $< -o $@

$(BUILD):
	@mkdir -p $@

test: $(LIB)
	@if [ -f $(TESTDIR)/test_srmech.c ]; then \
		$(CC) $(CFLAGS) -I$(INCDIR) $(TESTDIR)/test_srmech.c $(LIB) $(LDFLAGS) -o $(TESTBIN); \
		./$(TESTBIN); \
	else \
		echo "(Phase B1: no test_srmech.c yet — skipping)"; \
	fi

parity: test
	@if [ -f $(TESTDIR)/test_parity_python.py ]; then \
		python $(TESTDIR)/test_parity_python.py; \
	else \
		echo "(Phase B1: no test_parity_python.py yet — skipping)"; \
	fi

clean:
	rm -rf $(BUILD)
