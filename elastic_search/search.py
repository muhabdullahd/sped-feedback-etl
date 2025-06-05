"""
Elasticsearch utility functions for search operations and indexing.
"""
from typing import Dict, List, Any, Optional
from elastic_search.client import ElasticsearchClient
from elastic_search.config import ElasticsearchConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def get_client() -> ElasticsearchClient:
    """
    Get a configured Elasticsearch client.
    
    Returns:
        ElasticsearchClient: Configured client instance
    """
    client = ElasticsearchClient(
        host=ElasticsearchConfig.get_host(),
        port=ElasticsearchConfig.get_port(),
        username=ElasticsearchConfig.get_username(),
        password=ElasticsearchConfig.get_password()
    )
    client.connect()
    return client

def initialize_indices():
    """
    Initialize required Elasticsearch indices if they don't exist.
    """
    client = get_client()
    
    # Create feedback index with mapping
    client.create_index(
        ElasticsearchConfig.FEEDBACK_INDEX,
        mapping=ElasticsearchConfig.FEEDBACK_INDEX_MAPPING
    )

def index_feedback(feedback_data: Dict[str, Any]) -> bool:
    """
    Index a feedback document in Elasticsearch.
    
    Args:
        feedback_data: The feedback data to index
        
    Returns:
        bool: Success status
    """
    client = get_client()
    
    # Extract document ID
    doc_id = feedback_data.get("id")
    if not doc_id:
        logger.warning("Feedback data missing ID, generating one automatically")
        
    # Index the document
    return client.index_document(
        ElasticsearchConfig.FEEDBACK_INDEX,
        str(doc_id) if doc_id else "",
        feedback_data
    )

def bulk_index_feedback(feedback_items: List[Dict[str, Any]]) -> bool:
    """
    Bulk index multiple feedback documents.
    
    Args:
        feedback_items: List of feedback documents to index
        
    Returns:
        bool: Success status
    """
    client = get_client()
    return client.bulk_index(
        ElasticsearchConfig.FEEDBACK_INDEX,
        feedback_items,
        id_field="id"
    )

def search_feedback(query_text: str, size: int = 10) -> Dict[str, Any]:
    """
    Search for feedback using text query.
    
    Args:
        query_text: Text to search for
        size: Number of results to return
        
    Returns:
        Dict with search results
    """
    client = get_client()
    return client.text_search(
        ElasticsearchConfig.FEEDBACK_INDEX,
        query_text,
        fields=["open_feedback", "teacher_name", "topics", "entities"],
        size=size
    )

def search_feedback_by_category(category: str, size: int = 10) -> Dict[str, Any]:
    """
    Search for feedback by category.
    
    Args:
        category: Category to filter by
        size: Number of results to return
        
    Returns:
        Dict with search results
    """
    client = get_client()
    query = {
        "term": {
            "category": category
        }
    }
    return client.search(ElasticsearchConfig.FEEDBACK_INDEX, query, size)

def search_feedback_by_sentiment(sentiment: str, size: int = 10) -> Dict[str, Any]:
    """
    Search for feedback by sentiment.
    
    Args:
        sentiment: Sentiment to filter by (positive, negative, neutral)
        size: Number of results to return
        
    Returns:
        Dict with search results
    """
    client = get_client()
    query = {
        "term": {
            "sentiment": sentiment
        }
    }
    return client.search(ElasticsearchConfig.FEEDBACK_INDEX, query, size)

def advanced_feedback_search(
    text: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    size: int = 10
) -> Dict[str, Any]:
    """
    Perform advanced search on feedback with multiple filters.
    
    Args:
        text: Optional text to search for
        category: Optional category to filter by
        sentiment: Optional sentiment to filter by
        min_rating: Optional minimum rating
        max_rating: Optional maximum rating
        size: Number of results to return
        
    Returns:
        Dict with search results
    """
    client = get_client()
    
    # Build compound query
    must_clauses = []
    filter_clauses = []
    
    # Add text search if provided
    if text:
        must_clauses.append({
            "multi_match": {
                "query": text,
                "fields": ["open_feedback", "teacher_name", "topics", "entities"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    
    # Add category filter if provided
    if category:
        filter_clauses.append({
            "term": {"category": category}
        })
    
    # Add sentiment filter if provided
    if sentiment:
        filter_clauses.append({
            "term": {"sentiment": sentiment}
        })
    
    # Add rating range if provided
    if min_rating is not None or max_rating is not None:
        range_query = {"range": {"rating": {}}}
        
        if min_rating is not None:
            range_query["range"]["rating"]["gte"] = min_rating
            
        if max_rating is not None:
            range_query["range"]["rating"]["lte"] = max_rating
            
        filter_clauses.append(range_query)
    
    # Build the complete query
    query = {
        "bool": {}
    }
    
    if must_clauses:
        query["bool"]["must"] = must_clauses
        
    if filter_clauses:
        query["bool"]["filter"] = filter_clauses
    
    # If no clauses were added, search for all documents
    if not must_clauses and not filter_clauses:
        query = {"match_all": {}}
    
    return client.search(ElasticsearchConfig.FEEDBACK_INDEX, query, size)
