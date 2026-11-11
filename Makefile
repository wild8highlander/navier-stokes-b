# Research Papers — Top-level Makefile
#
# NOTE: all recipe lines are indented with real TAB characters.
# Every verify-* target maps onto a component that actually exists in
# verification/ (see verification/README.md for the framework map).

.PHONY: help install test verify-all verify-python verify-lean \
        verify-code verify-monolith verify-repo verify-manifest \
        manifest check-readmes lint format clean clean-all

.DEFAULT_GOAL := help

PYTHON  ?= python3
LEAN    ?= lake

help: ## Show help
	@echo "Research Papers — Makefile commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the scientific stack used by the suites
	$(PYTHON) -m pip install numpy scipy matplotlib mpmath pytest ruff

test: ## Run the verification consistency tests (pytest)
	cd verification && $(PYTHON) -m pytest tests/ -v --tb=short

verify-all: verify-python verify-lean ## Fast verification: aggregate + Lean (if lake present)

verify-python: ## Aggregate runner over every verification suite (quick preset)
	$(PYTHON) verification/common/python/main.py --all

verify-lean: ## Lean 4 formal core (needs lake; exits 3 with instructions if absent)
	cd verification/lean4 && $(LEAN) build && $(LEAN) env lean Tests/AxiomAudit.lean

verify-code: ## The code/code suite: exact constants + Lean audit
	cd verification/code/code && $(PYTHON) verify_all.py

verify-monolith: ## The self-contained verifier, CI preset (tasks 1-15)
	$(PYTHON) verification/verify_ns_full.py --ci

verify-repo: ## Repository-wide integrity audit of verification/ (5 groups)
	$(PYTHON) verification/tools/audit/verify_repo.py

verify-manifest: ## Check every file against MANIFEST.json (PASS/FAIL)
	$(PYTHON) .github/scripts/verify_manifest.py

manifest: ## Regenerate MANIFEST.json for the current tree
	$(PYTHON) .github/scripts/regen_manifest.py

check-readmes: ## Docs hygiene: every dir has a README, no Cyrillic in READMEs
	$(PYTHON) .github/scripts/check_readmes.py

lint: ## Run linters
	ruff check . --output-format=concise || true

format: ## Auto-format code
	ruff check --fix . && ruff format . || true

clean: ## Clean generated outputs
	rm -rf outputs/ figures/ benchmarks/ __pycache__/ .pytest_cache/
	rm -rf verification/results verification/code/code/results
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean ## Full clean
	rm -rf verification/lean4/.lake/
