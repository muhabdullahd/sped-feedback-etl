# Makefile for Special Education Feedback Insight System
# Provides shortcuts for common commands

# Variables
SHELL := /bin/zsh
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
FLASK_APP := flask_app.app
FLASK_ENV := development
FLASK_PORT := 5000
AIRFLOW_HOME := $(shell pwd)/airflow
STREAMLIT_APP := dashboard/streamlit_app.py
LOGS_DIR := logs

# Ensure logs directory exists
$(LOGS_DIR):
	mkdir -p $(LOGS_DIR)

# Virtual environment setup
$(VENV_BIN)/activate:
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Run 'source venv/bin/activate' to activate."

venv: $(VENV_BIN)/activate

# Install dependencies
install: venv
	$(VENV_BIN)/pip install -r requirements.txt
	@echo "Dependencies installed."

# Flask commands
flask-run: $(LOGS_DIR)
	@echo "Starting Flask application on port $(FLASK_PORT)..."
	FLASK_APP=$(FLASK_APP) FLASK_ENV=$(FLASK_ENV) $(VENV_BIN)/flask run --host=0.0.0.0 --port=$(FLASK_PORT)

flask-debug: $(LOGS_DIR)
	@echo "Starting Flask application in debug mode on port $(FLASK_PORT)..."
	FLASK_APP=$(FLASK_APP) FLASK_ENV=$(FLASK_ENV) FLASK_DEBUG=1 $(VENV_BIN)/flask run --host=0.0.0.0 --port=$(FLASK_PORT)

flask-bg: $(LOGS_DIR)
	@echo "Starting Flask application in background on port $(FLASK_PORT)..."
	FLASK_APP=$(FLASK_APP) FLASK_ENV=$(FLASK_ENV) $(VENV_BIN)/flask run --host=0.0.0.0 --port=$(FLASK_PORT) > $(LOGS_DIR)/flask.log 2>&1 &
	@echo "Flask app started. Check logs at $(LOGS_DIR)/flask.log"

flask: flask-run

# Celery commands
celery-worker: $(LOGS_DIR)
	@echo "Starting Celery worker..."
	$(VENV_BIN)/python -m celery_tasks.worker

celery-worker-bg: $(LOGS_DIR)
	@echo "Starting Celery worker in background..."
	$(VENV_BIN)/python -m celery_tasks.worker > $(LOGS_DIR)/celery.log 2>&1 &
	@echo "Celery worker started. Check logs at $(LOGS_DIR)/celery.log"

celery-flower: $(LOGS_DIR)
	@echo "Starting Celery Flower monitoring on port 5555..."
	$(VENV_BIN)/celery -A celery_tasks.celery flower --port=5555

celery: celery-worker

# Airflow commands
airflow-init: $(LOGS_DIR)
	@echo "Initializing Airflow..."
	mkdir -p $(AIRFLOW_HOME)
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow db init
	@echo "Creating Airflow admin user..."
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com \
		--password admin || echo "User may already exist, continuing..."
	mkdir -p $(AIRFLOW_HOME)/dags
	@echo "Linking Airflow DAGs..."
	for dag_file in $(shell pwd)/airflow_dags/*.py; do \
		if [ -f "$${dag_file}" ] && [[ "$${dag_file}" != *"__init__.py" ]]; then \
			ln -sf "$${dag_file}" "$(AIRFLOW_HOME)/dags/$$(basename $${dag_file})" || echo "Failed to link $${dag_file}"; \
		fi; \
	done
	@echo "Airflow initialized. Ready to start webserver and scheduler."

airflow-webserver: $(LOGS_DIR)
	@echo "Starting Airflow webserver on port 8080..."
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow webserver -p 8080

airflow-webserver-bg: $(LOGS_DIR)
	@echo "Starting Airflow webserver in background on port 8080..."
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow webserver -p 8080 > $(LOGS_DIR)/airflow_webserver.log 2>&1 &
	@echo "Airflow webserver started. Check logs at $(LOGS_DIR)/airflow_webserver.log"

airflow-scheduler: $(LOGS_DIR)
	@echo "Starting Airflow scheduler..."
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow scheduler

airflow-scheduler-bg: $(LOGS_DIR)
	@echo "Starting Airflow scheduler in background..."
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(VENV_BIN)/airflow scheduler > $(LOGS_DIR)/airflow_scheduler.log 2>&1 &
	@echo "Airflow scheduler started. Check logs at $(LOGS_DIR)/airflow_scheduler.log"

airflow: airflow-init
	@echo "Starting Airflow webserver and scheduler..."
	make airflow-webserver-bg
	make airflow-scheduler-bg
	@echo "Airflow is running at http://localhost:8080 (Username: admin, Password: admin)"

# Database commands
mysql-start:
	@echo "Starting MySQL service..."
	brew services start mysql

mysql-stop:
	@echo "Stopping MySQL service..."
	brew services stop mysql

mysql-create-db:
	@echo "Creating sped_feedback database if it doesn't exist..."
	mysql -u root -e "CREATE DATABASE IF NOT EXISTS sped_feedback;"

mysql: mysql-start mysql-create-db
	@echo "MySQL is running with sped_feedback database."

# RabbitMQ commands
rabbitmq-start:
	@echo "Starting RabbitMQ service..."
	brew services start rabbitmq

rabbitmq-stop:
	@echo "Stopping RabbitMQ service..."
	brew services stop rabbitmq

rabbitmq: rabbitmq-start
	@echo "RabbitMQ is running."

# Qdrant commands
qdrant-docker:
	@echo "Starting Qdrant using Docker..."
	docker run -d -p 6333:6333 -p 6334:6334 \
		-v $(shell pwd)/qdrant_storage:/qdrant/storage \
		--name qdrant_sped qdrant/qdrant
	@echo "Qdrant is running at http://localhost:6333"

qdrant-stop:
	@echo "Stopping Qdrant Docker container..."
	docker stop qdrant_sped
	docker rm qdrant_sped

qdrant: qdrant-docker

# Streamlit commands
streamlit-run: $(LOGS_DIR)
	@echo "Starting Streamlit dashboard..."
	$(VENV_BIN)/streamlit run $(STREAMLIT_APP)

streamlit-bg: $(LOGS_DIR)
	@echo "Starting Streamlit dashboard in background..."
	$(VENV_BIN)/streamlit run $(STREAMLIT_APP) > $(LOGS_DIR)/streamlit.log 2>&1 &
	@echo "Streamlit dashboard started. Check logs at $(LOGS_DIR)/streamlit.log"

streamlit: streamlit-run

# Start all services in background
start-all: $(LOGS_DIR)
	@echo "Starting all services in background..."
	make mysql
	make rabbitmq
	make qdrant-docker
	make flask-bg
	make celery-worker-bg
	make airflow
	make streamlit-bg
	@echo "All services started."

# Stop all services
stop-all:
	@echo "Stopping all services..."
	make mysql-stop
	make rabbitmq-stop
	make qdrant-stop
	@echo "Services stopped. Background processes may still be running."
	@echo "Use 'ps aux | grep -e flask -e celery -e airflow -e streamlit' to find and kill them."

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	@echo "Temporary files cleaned."

# Help command
help:
	@echo "Special Education Feedback Insight System Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make install           - Install dependencies in virtual environment"
	@echo "  make flask             - Start Flask application"
	@echo "  make flask-debug       - Start Flask application in debug mode"
	@echo "  make flask-bg          - Start Flask application in background"
	@echo "  make celery            - Start Celery worker"
	@echo "  make celery-worker-bg  - Start Celery worker in background"
	@echo "  make celery-flower     - Start Celery Flower monitoring"
	@echo "  make airflow           - Initialize and start Airflow (webserver + scheduler)"
	@echo "  make airflow-init      - Initialize Airflow database and setup"
	@echo "  make mysql             - Start MySQL and create database"
	@echo "  make rabbitmq          - Start RabbitMQ service"
	@echo "  make qdrant            - Start Qdrant using Docker"
	@echo "  make streamlit         - Start Streamlit dashboard"
	@echo "  make streamlit-bg      - Start Streamlit dashboard in background"
	@echo "  make start-all         - Start all services in background"
	@echo "  make stop-all          - Stop all services"
	@echo "  make clean             - Clean temporary files"
	@echo "  make help              - Show this help message"

.PHONY: venv install flask flask-run flask-debug flask-bg celery celery-worker celery-worker-bg celery-flower \
	airflow airflow-init airflow-webserver airflow-webserver-bg airflow-scheduler airflow-scheduler-bg \
	mysql mysql-start mysql-stop mysql-create-db rabbitmq rabbitmq-start rabbitmq-stop \
	qdrant qdrant-docker qdrant-stop streamlit streamlit-run streamlit-bg \
	start-all stop-all clean help
