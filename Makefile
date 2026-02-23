.PHONY: run stop build logs test migrate test-setup test-unit test-integration test-e2e test-frontend test-all test-cov test-down

run:
	docker-compose up -d

stop:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f --no-color | python3 scripts/log_colorizer.py

# 패키지 설치 및 의존성 강제 갱신 (package.json 변경 시 사용)
update:
	docker-compose down
	docker-compose up -d --build -V

migrate:
	docker-compose run backend alembic upgrade head

init-db:
	docker-compose run backend alembic revision --autogenerate -m "Initial migration"

# ============================================================================
# Test Commands
# ============================================================================
test-setup:
	$(MAKE) -C backend test-setup

test:
	$(MAKE) -C backend test

test-unit:
	$(MAKE) -C backend test-unit

test-integration:
	$(MAKE) -C backend test-integration

test-e2e:
	$(MAKE) -C backend test-e2e

test-frontend:
	@echo "🎨 Running Frontend unit tests..."
	cd frontend && npm run test -- --run

test-frontend-cov:
	@echo "📊 Running Frontend coverage..."
	cd frontend && npm run test:coverage -- --run

test-all: test-frontend test
	@echo "✅ All tests (Frontend + Backend) completed..."

test-cov:
	$(MAKE) -C backend test-cov

test-cov-all: test-cov test-frontend-cov
	@echo "📈 All coverage reports generated..."

test-down:
	$(MAKE) -C backend test-down
