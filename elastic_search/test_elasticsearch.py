#!/usr/bin/env python3
"""
Test script to verify Elasticsearch integration.
"""
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from elastic_search.client import ElasticsearchClient
from elastic_search.config import ElasticsearchConfig
from elastic_search.search import initialize_indices, index_feedback, search_feedback

def test_elasticsearch_connection():
    """Test basic Elasticsearch connection and operations."""
    print("Testing Elasticsearch connection...")
    
    # Create client
    client = ElasticsearchClient()
    
    # Test connection
    if client.connect():
        print("✅ Connected to Elasticsearch successfully")
    else:
        print("❌ Failed to connect to Elasticsearch")
        return False
    
    return True

def test_elasticsearch_operations():
    """Test Elasticsearch index creation and document operations."""
    print("\nTesting Elasticsearch operations...")
    
    # Initialize indices
    print("Initializing indices...")
    initialize_indices()
    print("✅ Indices initialized")
    
    # Create sample feedback data
    sample_feedback = {
        "id": "test-123",
        "student_id": "S12345",
        "teacher_name": "Jane Smith",
        "rating": 4,
        "category": "academics",
        "open_feedback": "The student has shown great improvement in reading comprehension. Needs more practice with math word problems.",
        "sentiment": "positive",
        "topics": ["reading", "math", "comprehension"],
        "entities": ["word problems"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Index the sample feedback
    print("Indexing sample feedback document...")
    if index_feedback(sample_feedback):
        print("✅ Sample feedback document indexed successfully")
    else:
        print("❌ Failed to index sample feedback document")
        return False
    
    # Wait for indexing to complete
    print("Waiting for document to be searchable...")
    import time
    time.sleep(2)
    
    # Search for the indexed document
    print("Searching for the indexed document...")
    search_results = search_feedback("reading comprehension")
    
    # Check if we got any results
    if search_results.get("hits") and len(search_results["hits"]) > 0:
        print("✅ Search returned results:")
        print(json.dumps(search_results["hits"][0], indent=2))
        return True
    else:
        print("❌ Search did not return any results")
        return False

def main():
    """Main test function."""
    print("=== Elasticsearch Integration Test ===\n")
    
    # Test connection
    if not test_elasticsearch_connection():
        print("\n❌ Elasticsearch connection test failed. Make sure Elasticsearch is running.")
        print("   Run './setup_elasticsearch.sh' to set up Elasticsearch.")
        return
    
    # Test operations
    if test_elasticsearch_operations():
        print("\n✅ All Elasticsearch tests passed!")
    else:
        print("\n❌ Some Elasticsearch tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
