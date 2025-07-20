.DEFAULT_GOAL := help

# Docker
up: ## Start and build Docker containers
	@echo "Starting Docker containers..."
	docker compose up --build -d

down: ## Stop and remove Docker containers
	@echo "Stopping Docker containers..."
	docker compose down

restart: ## Restart Docker containers
	@echo "Restarting Docker containers..."
	git pull
	docker compose down
	docker compose up --build -d

logs: ## Show logs for Docker containers
	@echo "Showing logs..."
	docker compose logs -f

# Help
help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
