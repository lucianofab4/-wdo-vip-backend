.PHONY: up down logs build install-playwright

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

logs-bot:
	docker-compose logs -f bot

logs-collector:
	docker-compose logs -f collector

logs-api:
	docker-compose logs -f api

restart-bot:
	docker-compose restart bot

restart-collector:
	docker-compose restart collector

shell-db:
	docker-compose exec postgres psql -U postgres -d signalbot

install-playwright:
	playwright install chromium
	playwright install-deps chromium
