.PHONY: test-setup test test-unit test-integration test-e2e test-cov test-down

# ============================================================================
# 테스트 환경 구성
# ============================================================================
test-setup:
	@echo "🚀 Setting up test environment..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 5
	@echo "📦 Installing test dependencies..."
	../venv/bin/pip install -r requirements-test.txt
	../venv/bin/playwright install chromium
	@echo "✅ Test environment ready!"

# ============================================================================
# 테스트 유틸리티
# ============================================================================
ensure-test-db:
	@if ! docker ps --filter name=krafton_test_db --format '{{.Names}}' | grep -q 'krafton_test_db'; then \
		echo "🚀 Test database is not running. Starting it now..."; \
		docker-compose -f docker-compose.test.yml up -d test-db; \
		echo "⏳ Waiting for database to be ready..."; \
		sleep 5; \
	fi

# ============================================================================
# 테스트 실행
# ============================================================================
test: ensure-test-db
	@echo "🧪 Running all tests..."
	../venv/bin/pytest tests/ -v

test-unit: ensure-test-db
	@echo "🔬 Running unit tests..."
	../venv/bin/pytest tests/unit/ -m unit -v

test-integration: ensure-test-db
	@echo "🔗 Running integration tests..."
	../venv/bin/pytest tests/integration/ -m integration -v

test-e2e: ensure-test-db
	@echo "🌐 Running E2E tests..."
	../venv/bin/pytest tests/e2e/ -m e2e -v

# ============================================================================
# 커버리지 리포트
# ============================================================================
test-cov: ensure-test-db
	@echo "📊 Running tests with coverage..."
	../venv/bin/pytest --cov=app --cov-report=html --cov-report=term-missing --cov-branch --cov-config=.coveragerc --cov-fail-under=90
	@echo ""
	@echo "✅ Coverage report generated!"
	@echo "📄 HTML report: file://$(PWD)/htmlcov/index.html"
	@echo ""

# ============================================================================
# 테스트 환경 종료
# ============================================================================
test-down:
	@echo "🛑 Stopping test environment..."
	docker-compose -f docker-compose.test.yml down -v
	@echo "✅ Test environment stopped!"

# ============================================================================
# 헬프
# ============================================================================
help:
	@echo "Available test commands:"
	@echo "  make test-setup      - Setup test environment (Docker + dependencies)"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration- Run integration tests only"
	@echo "  make test-e2e        - Run E2E tests only"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make test-down       - Stop test environment"
