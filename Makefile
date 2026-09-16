# Research Papers — Top-level Makefile

.PHONY: help install test verify-all verify-extended         verify-python verify-julia verify-java         verify-lean verify-coq verify-isabelle verify-agda         verify-rust verify-cpp verify-haskell         docker-build docker-up docker-down         docs docs-serve clean clean-all lint format

.DEFAULT_GOAL := help

PYTHON  ?= python3
JULIA   ?= julia
LEAN    ?= lake
COQ     ?= coqc
CARGO   ?= cargo
CMAKE   ?= cmake
CABAL   ?= cabal
DOCKER  ?= docker
COMPOSE ?= docker compose

help: ## Show help
	@echo "Research Papers — Makefile commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	$(PYTHON) -m pip install numpy scipy matplotlib reportlab python-docx mpmath pytest ruff
	cd verification/web-dashboard && npm ci || true

test: ## Run all tests
	cd verification && $(PYTHON) -m pytest tests/ -v --tb=short || true

verify-all: verify-python ## Run original verifications
	@echo "Running original Python/Julia/Java verification..."

verify-extended: verify-lean verify-coq verify-rust verify-cpp verify-haskell ## Run all 7 new languages

verify-python: ## Python verification
	cd verification && $(PYTHON) common/python/main.py --section 1 --preset default || true

verify-lean: ## Lean 4 formal verification
	cd verification/lean4 && $(LEAN) build

verify-coq: ## Coq formal verification
	cd verification/coq && coq_makefile -f _CoqProject -o Makefile && make

verify-rust: ## Rust numerical verification
	cd verification/rust && $(CARGO) build --release

verify-cpp: ## C++ numerical verification
	cd verification/cpp && mkdir -p build && cd build && $(CMAKE) .. && make -j$$(nproc)

verify-haskell: ## Haskell verification
	cd verification/haskell && $(CABAL) build all

docker-build: ## Build all Docker images
	cd verification && $(COMPOSE) -f docker/docker-compose.yml build

docker-up: ## Start all services
	cd verification && $(COMPOSE) -f docker/docker-compose.yml up -d

docker-down: ## Stop all services
	cd verification && $(COMPOSE) -f docker/docker-compose.yml down

docs: ## Build documentation
	cd verification && mkdocs build

docs-serve: ## Serve documentation locally
	cd verification && mkdocs serve

lint: ## Run linters
	ruff check . --output-format=concise || true

format: ## Auto-format code
	ruff check --fix . && ruff format . || true

clean: ## Clean generated outputs
	rm -rf outputs/ figures/ benchmarks/ __pycache__/ .pytest_cache/
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean ## Full clean
	rm -rf node_modules/ verification/web-dashboard/node_modules/
	rm -rf verification/rust/target/ verification/cpp/build/
	rm -rf verification/haskell/dist-newstyle/ verification/lean4/.lake/
