.PHONY: help build up down logs restart clean health sync-build web-build sync-up web-up sync-logs web-logs prod-up prod-optimized setup-performance monitor-performance deploy-prod

# Default target
help:
	@echo "Available targets:"
	@echo "  === Main Platform ==="
	@echo "  build         - Build all Docker images locally"
	@echo "  up            - Start all services in background"
	@echo "  down          - Stop and remove all services"
	@echo "  logs          - Show logs from all services"
	@echo "  restart       - Restart all services"
	@echo "  clean         - Stop services and remove volumes (DESTRUCTIVE)"
	@echo "  health        - Check service health"
	@echo "  prod-up       - Start services using published Docker Hub images"
	@echo "  dev           - Start development environment (builds locally)"
	@echo ""
	@echo "  === Performance Optimization ==="
	@echo "  setup-performance - Set up performance optimizations"
	@echo "  prod-optimized    - Start optimized production with nginx"
	@echo "  deploy-prod       - Deploy production with full optimizations"
	@echo "  monitor-performance - Test and monitor performance"
	@echo ""
	@echo "  === Sync Service ==="
	@echo "  sync-build    - Build sync service image"
	@echo "  sync-up       - Start sync service only"
	@echo "  sync-logs     - Show sync service logs"
	@echo "  sync-shell    - Open shell in sync container"
	@echo ""
	@echo "  === Web Interface ==="
	@echo "  web-build     - Build web interface image"
	@echo "  web-up        - Start web interface only"
	@echo "  web-logs      - Show web interface logs"
	@echo "  web-shell     - Open shell in web container"
	@echo ""
	@echo "  === Production Deployment ==="
	@echo "  prod-optimized - Start optimized production services with nginx"
	@echo "  setup-performance - Set up performance optimizations"
	@echo "  monitor-performance - Monitor performance"
	@echo "  deploy-prod    - Deploy production with performance optimizations"

# Main platform commands
build:
	docker-compose -f docker-compose.dev.yml build

up:
	docker-compose -f docker-compose.dev.yml up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

# Production deployment using published images
prod-up:
	@echo "Starting services with published Docker Hub images..."
	@echo "Make sure to update docker-compose.yml with your Docker Hub username!"
	docker-compose pull
	docker-compose up -d

# Production deployment with performance optimizations
prod-optimized:
	@echo "Starting optimized production services with nginx..."
	@if [ ! -f .env.prod ]; then echo "❌ .env.prod not found! Run 'make setup-performance' first."; exit 1; fi
	docker-compose -f docker-compose.prod.yml pull
	docker-compose -f docker-compose.prod.yml up -d

# Development environment
dev:
	@echo "Starting development environment with local builds..."
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.dev.yml up -d

# Sync service commands
sync-build:
	cd sync_app && docker build -t mercury-bank-sync:dev .

sync-up:
	docker-compose -f docker-compose.dev.yml up mercury-sync -d

sync-logs:
	docker-compose logs -f mercury-sync

sync-shell:
	docker-compose exec mercury-sync /bin/bash

# Web interface commands  
web-build:
	cd web_app && docker build -t mercury-bank-sync-gui:dev .

web-up:
	docker-compose -f docker-compose.dev.yml up web-app -d

web-logs:
	docker-compose logs -f web-app

web-shell:
	docker-compose exec web-app /bin/bash

clean:
	@echo "WARNING: This will remove all data. Press Ctrl+C to cancel."
	@sleep 5
	docker-compose down -v
	docker system prune -f

health:
	docker-compose ps
	@echo "\nChecking mercury-sync health:"
	docker-compose exec mercury-sync python health_check.py

shell:
	docker-compose exec mercury-sync /bin/bash

# One-time sync
sync-once:
	RUN_ONCE=true docker-compose run --rm mercury-sync

# Performance optimization setup
setup-performance:
	@echo "🚀 Setting up performance optimizations..."
	./setup_performance.sh

# Monitor performance
monitor-performance:
	@echo "🔍 Testing performance..."
	@if [ -f monitor_performance.sh ]; then \
		./monitor_performance.sh http://localhost/dashboard 5; \
	else \
		echo "❌ Performance monitoring not set up. Run 'make setup-performance' first."; \
	fi

# Production deployment with performance monitoring
deploy-prod:
	@echo "🚀 Deploying production with performance optimizations..."
	@if [ -f deploy_production.sh ]; then \
		./deploy_production.sh; \
	else \
		echo "❌ Production deployment script not found. Run 'make setup-performance' first."; \
	fi
