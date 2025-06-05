import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class DynamoDBClient:
    """Client for interacting with Amazon DynamoDB."""
    
    def __init__(self, region: str = None, endpoint_url: str = None):
        """
        Initialize the DynamoDB client.
        
        Args:
            region: AWS region
            endpoint_url: Custom endpoint URL (for local DynamoDB)
        """
        self.region = region or os.environ.get('DYNAMODB_REGION', 'us-east-1')
        self.endpoint_url = endpoint_url or os.environ.get('DYNAMODB_ENDPOINT')
        self.client = None
        self.resource = None
        
    def connect(self):
        """Establish connection to DynamoDB."""
        try:
            kwargs = {'region_name': self.region}
            if self.endpoint_url:
                kwargs['endpoint_url'] = self.endpoint_url
                
            self.client = boto3.client('dynamodb', **kwargs)
            self.resource = boto3.resource('dynamodb', **kwargs)
            
            logger.info(f"Connected to DynamoDB in {self.region}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {str(e)}")
            return False
    
    def create_table(self, 
                    table_name: str,
                    key_schema: List[Dict[str, str]],
                    attribute_definitions: List[Dict[str, str]],
                    provisioned_throughput: Dict[str, int] = None) -> bool:
        """
        Create a new DynamoDB table.
        
        Args:
            table_name: Name of the table
            key_schema: Key schema for the table
            attribute_definitions: Attribute definitions
            provisioned_throughput: Provisioned throughput settings
            
        Returns:
            bool: Success status
        """
        if not self.client:
            self.connect()
            
        # Default provisioned throughput if not provided
        if provisioned_throughput is None:
            provisioned_throughput = {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
            
        try:
            response = self.client.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput
            )
            
            logger.info(f"Created DynamoDB table: {table_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Table {table_name} already exists")
                return True
            else:
                logger.error(f"Error creating table {table_name}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
            return False
    
    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """
        Insert an item into a DynamoDB table.
        
        Args:
            table_name: Name of the table
            item: Item to insert
            
        Returns:
            bool: Success status
        """
        if not self.resource:
            self.connect()
            
        try:
            table = self.resource.Table(table_name)
            response = table.put_item(Item=item)
            
            logger.info(f"Added item to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding item to {table_name}: {str(e)}")
            return False
    
    def get_item(self, 
                table_name: str, 
                key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key: Primary key of the item to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The item if found, None otherwise
        """
        if not self.resource:
            self.connect()
            
        try:
            table = self.resource.Table(table_name)
            response = table.get_item(Key=key)
            
            if 'Item' in response:
                return response['Item']
            else:
                logger.info(f"No item found in {table_name} with key {key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting item from {table_name}: {str(e)}")
            return None
    
    def query(self, 
             table_name: str, 
             key_condition_expression,
             expression_attribute_values: Dict[str, Any] = None,
             index_name: str = None) -> List[Dict[str, Any]]:
        """
        Query items from a DynamoDB table.
        
        Args:
            table_name: Name of the table
            key_condition_expression: Key condition expression
            expression_attribute_values: Expression attribute values
            index_name: Optional index name to query
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        if not self.resource:
            self.connect()
            
        try:
            table = self.resource.Table(table_name)
            
            kwargs = {
                'KeyConditionExpression': key_condition_expression,
                'ExpressionAttributeValues': expression_attribute_values
            }
            
            if index_name:
                kwargs['IndexName'] = index_name
                
            response = table.query(**kwargs)
            
            items = response.get('Items', [])
            logger.info(f"Query returned {len(items)} items from {table_name}")
            return items
            
        except Exception as e:
            logger.error(f"Error querying {table_name}: {str(e)}")
            return []
