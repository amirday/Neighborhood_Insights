SHELL := /bin/bash

# === Development ===
.PHONY: up down logs clean restart

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

restart: down up

# === Database ===
.PHONY: psql migrate reset-db

psql:
	PGPASSWORD=ni_password psql -h localhost -U ni -d ni

migrate:
	PGPASSWORD=ni_password psql -h localhost -U ni -d ni -f db/01-init-migration-system.sql

reset-db:
	docker compose down postgres
	docker volume rm neighborhood_insights_pgdata || true
	docker compose up -d postgres
	sleep 5
	make migrate

# === ETL ===
.PHONY: etl-cbs-sa etl-all

etl-cbs-sa:
	cd etl && poetry run python cbs_processor.py ../data/raw/cbs_statistical_areas.zip

etl-all:
	cd etl && poetry run python -m etl.pipeline

# === API ===
.PHONY: api api-dev api-test

api:
	cd api && poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000

api-dev:
	cd api && poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	cd api && poetry run pytest tests/ -v

# === Frontend ===
.PHONY: app app-dev app-build app-test

app-dev:
	cd app && pnpm run dev

app-build:
	cd app && pnpm run build

app-test:
	cd app && pnpm run test

# === Testing ===
.PHONY: test test-unit test-integration test-e2e test-all

test-unit:
	cd api && poetry run pytest tests/unit/ -v
	cd etl && poetry run pytest tests/unit/ -v
	cd app && pnpm run test

test-integration:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

test-e2e:
	cd e2e && pnpm exec playwright test

test-all:
	@./scripts/test-all.sh

# === Tiles ===
.PHONY: tiles tiles-neighborhoods

tiles:
	bash tiles/build_tiles.sh

tiles-neighborhoods:
	ogr2ogr -f GeoJSON tiles/neighborhoods.geojson \
		PG:"host=localhost dbname=${POSTGRES_DB:-ni} user=${POSTGRES_USER:-ni} password=${POSTGRES_PASSWORD:-ni_password}" \
		-sql "SELECT neigh_id, name_he AS name, score_0_100, geom FROM neighborhoods_canonical"
	tippecanoe -o tiles/neighborhoods.mbtiles -zg -l neighborhoods --drop-densest-as-needed tiles/neighborhoods.geojson

# === Code Quality ===
.PHONY: format lint type-check pre-commit-install

format:
	cd api && poetry run black . && poetry run isort .
	cd etl && poetry run black . && poetry run isort .
	cd app && pnpm run format

lint:
	cd api && poetry run flake8 .
	cd etl && poetry run flake8 .
	cd app && pnpm run lint

type-check:
	cd api && poetry run mypy .
	cd etl && poetry run mypy .
	cd app && pnpm run type-check

pre-commit-install:
	pip install pre-commit
	pre-commit install

# === Deployment ===
.PHONY: deploy-api deploy-app

deploy-api:
	cd api && flyctl deploy

deploy-app:
	cd app && vercel --prod

# === Data Management ===
.PHONY: data-download data-clean

data-download:
	mkdir -p data/raw
	# Download CBS statistical areas
	curl -L -o data/raw/cbs_stat_areas.zip "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/statistical_areas_2022/FeatureServer/0/query?where=1%3D1&outFields=*&f=pgeojson"
	# Download OSM Israel extract
	wget -c -P data/raw/ https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf

data-clean:
	rm -rf data/raw/*.zip data/raw/*.pbf data/raw/*.csv data/raw/*.json
	rm -rf data/processed/*

# === Help ===
.PHONY: help

help:
	@echo "Neighborhood Insights IL - Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  up              Start all services"
	@echo "  down            Stop all services" 
	@echo "  logs            Show service logs"
	@echo "  restart         Restart all services"
	@echo "  clean           Clean up containers and volumes"
	@echo ""
	@echo "Database:"
	@echo "  psql            Connect to PostgreSQL"
	@echo "  migrate         Run database migrations"
	@echo "  reset-db        Reset database with fresh schema"
	@echo ""
	@echo "Development Servers:"
	@echo "  api-dev         Start API development server"
	@echo "  app-dev         Start frontend development server"
	@echo ""
	@echo "Testing:"
	@echo "  test-unit       Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-e2e        Run end-to-end tests"
	@echo "  test-all        Run comprehensive test suite with report"
	@echo ""
	@echo "Code Quality:"
	@echo "  format          Format all code"
	@echo "  lint            Lint all code"
	@echo "  type-check      Type check all code"
	@echo ""
	@echo "Data:"
	@echo "  etl-all         Run complete ETL pipeline"
	@echo "  data-download   Download raw datasets"
	@echo "  tiles           Generate vector tiles"
