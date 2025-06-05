# Special Education Feedback Insight System

A scalable system designed to collect, process, analyze, and generate insights from feedback in special education contexts. This project leverages various data storage solutions and processing tools to extract meaningful patterns and actionable insights from feedback data.

## Project Overview

This system is designed to:

- Collect feedback data from various sources via a Flask API
- Process and analyze feedback using natural language processing techniques
- Store data in appropriate databases (Vector DB, Graph DB, DynamoDB)
- Generate insights through scheduled ETL processes
- Deliver insights through API endpoints

## Architecture

The project follows a modular architecture with the following components:

### Core Components

1. **Web API (Flask)** - `flask_app/`
   - Provides REST API endpoints for feedback submission and insights retrieval
   - Handles input validation and request processing
   - Triggers asynchronous processing tasks

2. **Task Processing (Celery)** - `celery_tasks/`
   - Processes feedback asynchronously using RabbitMQ as message broker
   - Performs text analysis, sentiment analysis, and data transformation
   - Coordinates data flow between different storage systems

3. **ETL Pipelines (Airflow)** - `airflow_dags/`
   - Schedules and orchestrates data processing workflows
   - Manages extract, transform, load operations for batch processing
   - Generates periodic insights and reports

### Data Storage

4. **Vector Database** - `vector_db/`
   - Stores text embeddings for semantic similarity search
   - Enables finding related feedback based on content similarity
   - Supports natural language queries and concept matching

5. **Graph Database** - `graph_db/`
   - Models relationships between feedback, topics, entities, and stakeholders
   - Enables network analysis and relationship pattern discovery
   - Supports traversal queries for complex insight generation

6. **DynamoDB** - `dynamo/`
   - Provides fast, scalable NoSQL storage for feedback and metadata
   - Supports high-throughput operations and flexible schema
   - Primary persistent storage for the system

7. **Elasticsearch** - `elastic_search/`
   - Full-text search and analytics engine
   - Indexes feedback data for fast and powerful text search capabilities
   - Supports advanced queries for finding patterns in feedback

8. **Utilities** - `utils/`
   - Shared logging, validation, and helper functions
   - Common code used across different components

## System Flow

1. Feedback is submitted through the Flask API
2. Initial validation and preprocessing occurs
3. Celery tasks are triggered for asynchronous processing
4. Processed data is stored in appropriate databases
5. Airflow DAGs run scheduled jobs to generate insights
6. Insights are made available through API endpoints

## Setup and Installation

### Prerequisites

- Python 3.8+
- RabbitMQ (for Celery)
- Airflow
- Access to AWS (for DynamoDB)
- A vector database (e.g., Pinecone, Weaviate, or Milvus)
- A graph database (e.g., Neo4j)
- Elasticsearch (for text search)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd sped-feedback-etl
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Elasticsearch:
   ```bash
   ./setup_elasticsearch.sh
   ```

5. Set up environment variables (create a `.env` file in the project root):
   ```
   # Flask settings
   FLASK_APP=flask_app.app
   FLASK_ENV=development
   
   # Database settings
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@localhost/sped_feedback
   
   # Vector DB settings
   VECTOR_DB_HOST=localhost
   VECTOR_DB_PORT=6333
   
   # Graph DB settings
   GRAPH_DB_HOST=localhost
   GRAPH_DB_PORT=8182
   
   # AWS settings
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   
   # Elasticsearch settings
   ELASTICSEARCH_HOST=localhost
   ELASTICSEARCH_PORT=9200
   ```
   SECRET_KEY=your-secret-key

   # AWS settings
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   DYNAMODB_REGION=us-east-1

   # Database connections
   VECTOR_DB_HOST=your-vector-db-host
   VECTOR_DB_PORT=your-vector-db-port
   GRAPH_DB_URI=your-graph-db-uri
   GRAPH_DB_USER=your-graph-db-user
   GRAPH_DB_PASSWORD=your-graph-db-password

   # Celery settings
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
   CELERY_RESULT_BACKEND=rpc://
   ```

## Running Locally

### Starting the Flask API

```bash
cd sped-feedback-etl
source venv/bin/activate
flask run --host=0.0.0.0 --port=5000
```

### Starting Celery Worker

```bash
cd sped-feedback-etl
source venv/bin/activate
celery -A celery_tasks.celery worker --loglevel=info
```

### Running Airflow

1. Initialize the Airflow database (first time only):
   ```bash
   airflow db init
   ```

2. Create an Airflow user (first time only):
   ```bash
   airflow users create \
       --username admin \
       --firstname Admin \
       --lastname User \
       --role Admin \
       --email admin@example.com \
       --password admin
   ```

3. Start the Airflow webserver:
   ```bash
   airflow webserver --port 8080
   ```

4. Start the Airflow scheduler in a separate terminal:
   ```bash
   airflow scheduler
   ```

5. Place the DAG files in your Airflow DAGs directory or configure Airflow to use the project's `airflow_dags` directory.

## API Endpoints

### Health Check
```
GET /health
```

### Submit Feedback
```
POST /api/feedback
Content-Type: application/json

{
  "content": "Student showed significant improvement in reading comprehension after the new visual aids were introduced.",
  "source": "teacher",
  "timestamp": "2023-05-15T14:30:00Z",
  "metadata": {
    "studentId": "S12345",
    "gradeLevel": "3",
    "subject": "reading"
  }
}
```

### Get Insights
```
GET /api/insights
```

## Tools and Technologies Used

- **Flask**: Web framework for API endpoints
- **Celery**: Distributed task queue
- **RabbitMQ**: Message broker for Celery
- **Airflow**: Workflow orchestration
- **DynamoDB**: NoSQL database for data persistence
- **Vector Database**: (Pinecone/Weaviate/Milvus) for similarity search
- **Graph Database**: (Neo4j) for relationship modeling
- **Python**: Primary programming language
- **scikit-learn**: For machine learning components
- **spaCy**: For natural language processing

## Development

### Project Structure
```
sped-feedback-etl/
├── airflow_dags/          # Airflow workflow definitions
├── celery_tasks/          # Celery task definitions
├── dynamo/                # DynamoDB interface
├── flask_app/             # Flask web application
├── graph_db/              # Graph database interface
├── utils/                 # Shared utilities
├── vector_db/             # Vector database interface
├── requirements.txt       # Python dependencies
└── .gitignore             # Git ignore file
```

### Adding New Features

- Add new API endpoints in `flask_app/app.py`
- Create new Celery tasks in `celery_tasks/`
- Define new Airflow DAGs in `airflow_dags/`
- Extend database clients as needed

## License



