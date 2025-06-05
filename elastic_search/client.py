import os
from typing import List, Dict, Any, Optional, Union
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, RequestError
from utils.logger import get_logger

logger = get_logger(__name__)

class ElasticsearchClient:
    """Client for interacting with Elasticsearch for feedback data."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Elasticsearch client.
        
        Args:
            host: Elasticsearch host address
            port: Elasticsearch port
            username: Elasticsearch username (if authentication is enabled)
            password: Elasticsearch password (if authentication is enabled)
        """
        self.host = host or os.environ.get('ELASTICSEARCH_HOST', 'localhost')
        self.port = port or os.environ.get('ELASTICSEARCH_PORT', '9200')
        self.username = username or os.environ.get('ELASTICSEARCH_USERNAME')
        self.password = password or os.environ.get('ELASTICSEARCH_PASSWORD')
        self.url = f"http://{self.host}:{self.port}"
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to Elasticsearch.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Build connection params
            conn_params = {"hosts": [self.url]}
            
            # Add authentication if provided
            if self.username and self.password:
                conn_params["basic_auth"] = [self.username, self.password]
            
            # Connect to Elasticsearch
            self.client = Elasticsearch(**conn_params)
            self.connected = self.client.ping()
            
            if self.connected:
                logger.info(f"Connected to Elasticsearch at {self.url}")
                return True
            else:
                logger.error("Failed to ping Elasticsearch server")
                return False
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Elasticsearch: {str(e)}")
            self.connected = False
            return False
    
    def create_index(self, index_name: str, mapping: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create an Elasticsearch index with optional mapping.
        
        Args:
            index_name: Name of the index to create
            mapping: Optional mapping configuration for the index
            
        Returns:
            bool: Success status
        """
        if not self.connected and not self.connect():
            return False
            
        try:
            # Check if index already exists
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists")
                return True
                
            # Create index with mapping if provided
            if mapping:
                self.client.indices.create(index=index_name, body=mapping)
            else:
                self.client.indices.create(index=index_name)
                
            logger.info(f"Created Elasticsearch index '{index_name}'")
            return True
            
        except RequestError as e:
            logger.error(f"Error creating index '{index_name}': {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating index '{index_name}': {str(e)}")
            return False
    
    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Index a document in Elasticsearch.
        
        Args:
            index_name: Name of the index
            doc_id: Unique ID for the document
            document: Document data to index
            
        Returns:
            bool: Success status
        """
        if not self.connected and not self.connect():
            return False
            
        try:
            self.client.index(index=index_name, id=doc_id, document=document)
            logger.info(f"Indexed document '{doc_id}' in index '{index_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document '{doc_id}': {str(e)}")
            return False
    
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]], id_field: str = "id") -> bool:
        """
        Bulk index multiple documents in Elasticsearch.
        
        Args:
            index_name: Name of the index
            documents: List of documents to index
            id_field: Field name to use as document ID
            
        Returns:
            bool: Success status
        """
        if not self.connected and not self.connect():
            return False
            
        try:
            # Prepare bulk indexing operations
            operations = []
            for doc in documents:
                doc_id = doc.get(id_field)
                if not doc_id:
                    doc_id = None  # Let ES generate an ID
                    
                operations.append({"index": {"_index": index_name, "_id": doc_id}})
                operations.append(doc)
            
            # Execute bulk operation
            if operations:
                response = self.client.bulk(operations=operations)
                if response.get("errors"):
                    logger.warning(f"Some errors occurred during bulk indexing: {response}")
                    return False
                logger.info(f"Bulk indexed {len(documents)} documents in index '{index_name}'")
                return True
            else:
                logger.warning("No documents to index")
                return False
            
        except Exception as e:
            logger.error(f"Error bulk indexing documents: {str(e)}")
            return False
    
    def search(self, 
              index_name: str, 
              query: Dict[str, Any], 
              size: int = 10, 
              from_: int = 0) -> Dict[str, Any]:
        """
        Perform a search query in Elasticsearch.
        
        Args:
            index_name: Name of the index to search
            query: Elasticsearch query DSL
            size: Number of results to return
            from_: Starting offset for pagination
            
        Returns:
            Dict with search results
        """
        if not self.connected and not self.connect():
            return {"error": "Not connected to Elasticsearch", "hits": [], "total": 0}
            
        try:
            response = self.client.search(
                index=index_name,
                query=query,
                size=size,
                from_=from_
            )
            
            # Format the results
            hits = []
            for hit in response["hits"]["hits"]:
                doc = hit["_source"]
                doc["_id"] = hit["_id"]
                doc["_score"] = hit["_score"]
                hits.append(doc)
                
            result = {
                "hits": hits,
                "total": response["hits"]["total"]["value"],
                "max_score": response["hits"]["max_score"]
            }
            
            logger.info(f"Search in index '{index_name}' returned {len(hits)} results")
            return result
            
        except Exception as e:
            logger.error(f"Error searching in index '{index_name}': {str(e)}")
            return {"error": str(e), "hits": [], "total": 0}
    
    def text_search(self, index_name: str, text: str, fields: List[str], size: int = 10) -> Dict[str, Any]:
        """
        Perform a multi-match text search across specified fields.
        
        Args:
            index_name: Name of the index to search
            text: Text to search for
            fields: List of fields to search in
            size: Number of results to return
            
        Returns:
            Dict with search results
        """
        query = {
            "multi_match": {
                "query": text,
                "fields": fields,
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        }
        
        return self.search(index_name, query, size)
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        Delete a document from an index.
        
        Args:
            index_name: Name of the index
            doc_id: ID of document to delete
            
        Returns:
            bool: Success status
        """
        if not self.connected and not self.connect():
            return False
            
        try:
            self.client.delete(index=index_name, id=doc_id)
            logger.info(f"Deleted document '{doc_id}' from index '{index_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document '{doc_id}': {str(e)}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an entire index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            bool: Success status
        """
        if not self.connected and not self.connect():
            return False
            
        try:
            self.client.indices.delete(index=index_name)
            logger.info(f"Deleted index '{index_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting index '{index_name}': {str(e)}")
            return False
