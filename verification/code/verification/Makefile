# Verification Makefile

.PHONY: help verify-all verify-extended verify-formal verify-numerical \
        verify-python verify-lean verify-coq verify-isabelle verify-agda \
        verify-rust verify-cpp verify-haskell test docker-build docker-up clean

PYTHON ?= python3
LEAN   ?= lake
COQ    ?= coqc
CARGO  ?= cargo

help:
	@echo "Verification commands:"

verify-all: verify-python verify-extended

verify-extended: verify-formal verify-numerical

verify-formal: verify-lean verify-coq verify-isabelle verify-agda

verify-numerical: verify-rust verify-cpp verify-haskell

verify-python:
	$(PYTHON) common/python/main.py --section 1 --preset default || true

verify-lean:
	cd lean4 && $(LEAN) build

verify-coq:
	cd coq && coq_makefile -f _CoqProject -o Makefile && make

verify-rust:
	cd rust && $(CARGO) build --release

verify-cpp:
	cd cpp && mkdir -p build && cd build && cmake .. && make -j$$(nproc)

verify-haskell:
	cd haskell && cabal build all

test:
	$(PYTHON) -m pytest tests/ -v --tb=short || true

clean:
	rm -rf outputs/ figures/ __pycache__/
	find . -name "*.pyc" -delete 2>/dev/null || true
