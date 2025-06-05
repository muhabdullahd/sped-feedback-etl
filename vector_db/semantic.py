"""
Semantic processing module for special education feedback.

This module handles:
1. Converting feedback text to vector embeddings using SentenceTransformers
2. Storing embeddings and metadata in Qdrant vector database
3. Performing semantic search based on vector similarity
"""
import os
import numpy as np
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from utils.logger import get_logger

logger = get_logger(__name__)

class SemanticProcessor:
    """
    Processes feedback text into semantic embeddings and interfaces with Qdrant.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        qdrant_host: str = None,
        qdrant_port: int = None,
        collection_name: str = "feedback_embeddings",
        vector_size: int = 384  # Dimension of all-MiniLM-L6-v2 embeddings
    ):
        """
        Initialize the semantic processor.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
            qdrant_host: Qdrant server host (defaults to environment variable or localhost)
            qdrant_port: Qdrant server port (defaults to environment variable or 6333)
            collection_name: Name of the Qdrant collection to use
            vector_size: Dimension of the vector embeddings
        """
        self.model_name = model_name
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize the SentenceTransformer model
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
        
        # Initialize Qdrant client
        self.qdrant_host = qdrant_host or os.environ.get("QDRANT_HOST", "localhost")
        self.qdrant_port = qdrant_port or int(os.environ.get("QDRANT_PORT", 6333))
        
        logger.info(f"Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
        try:
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            logger.info("Successfully connected to Qdrant")
            
            # Ensure collection exists
            self._ensure_collection_exists()
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {str(e)}")
            raise
    
    def _ensure_collection_exists(self):
        """Ensure that the Qdrant collection exists, creating it if necessary."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection '{self.collection_name}' in Qdrant")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a piece of text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            np.ndarray: The embedding vector
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            # Return zero vector of the correct size
            return np.zeros(self.vector_size)
        
        try:
            embedding = self.model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def store_feedback_embedding(
        self,
        feedback_id: Union[int, str],
        feedback_text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store feedback text embedding and metadata in Qdrant.
        
        Args:
            feedback_id: Unique identifier for the feedback
            feedback_text: The text to generate an embedding for
            metadata: Additional metadata to store with the embedding
            
        Returns:
            bool: Success status
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(feedback_text)
            
            # Prepare payload with metadata
            payload = {
                "feedback_id": str(feedback_id),
                "text": feedback_text[:1000],  # Truncate text for storage
                **metadata
            }
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    qdrant_models.PointStruct(
                        id=feedback_id,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"Successfully stored embedding for feedback ID: {feedback_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing feedback embedding: {str(e)}")
            return False
    
    def batch_store_feedback_embeddings(
        self,
        feedback_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store multiple feedback embeddings in a batch operation.
        
        Args:
            feedback_data: List of dictionaries containing:
                - feedback_id: Unique identifier for the feedback
                - feedback_text: The text to generate an embedding for
                - metadata: Additional metadata to store with the embedding
                
        Returns:
            Dict with success count and failed IDs
        """
        points = []
        success_count = 0
        failed_ids = []
        
        for item in feedback_data:
            try:
                feedback_id = item.get('feedback_id')
                feedback_text = item.get('feedback_text', '')
                metadata = item.get('metadata', {})
                
                # Generate embedding
                embedding = self.generate_embedding(feedback_text)
                
                # Prepare payload with metadata
                payload = {
                    "feedback_id": str(feedback_id),
                    "text": feedback_text[:1000],  # Truncate text for storage
                    **metadata
                }
                
                points.append(
                    qdrant_models.PointStruct(
                        id=feedback_id,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing feedback ID {item.get('feedback_id')}: {str(e)}")
                failed_ids.append(item.get('feedback_id'))
        
        if points:
            try:
                # Store batch in Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Successfully stored {success_count} embeddings in batch")
            except Exception as e:
                logger.error(f"Error storing batch embeddings: {str(e)}")
                # If batch insert fails, all points are considered failed
                failed_ids = [item.get('feedback_id') for item in feedback_data]
                success_count = 0
        
        return {
            "success_count": success_count,
            "failed_ids": failed_ids
        }
    
    def semantic_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using a text query.
        
        Args:
            query_text: The query text to search for
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of matched documents with metadata and similarity scores
        """
        try:
            # Generate embedding for the query
            query_vector = self.generate_embedding(query_text)
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "feedback_id": result.payload.get("feedback_id"),
                    "text": result.payload.get("text"),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["feedback_id", "text"]}
                })
            
            logger.info(f"Semantic search for '{query_text}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            return []

# Function to get a pre-configured instance of the semantic processor
def get_semantic_processor(
    model_name: str = "all-MiniLM-L6-v2",
    qdrant_host: str = None,
    qdrant_port: int = None,
    collection_name: str = "feedback_embeddings"
) -> SemanticProcessor:
    """
    Get a pre-configured instance of the semantic processor.
    
    Args:
        model_name: Name of the SentenceTransformer model to use
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
        collection_name: Name of the Qdrant collection to use
        
    Returns:
        SemanticProcessor: Configured semantic processor instance
    """
    return SemanticProcessor(
        model_name=model_name,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        collection_name=collection_name
    )
