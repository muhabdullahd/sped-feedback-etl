#!/usr/bin/env python
"""
Celery worker script for processing special education feedback.
This worker connects to RabbitMQ and processes tasks asynchronously.
"""
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_tasks.celery import app
from utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == '__main__':
    logger.info("Starting Celery worker for processing special education feedback...")
    app.worker_main(argv=['worker', '--loglevel=info', '-Q', 'celery'])
