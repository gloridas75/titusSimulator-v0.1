.PHONY: help install test run clean dev docs ui

help:
	@echo "Titus Simulator - Available Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run component tests"
	@echo "  make run        - Start the server"
	@echo "  make dev        - Start in development mode (auto-reload)"
	@echo "  make ui         - Start the web UI (requires server running)"
	@echo "  make both       - Start both server and UI"
	@echo "  make clean      - Clean up generated files"
	@echo "  make docs       - Open API documentation"
	@echo "  make setup      - First-time setup"
	@echo ""

setup:
	@echo "Setting up Titus Simulator..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -e .
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file - please edit with your configuration"; \
	fi
	@echo "Setup complete! Edit .env and run 'make run'"

install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -e .

test:
	@echo "Running component tests..."
	python test_components.py

run:
	@echo "Starting Titus Simulator..."
	uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000

dev:
	@echo "Starting in development mode..."
	uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 --reload

ui:
	@echo "Starting Web UI..."
	@echo "Note: Make sure the API server is running (make run or make dev)"
	streamlit run streamlit_ui.py

both:
	@echo "Starting both server and UI..."
	@echo "Starting API server in background..."
	@uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 & \
	echo "API started. Now starting UI..." && \
	sleep 3 && \
	streamlit run streamlit_ui.py

clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf src/titus_simulator/__pycache__
	rm -rf .pytest_cache
	rm -f sim_state.db
	rm -f test_state.db
	@echo "Clean complete!"

docs:
	@echo "Opening API documentation..."
	@echo "Server must be running. If not, start with: make run"
	@sleep 1
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

health:
	@echo "Checking health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Server not running. Start with: make run"

trigger:
	@echo "Triggering simulation cycle..."
	@curl -s -X POST http://localhost:8000/run-once | python3 -m json.tool

stats:
	@echo "Getting statistics..."
	@curl -s http://localhost:8000/stats | python3 -m json.tool

