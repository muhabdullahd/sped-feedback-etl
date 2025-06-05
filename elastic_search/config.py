import os
from utils.logger import get_logger

logger = get_logger(__name__)

class ElasticsearchConfig:
    """Configuration settings for Elasticsearch."""
    
    # Default index mappings
    FEEDBACK_INDEX_MAPPING = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "student_id": {"type": "keyword"},
                "teacher_name": {"type": "text"},
                "rating": {"type": "integer"},
                "category": {"type": "keyword"},
                "open_feedback": {
                    "type": "text",
                    "analyzer": "english"
                },
                "sentiment": {"type": "keyword"},
                "topics": {"type": "keyword"},
                "entities": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        }
    }
    
    # Default index names
    FEEDBACK_INDEX = "feedback"
    
    @classmethod
    def get_host(cls) -> str:
        """Get Elasticsearch host from environment or default."""
        return os.environ.get("ELASTICSEARCH_HOST", "localhost")
    
    @classmethod
    def get_port(cls) -> str:
        """Get Elasticsearch port from environment or default."""
        return os.environ.get("ELASTICSEARCH_PORT", "9200")
    
    @classmethod
    def get_username(cls) -> str:
        """Get Elasticsearch username from environment."""
        return os.environ.get("ELASTICSEARCH_USERNAME", "")
    
    @classmethod
    def get_password(cls) -> str:
        """Get Elasticsearch password from environment."""
        return os.environ.get("ELASTICSEARCH_PASSWORD", "")
    
    @classmethod
    def get_url(cls) -> str:
        """Get full Elasticsearch URL."""
        host = cls.get_host()
        port = cls.get_port()
        return f"http://{host}:{port}"
