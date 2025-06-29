.PHONY: help build up down logs restart clean health

# Default target
help:
	@echo "Available targets:"
	@echo "  build     - Build the Docker images"
	@echo "  up        - Start services in background"
	@echo "  down      - Stop and remove services"
	@echo "  logs      - Show logs from mercury-sync service"
	@echo "  restart   - Restart the mercury-sync service"
	@echo "  clean     - Stop services and remove volumes (DESTRUCTIVE)"
	@echo "  health    - Check service health"
	@echo "  shell     - Open shell in sync container"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f mercury-sync

restart:
	docker-compose restart mercury-sync

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
