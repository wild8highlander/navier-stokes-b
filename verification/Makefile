# ─────────────────────────────────────────────────────────────────────
# verification/ — Makefile of the verification framework
#
# Every target maps 1:1 onto a component that actually exists in this
# directory (see README.md). Recipe lines are indented with real TABs;
# no target silences exit codes (`|| true` is banned — the auditors
# check for it).
# ─────────────────────────────────────────────────────────────────────

.PHONY: help verify-all verify-levels verify-monolith verify-code \
        verify-common verify-lean test audit verify-repo clean

.DEFAULT_GOAL := help

PYTHON ?= python3
LEAN   ?= lake

help:
	@echo "verification/ — commands:"
	@echo "  make verify-levels    - the L1-L5 reference chain (python_levels; L5 ~10-20 min)"
	@echo "  make verify-monolith  - the self-contained verifier, CI preset (tasks 1-15, ~2 min)"
	@echo "  make verify-code      - the code/code suite (exact constants + Lean audit)"
	@echo "  make verify-common    - the aggregate runner over every suite (contract-enforcing)"
	@echo "  make verify-lean      - the Lean 4 core (needs lake + Mathlib; skips honestly if absent)"
	@echo "  make verify-all       - levels (fast) + code + lean"
	@echo "  make test             - pytest verification/tests (fast consistency tests)"
	@echo "  make audit            - the static Lean audit (audit_lean.py)"
	@echo "  make verify-repo      - the whole-tree auditor, 5 evidence groups"
	@echo "  make clean            - remove generated runs and caches"

# The reference chain L1-L5. Set FAST=1 to skip the 3D benchmark (L5).
verify-levels:
	NSE3D_SKIP=$(FAST) $(PYTHON) scripts/python_levels/verify_all.py

# The self-contained monolithic verifier, CI preset: tasks 1-15 + reports.
verify-monolith:
	$(PYTHON) verify_ns_full.py --ci

# The code/code suite: exact constants (mpmath, 50 digits) + Lean audit.
verify-code:
	cd code/code && $(PYTHON) verify_all.py

# The contract-enforcing aggregate runner (banner -> PASS/FAIL -> JSON).
verify-common:
	$(PYTHON) common/python/main.py --all

# Lean 4 formal core. lake is optional toolchain: if it is absent the
# target says so and exits non-zero (it does not pretend to have run).
verify-lean:
	@if command -v $(LEAN) >/dev/null 2>&1; then \
		cd lean4 && $(LEAN) build && $(LEAN) env lean Tests/AxiomAudit.lean; \
	else \
		echo "verify-lean: lake не установлен — формальное ядро не собиралось."; \
		echo "  Установите elan (https://leanprover.github.io/lean4) и повторите."; \
		exit 3; \
	fi

verify-all: verify-levels verify-code verify-lean

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

audit:
	$(PYTHON) tools/audit/audit_lean.py

verify-repo:
	$(PYTHON) tools/audit/verify_repo.py

clean:
	rm -rf results code/code/results
	find . -name "*.pyc" -delete 2>/dev/null
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
