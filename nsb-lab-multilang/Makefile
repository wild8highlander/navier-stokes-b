# Makefile — NSB Lab polyglot: build + smoke-test every CLI edition
#
#   make all          build C, C++, Rust, Go (scripted languages need nothing)
#   make smoke        run --selftest of every CLI edition (fast, N≤16 grids)
#   make python|c|cpp|rust|go|php|julia    per-edition helpers
#   make clean        remove build artefacts
#
# The web app needs no build step: open webapp/index.html.

SHELL := /bin/bash
.PHONY: all smoke python c cpp rust go php julia web clean help

all: c cpp rust go
	@echo "── all CLI binaries built ──"

help:
	@sed -n '2,9p' $(firstword $(MAKEFILE_LIST))

python:
	@python3 -c "import numpy" 2>/dev/null || { echo "numpy missing: pip install numpy"; exit 1; }
	@python3 python/nsb_lab.py --version

c: c/nsb_lab
c/nsb_lab: c/nsb_lab.c
	$(CC) -O2 -std=c99 -Wall c/nsb_lab.c -o $@ -lm

cpp: cpp/nsb_lab
cpp/nsb_lab: cpp/nsb_lab.cpp
	$(CXX) -O2 -std=c++17 -Wall -pthread cpp/nsb_lab.cpp -o $@

rust: rust/target/release/nsb_lab
rust/target/release/nsb_lab: rust/src/main.rs
	cargo build --release --manifest-path rust/Cargo.toml

go: go/nsb_go
go/nsb_go: go/main.go
	cd go && go build -o nsb_go .

php:
	@php -v | head -1

julia:
	@julia --version || echo "julia not installed (optional)"

web:
	@echo "Open webapp/index.html in a browser (or: python3 -m http.server -d webapp 8080)"

# ── smoke tests: --selftest of everything, tiny grids, no colours ──
smoke:
	@echo "══ NSB Lab smoke: every edition must PASS ══"
	@python3 python/nsb_lab.py --selftest --no-color --ascii --out /tmp/nsb_smoke_py >/dev/null 2>&1 \
	  && echo "  python  PASS" || echo "  python  FAIL"
	@./c/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_c >/dev/null 2>&1 \
	  && echo "  c       PASS" || { test -x c/nsb_lab || echo "  c       (not built: make c)"; test -x c/nsb_lab && echo "  c       FAIL"; }
	@./cpp/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_cpp >/dev/null 2>&1 \
	  && echo "  cpp     PASS" || { test -x cpp/nsb_lab || echo "  cpp     (not built: make cpp)"; test -x cpp/nsb_lab && echo "  cpp     FAIL"; }
	@./rust/target/release/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_rs >/dev/null 2>&1 \
	  && echo "  rust    PASS" || { test -x rust/target/release/nsb_lab || echo "  rust    (not built: make rust)"; test -x rust/target/release/nsb_lab && echo "  rust    FAIL"; }
	@./go/nsb_go --selftest --no-color --ascii --out /tmp/nsb_smoke_go >/dev/null 2>&1 \
	  && echo "  go      PASS" || { test -x go/nsb_go || echo "  go      (not built: make go)"; test -x go/nsb_go && echo "  go      FAIL"; }
	@php php/nsb_lab.php --selftest --no-color --ascii --out /tmp/nsb_smoke_php >/dev/null 2>&1 \
	  && echo "  php     PASS" || echo "  php     FAIL (php missing?)"
	@echo "══ done ══"

clean:
	rm -f c/nsb_lab cpp/nsb_lab go/nsb_go
	rm -rf rust/target cpp/build
	@echo "cleaned"
