"""
Amazon Neptune graph database loader for special education feedback system.

This module handles:
1. Connecting to Amazon Neptune
2. Creating nodes for Students, Teachers, and Categories
3. Creating edges to represent relationships between nodes
4. Loading feedback data into the graph database
"""
import os
import uuid
import json
from typing import Dict, List, Any, Optional, Union
from gremlin_python.driver import client
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P, Cardinality
from utils.logger import get_logger

logger = get_logger(__name__)

class NeptuneLoader:
    """
    Handles loading data into Amazon Neptune graph database.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        port: Optional[int] = None,
        use_iam_auth: bool = True,
        region: Optional[str] = None
    ):
        """
        Initialize the Neptune loader.
        
        Args:
            endpoint: Neptune endpoint (defaults to environment variable)
            port: Neptune port (defaults to environment variable or 8182)
            use_iam_auth: Whether to use IAM authentication
            region: AWS region for IAM authentication
        """
        self.endpoint = endpoint or os.environ.get("NEPTUNE_ENDPOINT")
        self.port = port or int(os.environ.get("NEPTUNE_PORT", 8182))
        self.use_iam_auth = use_iam_auth
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.gremlin_client = None
        self.g = None
        
        if not self.endpoint:
            raise ValueError("Neptune endpoint not provided and NEPTUNE_ENDPOINT environment variable not set")
        
        self.connection_string = f"wss://{self.endpoint}:{self.port}/gremlin"
        
    def connect(self) -> bool:
        """
        Establish connection to Neptune.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.use_iam_auth:
                # Configure IAM auth
                from aws_requests_auth.aws_auth import AWSRequestsAuth
                from gremlin_python.driver.aiohttp.transport import AiohttpTransport
                import boto3
                
                session = boto3.Session(region_name=self.region)
                credentials = session.get_credentials()
                
                auth = AWSRequestsAuth(
                    aws_access_key=credentials.access_key,
                    aws_secret_access_key=credentials.secret_key,
                    aws_token=credentials.token,
                    aws_host=self.endpoint,
                    aws_region=self.region,
                    aws_service='neptune-db'
                )
                
                # Create connection with IAM auth
                connection = DriverRemoteConnection(
                    self.connection_string,
                    'g',
                    transport_factory=lambda: AiohttpTransport(auth=auth)
                )
            else:
                # Create connection without IAM auth
                connection = DriverRemoteConnection(self.connection_string, 'g')
            
            # Create traversal source
            self.g = traversal().withRemote(connection)
            
            # Test connection
            self.g.V().limit(1).count().next()
            
            logger.info(f"Successfully connected to Neptune at {self.endpoint}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Neptune: {str(e)}")
            return False
    
    def add_student(
        self,
        student_id: str,
        properties: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add a Student node to the graph.
        
        Args:
            student_id: Unique identifier for the student
            properties: Additional properties for the student node
            
        Returns:
            Optional[str]: Vertex ID if successful, None otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Check if student already exists
            existing = self.g.V().hasLabel('Student').has('student_id', student_id).count().next()
            
            if existing > 0:
                logger.info(f"Student with ID {student_id} already exists, retrieving vertex")
                vertex_id = self.g.V().hasLabel('Student').has('student_id', student_id).id().next()
                return vertex_id
            
            # Add student vertex
            vertex = self.g.addV('Student').property(T.id, str(uuid.uuid4()))
            
            # Add student_id as a property
            vertex = vertex.property('student_id', student_id)
            
            # Add additional properties
            for key, value in properties.items():
                if value is not None:
                    vertex = vertex.property(key, value)
            
            # Execute and get the vertex ID
            vertex_id = vertex.id().next()
            
            logger.info(f"Added Student node with ID {vertex_id}")
            return vertex_id
            
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            return None
    
    def add_teacher(
        self,
        teacher_name: str,
        properties: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add a Teacher node to the graph.
        
        Args:
            teacher_name: Name of the teacher
            properties: Additional properties for the teacher node
            
        Returns:
            Optional[str]: Vertex ID if successful, None otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Check if teacher already exists
            existing = self.g.V().hasLabel('Teacher').has('name', teacher_name).count().next()
            
            if existing > 0:
                logger.info(f"Teacher with name {teacher_name} already exists, retrieving vertex")
                vertex_id = self.g.V().hasLabel('Teacher').has('name', teacher_name).id().next()
                return vertex_id
            
            # Add teacher vertex
            vertex = self.g.addV('Teacher').property(T.id, str(uuid.uuid4()))
            
            # Add name as a property
            vertex = vertex.property('name', teacher_name)
            
            # Add additional properties
            for key, value in properties.items():
                if value is not None:
                    vertex = vertex.property(key, value)
            
            # Execute and get the vertex ID
            vertex_id = vertex.id().next()
            
            logger.info(f"Added Teacher node with ID {vertex_id}")
            return vertex_id
            
        except Exception as e:
            logger.error(f"Error adding teacher: {str(e)}")
            return None
    
    def add_category(
        self,
        category_name: str,
        properties: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add a Category node to the graph.
        
        Args:
            category_name: Name of the category
            properties: Additional properties for the category node
            
        Returns:
            Optional[str]: Vertex ID if successful, None otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Check if category already exists
            existing = self.g.V().hasLabel('Category').has('name', category_name).count().next()
            
            if existing > 0:
                logger.info(f"Category with name {category_name} already exists, retrieving vertex")
                vertex_id = self.g.V().hasLabel('Category').has('name', category_name).id().next()
                return vertex_id
            
            # Add category vertex
            vertex = self.g.addV('Category').property(T.id, str(uuid.uuid4()))
            
            # Add name as a property
            vertex = vertex.property('name', category_name)
            
            # Add additional properties
            for key, value in properties.items():
                if value is not None:
                    vertex = vertex.property(key, value)
            
            # Execute and get the vertex ID
            vertex_id = vertex.id().next()
            
            logger.info(f"Added Category node with ID {vertex_id}")
            return vertex_id
            
        except Exception as e:
            logger.error(f"Error adding category: {str(e)}")
            return None
    
    def add_feedback(
        self,
        feedback_id: Union[int, str],
        rating: int,
        open_feedback: Optional[str] = None,
        properties: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add a Feedback node to the graph.
        
        Args:
            feedback_id: Unique identifier for the feedback
            rating: Numerical rating
            open_feedback: Open-ended feedback text
            properties: Additional properties for the feedback node
            
        Returns:
            Optional[str]: Vertex ID if successful, None otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Check if feedback already exists
            existing = self.g.V().hasLabel('Feedback').has('feedback_id', str(feedback_id)).count().next()
            
            if existing > 0:
                logger.info(f"Feedback with ID {feedback_id} already exists, retrieving vertex")
                vertex_id = self.g.V().hasLabel('Feedback').has('feedback_id', str(feedback_id)).id().next()
                return vertex_id
            
            # Add feedback vertex
            vertex = self.g.addV('Feedback').property(T.id, str(uuid.uuid4()))
            
            # Add basic properties
            vertex = vertex.property('feedback_id', str(feedback_id))
            vertex = vertex.property('rating', rating)
            
            if open_feedback:
                vertex = vertex.property('open_feedback', open_feedback)
            
            # Add additional properties
            for key, value in properties.items():
                if value is not None:
                    vertex = vertex.property(key, value)
            
            # Execute and get the vertex ID
            vertex_id = vertex.id().next()
            
            logger.info(f"Added Feedback node with ID {vertex_id}")
            return vertex_id
            
        except Exception as e:
            logger.error(f"Error adding feedback: {str(e)}")
            return None
    
    def create_student_submits_feedback_edge(
        self,
        student_vertex_id: str,
        feedback_vertex_id: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create an edge representing that a student submitted feedback.
        
        Args:
            student_vertex_id: Vertex ID of the student
            feedback_vertex_id: Vertex ID of the feedback
            properties: Additional properties for the edge
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Create edge
            edge = self.g.V(student_vertex_id).addE('SUBMITS').to(__.V(feedback_vertex_id))
            
            # Add properties to edge
            for key, value in properties.items():
                if value is not None:
                    edge = edge.property(key, value)
            
            # Execute
            edge.next()
            
            logger.info(f"Created SUBMITS edge from Student {student_vertex_id} to Feedback {feedback_vertex_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating SUBMITS edge: {str(e)}")
            return False
    
    def create_student_assigned_to_teacher_edge(
        self,
        student_vertex_id: str,
        teacher_vertex_id: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create an edge representing that a student is assigned to a teacher.
        
        Args:
            student_vertex_id: Vertex ID of the student
            teacher_vertex_id: Vertex ID of the teacher
            properties: Additional properties for the edge
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Create edge
            edge = self.g.V(student_vertex_id).addE('ASSIGNED_TO').to(__.V(teacher_vertex_id))
            
            # Add properties to edge
            for key, value in properties.items():
                if value is not None:
                    edge = edge.property(key, value)
            
            # Execute
            edge.next()
            
            logger.info(f"Created ASSIGNED_TO edge from Student {student_vertex_id} to Teacher {teacher_vertex_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating ASSIGNED_TO edge: {str(e)}")
            return False
    
    def create_feedback_related_to_category_edge(
        self,
        feedback_vertex_id: str,
        category_vertex_id: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create an edge representing that feedback is related to a category.
        
        Args:
            feedback_vertex_id: Vertex ID of the feedback
            category_vertex_id: Vertex ID of the category
            properties: Additional properties for the edge
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            # Create edge
            edge = self.g.V(feedback_vertex_id).addE('RELATED_TO').to(__.V(category_vertex_id))
            
            # Add properties to edge
            for key, value in properties.items():
                if value is not None:
                    edge = edge.property(key, value)
            
            # Execute
            edge.next()
            
            logger.info(f"Created RELATED_TO edge from Feedback {feedback_vertex_id} to Category {category_vertex_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating RELATED_TO edge: {str(e)}")
            return False
    
    def load_feedback_into_graph(
        self,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load feedback data into the graph, creating all necessary nodes and edges.
        
        Args:
            feedback_data: Dictionary containing feedback data:
                - feedback_id: Unique identifier for the feedback
                - student_id: Identifier for the student
                - teacher_name: Name of the teacher
                - category: Category of the feedback
                - rating: Numerical rating
                - open_feedback: Open-ended feedback text
                - additional properties for any of the nodes or edges
                
        Returns:
            Dict with status and created vertex IDs
        """
        try:
            # Extract basic data
            feedback_id = feedback_data.get('feedback_id')
            student_id = feedback_data.get('student_id')
            teacher_name = feedback_data.get('teacher_name')
            category_name = feedback_data.get('category')
            rating = feedback_data.get('rating')
            open_feedback = feedback_data.get('open_feedback')
            
            # Validate required fields
            if not all([feedback_id, student_id, teacher_name, category_name, rating]):
                missing = []
                if not feedback_id: missing.append('feedback_id')
                if not student_id: missing.append('student_id')
                if not teacher_name: missing.append('teacher_name')
                if not category_name: missing.append('category')
                if not rating: missing.append('rating')
                
                return {
                    'status': 'error',
                    'message': f"Missing required fields: {', '.join(missing)}"
                }
            
            # Create nodes
            student_vertex_id = self.add_student(student_id)
            teacher_vertex_id = self.add_teacher(teacher_name)
            category_vertex_id = self.add_category(category_name)
            feedback_vertex_id = self.add_feedback(
                feedback_id, 
                rating, 
                open_feedback
            )
            
            # Create edges
            self.create_student_submits_feedback_edge(
                student_vertex_id, 
                feedback_vertex_id
            )
            
            self.create_student_assigned_to_teacher_edge(
                student_vertex_id, 
                teacher_vertex_id
            )
            
            self.create_feedback_related_to_category_edge(
                feedback_vertex_id, 
                category_vertex_id
            )
            
            return {
                'status': 'success',
                'student_vertex_id': student_vertex_id,
                'teacher_vertex_id': teacher_vertex_id,
                'category_vertex_id': category_vertex_id,
                'feedback_vertex_id': feedback_vertex_id
            }
            
        except Exception as e:
            logger.error(f"Error loading feedback into graph: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def batch_load_feedback(
        self,
        feedback_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Load multiple feedback items into the graph in batch.
        
        Args:
            feedback_data_list: List of feedback data dictionaries
                
        Returns:
            Dict with success count and failed items
        """
        success_count = 0
        failed_items = []
        
        for feedback_data in feedback_data_list:
            result = self.load_feedback_into_graph(feedback_data)
            
            if result.get('status') == 'success':
                success_count += 1
            else:
                failed_items.append({
                    'feedback_data': feedback_data,
                    'error': result.get('message')
                })
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_items),
            'failed_items': failed_items
        }

# Example usage function
def load_feedback_example():
    """Example of how to use the NeptuneLoader."""
    loader = NeptuneLoader(
        endpoint=os.environ.get("NEPTUNE_ENDPOINT"),
        port=int(os.environ.get("NEPTUNE_PORT", 8182)),
        use_iam_auth=True
    )
    
    if loader.connect():
        # Load a single feedback
        result = loader.load_feedback_into_graph({
            'feedback_id': '12345',
            'student_id': 'S789',
            'teacher_name': 'Ms. Johnson',
            'category': 'reading',
            'rating': 4,
            'open_feedback': 'Shows great improvement in phonemic awareness'
        })
        
        print(f"Load result: {json.dumps(result, indent=2)}")
        
        # Or batch load multiple feedback items
        batch_result = loader.batch_load_feedback([
            {
                'feedback_id': '12346',
                'student_id': 'S789',
                'teacher_name': 'Ms. Johnson',
                'category': 'math',
                'rating': 3,
                'open_feedback': 'Needs more practice with fractions'
            },
            {
                'feedback_id': '12347',
                'student_id': 'S790',
                'teacher_name': 'Mr. Smith',
                'category': 'behavior',
                'rating': 5,
                'open_feedback': 'Very focused during independent work time'
            }
        ])
        
        print(f"Batch load result: {json.dumps(batch_result, indent=2)}")

# Can be run directly for testing
if __name__ == "__main__":
    load_feedback_example()
