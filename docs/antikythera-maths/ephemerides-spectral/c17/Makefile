# ephemerides-spectral C17 BIP encoder — Makefile
#
# Targets:
#   all      build the static library + smoke-test binary
#   lib      build only libephemerides_spectral.a
#   test     build + run the smoke test
#   parity   build + run the cross-language parity test (Python required)
#   codegen  re-emit es_bodies.c / es_laplacian.c / es_cosine_lut.c
#            from the Python research modules
#   clean    delete build/

CC      ?= cc
STD     ?= c17
CFLAGS  ?= -std=$(STD) -Wall -Wextra -Wpedantic -O2 -fPIC
LDFLAGS ?= -lm

BUILD   := build
SRCDIR  := src
INCDIR  := include
TESTDIR := test

# Source files (codegen-emitted + hand-written).
SRCS := $(wildcard $(SRCDIR)/*.c)
OBJS := $(patsubst $(SRCDIR)/%.c,$(BUILD)/%.o,$(SRCS))

LIB     := $(BUILD)/libephemerides_spectral.a
TESTBIN := $(BUILD)/test_es_encode

.PHONY: all lib test parity codegen clean

all: lib test

lib: $(LIB)

$(LIB): $(OBJS)
	@mkdir -p $(BUILD)
	$(AR) rcs $@ $^

$(BUILD)/%.o: $(SRCDIR)/%.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(INCDIR) -c $< -o $@

$(BUILD):
	@mkdir -p $@

test: $(TESTBIN)
	./$(TESTBIN)

$(TESTBIN): $(LIB) $(TESTDIR)/test_es_encode.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(INCDIR) $(TESTDIR)/test_es_encode.c $(LIB) $(LDFLAGS) -o $@

parity: $(TESTBIN)
	python $(TESTDIR)/test_parity_python.py

codegen:
	cd codegen && python emit_c_tables.py

clean:
	rm -rf $(BUILD)
