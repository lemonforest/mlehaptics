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

# rc356 (`#T953`): build + run EVERY c/test/test_srmech_*.c.
#
# This target used to look for `test/test_srmech.c`, a file that has never
# existed in this tree, and print "(Phase B1: no test_srmech.c yet — skipping)"
# before exiting 0. c/README.md documents `make test` as THE local flow, so the
# documented developer path was itself a false green — for all 30 tests, on
# every run, for as long as the file has had this shape. Between that and CI
# (which had no run step at all until rc356), NOTHING executed a C test.
#
# -I$(SRCDIR) because test_srmech_config.c and test_srmech_text_fold.c include
# private headers (srmech_platform.h / srmech_unicode_fold_tables.h). -lm for
# the GNU/Linux math runtime; harmless elsewhere.
#
# Each binary runs with $(BUILD) as its cwd — several tests write scratch files
# (rcut_graph.bin, rcut_w1/ …) relative to it, and running them from c/ drops
# that litter straight into the source tree. build/ is already gitignored, which
# is the whole reason it is the right cwd. ctest does this by default.
TESTS    := $(wildcard $(TESTDIR)/test_srmech_*.c)
TESTBINS := $(patsubst $(TESTDIR)/%.c,$(BUILD)/%,$(TESTS))
TESTLIBS := -lm

$(BUILD)/test_srmech_%: $(TESTDIR)/test_srmech_%.c $(LIB) | $(BUILD)
	$(CC) $(CFLAGS) -I$(INCDIR) -I$(SRCDIR) $< $(LIB) $(LDFLAGS) $(TESTLIBS) -o $@

test: $(TESTBINS)
	@if [ -z "$(TESTBINS)" ]; then \
		echo "no c/test/test_srmech_*.c found — that is a DEFECT, not a skip"; \
		exit 1; \
	fi
	@pass=0; fail=0; \
	for t in $(TESTBINS); do \
		if out=$$(cd $(BUILD) && "./$$(basename $$t)" 2>&1); then \
			pass=$$((pass+1)); printf '  PASS  %s\n' "$$(basename $$t)"; \
		else \
			fail=$$((fail+1)); printf '  FAIL  %s\n' "$$(basename $$t)"; \
			printf '%s\n' "$$out" | tail -20; \
		fi; \
	done; \
	echo "== C tests: $$pass passed, $$fail failed =="; \
	[ $$fail -eq 0 ]

parity: test
	@if [ -f $(TESTDIR)/test_parity_python.py ]; then \
		python $(TESTDIR)/test_parity_python.py; \
	else \
		echo "(Phase B1: no test_parity_python.py yet — skipping)"; \
	fi

clean:
	rm -rf $(BUILD)
