# Intel Quickstart — Shared Makefile
# CDD → TDD → EDD: Write tests RED, deploy until GREEN
# Each stage gates the next. Run: make test-all

QUICKSTART_NAME ?= $(shell basename $(CURDIR))
PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
HELM ?= helm
PODMAN ?= podman

.PHONY: help test-all test-contracts test-infra test-unit test-integration \
        test-benchmarks test-publication \
        build compose-up compose-down lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

# ── Stage 0: Contracts (CDD) ──────────────────────────────────────────
test-contracts: ## Stage 0 — Validate API contracts (OpenAPI, MCP, AsyncAPI)
	$(PYTEST) tests/contracts/ -v --tb=short

# ── Stage 1: Infrastructure ───────────────────────────────────────────
test-infra: ## Stage 1 — Build containers, start stack, check health
	@echo "=== Building containers ==="
	$(PODMAN) compose build 2>&1 || (echo "FAIL: container build" && exit 1)
	@echo "=== Checking for hardcoded secrets ==="
	@! grep -rn --include="*.py" --include="*.yaml" --include="*.yml" \
		--include="*.json" --include="*.env" \
		-E '(api_key|password|secret)\s*[:=]\s*["\x27][^{$$]' src/ chart/ \
		|| (echo "FAIL: hardcoded secrets found" && exit 1)
	@echo "=== Helm template render ==="
	$(HELM) template test chart/ --values chart/values.yaml 2>&1 || \
		(echo "FAIL: helm template" && exit 1)
	@echo "Stage 1: GREEN"

# ── Stage 2: Unit / Technique (TDD) ──────────────────────────────────
test-unit: ## Stage 2 — Technique-specific unit tests
	$(PYTEST) tests/unit/ -v --tb=short

# ── Stage 3: Integration (EDD) ───────────────────────────────────────
test-integration: ## Stage 3 — End-to-end flow validation
	$(PYTEST) tests/integration/ -v --tb=short

# ── Stage 4: Benchmarks (BDD) ────────────────────────────────────────
test-benchmarks: ## Stage 4 — Performance benchmarks against rubric
	$(PYTEST) tests/benchmarks/ -v --tb=short

# ── Stage 5: Publication ─────────────────────────────────────────────
test-publication: ## Stage 5 — README and repo structure validation
	$(PYTEST) tests/publication/ -v --tb=short

# ── Aggregates ────────────────────────────────────────────────────────
test-all: ## Run all stages sequentially (gated)
	@echo "╔══════════════════════════════════════════╗"
	@echo "║  $(QUICKSTART_NAME) — Validation Matrix  ║"
	@echo "╚══════════════════════════════════════════╝"
	@$(MAKE) test-contracts   && echo "Stage 0: Contracts    ✅" || (echo "Stage 0: Contracts    ❌" && exit 1)
	@$(MAKE) test-infra       && echo "Stage 1: Infra        ✅" || (echo "Stage 1: Infra        ❌" && exit 1)
	@$(MAKE) test-unit        && echo "Stage 2: Unit/TDD     ✅" || (echo "Stage 2: Unit/TDD     ❌" && exit 1)
	@$(MAKE) test-integration && echo "Stage 3: Integration  ✅" || (echo "Stage 3: Integration  ❌" && exit 1)
	@$(MAKE) test-benchmarks  && echo "Stage 4: Benchmarks   ✅" || (echo "Stage 4: Benchmarks   ❌" && exit 1)
	@$(MAKE) test-publication && echo "Stage 5: Publication  ✅" || (echo "Stage 5: Publication  ❌" && exit 1)
	@echo ""
	@echo "ALL STAGES GREEN ✅"

# ── Build & Run ───────────────────────────────────────────────────────
build: ## Build all container images
	$(PODMAN) compose build

compose-up: ## Start local dev stack
	$(PODMAN) compose up -d

compose-down: ## Stop local dev stack
	$(PODMAN) compose down -v

lint: ## Lint Python, Helm, and README
	$(PYTHON) -m ruff check src/ tests/ || true
	$(HELM) lint chart/ || true
