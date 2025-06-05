from celery import Celery
import os

# Configure Celery app
app = Celery('sped_feedback_tasks')

# Get broker URL from environment or use default
broker_url = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'rpc://')

app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Auto-discover tasks in the project
app.autodiscover_tasks(['celery_tasks.process_feedback', 
                        'celery_tasks.vector_embeddings',
                        'celery_tasks.graph_processing'])

if __name__ == '__main__':
    app.start()
