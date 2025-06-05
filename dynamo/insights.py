"""
DynamoDB insights module for special education feedback system.

This module handles inserting and retrieving insight records
generated from processed feedback in DynamoDB.
"""
import os
import uuid
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from utils.logger import get_logger

logger = get_logger(__name__)

class InsightsManager:
    """
    Manages insight records in DynamoDB for the special education feedback system.
    """
    
    def __init__(
        self,
        table_name: str = "sped_insights",
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize the insights manager.
        
        Args:
            table_name: Name of the DynamoDB table for insights
            region: AWS region (defaults to environment variable)
            endpoint_url: Custom endpoint URL for DynamoDB (for local testing)
        """
        self.table_name = table_name
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.endpoint_url = endpoint_url or os.environ.get("DYNAMODB_ENDPOINT")
        
        # Initialize the DynamoDB resource
        self._init_dynamodb()
        
    def _init_dynamodb(self):
        """Initialize the DynamoDB resource and ensure table exists."""
        try:
            # Create DynamoDB resource
            kwargs = {'region_name': self.region}
            if self.endpoint_url:
                kwargs['endpoint_url'] = self.endpoint_url
                
            self.dynamodb = boto3.resource('dynamodb', **kwargs)
            
            # Try to get the table
            try:
                self.table = self.dynamodb.Table(self.table_name)
                # Check if table exists by accessing its creation date
                self.table.creation_date_time
                logger.info(f"Connected to DynamoDB table: {self.table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"Table {self.table_name} does not exist, creating it")
                    self._create_insights_table()
                else:
                    logger.error(f"Error checking table: {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"Error initializing DynamoDB: {str(e)}")
            raise
    
    def _create_insights_table(self):
        """Create the insights table if it doesn't exist."""
        try:
            # Create the insights table
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'insight_id', 'KeyType': 'HASH'},  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'insight_id', 'AttributeType': 'S'},
                    {'AttributeName': 'student_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'N'},
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'student_id-created_at-index',
                        'KeySchema': [
                            {'AttributeName': 'student_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be created
            self.table.meta.client.get_waiter('table_exists').wait(
                TableName=self.table_name
            )
            
            logger.info(f"Created DynamoDB table: {self.table_name}")
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise
    
    def insert_insight(
        self, 
        student_id: str,
        theme: str, 
        sentiment: str, 
        summary: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Insert an insight record into DynamoDB.
        
        Args:
            student_id: ID of the student the insight relates to
            theme: Theme of the insight (e.g., 'accessibility', 'learning_style')
            sentiment: Sentiment of the insight (e.g., 'positive', 'negative', 'neutral')
            summary: Text summary of the insight
            additional_data: Any additional data to store with the insight
            
        Returns:
            Dict with status and insight_id
        """
        try:
            # Generate a unique insight ID
            insight_id = str(uuid.uuid4())
            
            # Get current timestamp
            current_time = int(time.time())
            
            # Prepare the item to insert
            item = {
                'insight_id': insight_id,
                'student_id': student_id,
                'theme': theme,
                'sentiment': sentiment,
                'summary': summary,
                'created_at': current_time,
                'created_date': datetime.utcnow().isoformat()
            }
            
            # Add any additional data
            if additional_data:
                item.update(additional_data)
            
            # Insert the item into DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Inserted insight record with ID: {insight_id}")
            
            return {
                'status': 'success',
                'insight_id': insight_id
            }
            
        except Exception as e:
            logger.error(f"Error inserting insight: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def batch_insert_insights(
        self,
        insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Insert multiple insight records in batch.
        
        Args:
            insights: List of insight records, each should contain:
                - student_id: ID of the student
                - theme: Theme of the insight
                - sentiment: Sentiment of the insight
                - summary: Text summary of the insight
                - additional fields as needed
                
        Returns:
            Dict with success count and failed items
        """
        try:
            if not insights:
                return {
                    'status': 'success',
                    'message': 'No insights to insert',
                    'success_count': 0,
                    'failed_count': 0
                }
            
            success_count = 0
            failed_items = []
            
            # DynamoDB can only process 25 items in a single batch write
            # Split the insights into chunks of 25
            chunk_size = 25
            for i in range(0, len(insights), chunk_size):
                chunk = insights[i:i + chunk_size]
                
                # Prepare the batch write request
                batch_items = []
                for insight in chunk:
                    # Validate required fields
                    if not all(k in insight for k in ['student_id', 'theme', 'sentiment', 'summary']):
                        failed_items.append({
                            'item': insight,
                            'error': 'Missing required fields'
                        })
                        continue
                    
                    # Generate a unique insight ID
                    insight_id = str(uuid.uuid4())
                    
                    # Get current timestamp
                    current_time = int(time.time())
                    
                    # Prepare the item to insert
                    item = {
                        'insight_id': insight_id,
                        'student_id': insight['student_id'],
                        'theme': insight['theme'],
                        'sentiment': insight['sentiment'],
                        'summary': insight['summary'],
                        'created_at': current_time,
                        'created_date': datetime.utcnow().isoformat()
                    }
                    
                    # Add any additional data
                    for k, v in insight.items():
                        if k not in ['student_id', 'theme', 'sentiment', 'summary']:
                            item[k] = v
                    
                    batch_items.append({
                        'PutRequest': {
                            'Item': item
                        }
                    })
                
                # Execute the batch write
                if batch_items:
                    try:
                        response = self.dynamodb.batch_write_item(
                            RequestItems={
                                self.table_name: batch_items
                            }
                        )
                        
                        # Check for unprocessed items
                        unprocessed = response.get('UnprocessedItems', {}).get(self.table_name, [])
                        if unprocessed:
                            for item in unprocessed:
                                failed_items.append({
                                    'item': item['PutRequest']['Item'],
                                    'error': 'Unprocessed in batch write'
                                })
                        
                        success_count += (len(batch_items) - len(unprocessed))
                        
                    except Exception as e:
                        logger.error(f"Error in batch write: {str(e)}")
                        for item in batch_items:
                            failed_items.append({
                                'item': item['PutRequest']['Item'],
                                'error': str(e)
                            })
            
            return {
                'status': 'success',
                'success_count': success_count,
                'failed_count': len(failed_items),
                'failed_items': failed_items if failed_items else None
            }
            
        except Exception as e:
            logger.error(f"Error in batch insert: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_insights_by_student(
        self,
        student_id: str,
        limit: int = 50,
        start_date: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get insights for a specific student.
        
        Args:
            student_id: ID of the student
            limit: Maximum number of insights to return
            start_date: Optional timestamp to start from
            
        Returns:
            Dict with status and insights
        """
        try:
            # Build query parameters
            query_params = {
                'IndexName': 'student_id-created_at-index',
                'KeyConditionExpression': Key('student_id').eq(student_id),
                'Limit': limit,
                'ScanIndexForward': False  # Sort in descending order (newest first)
            }
            
            if start_date:
                query_params['KeyConditionExpression'] = Key('student_id').eq(student_id) & \
                                                       Key('created_at').gt(start_date)
            
            # Execute the query
            response = self.table.query(**query_params)
            
            insights = response.get('Items', [])
            
            return {
                'status': 'success',
                'count': len(insights),
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error getting insights for student {student_id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

# Example usage
def insert_insight_example():
    """Example demonstrating how to use the InsightsManager."""
    # Initialize the insights manager
    insights_manager = InsightsManager()
    
    # Insert a single insight
    result = insights_manager.insert_insight(
        student_id="S001",
        theme="accessibility",
        sentiment="negative",
        summary="Student reports difficulty using screen readers with the current materials",
        additional_data={
            "source_feedback_ids": ["F123", "F456"],
            "priority": "high",
            "suggested_action": "Review digital materials for screen reader compatibility"
        }
    )
    
    print(f"Insert result: {json.dumps(result, indent=2)}")
    
    # Insert multiple insights in batch
    batch_result = insights_manager.batch_insert_insights([
        {
            "student_id": "S001",
            "theme": "learning_style",
            "sentiment": "positive",
            "summary": "Student responds well to visual learning materials",
            "confidence": 0.87
        },
        {
            "student_id": "S002",
            "theme": "participation",
            "sentiment": "neutral",
            "summary": "Participation varies depending on subject matter",
            "subjects": ["math", "science"]
        }
    ])
    
    print(f"Batch insert result: {json.dumps(batch_result, indent=2)}")
    
    # Retrieve insights for a student
    get_result = insights_manager.get_insights_by_student("S001")
    
    print(f"Get insights result: {json.dumps(get_result, indent=2)}")

# Can be run directly for testing
if __name__ == "__main__":
    insert_insight_example()
