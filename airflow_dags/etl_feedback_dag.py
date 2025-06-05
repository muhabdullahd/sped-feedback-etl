"""
Airflow DAG for ETL processing of special education feedback data.

This DAG:
1. Connects to MySQL database
2. Pulls feedback marked as "unprocessed"
3. Cleans the text (lowercase, remove punctuation)
4. Writes cleaned feedback to a temporary CSV
5. Marks feedback as "processed"
"""
from datetime import datetime, timedelta
import os
import pandas as pd
import re
import string
from sqlalchemy import create_engine, text
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Define default arguments for the DAG
default_args = {
    'owner': 'sped_feedback',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'sped_feedback_etl',
    default_args=default_args,
    description='ETL process for special education feedback data',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    catchup=False
)

# Define the database connection parameters
# These should ideally come from environment variables or Airflow connections
def get_db_connection_string():
    """Get the database connection string from environment variables."""
    db_user = os.environ.get('MYSQL_USER', 'root')
    db_password = os.environ.get('MYSQL_PASSWORD', 'password')
    db_host = os.environ.get('MYSQL_HOST', 'localhost')
    db_port = os.environ.get('MYSQL_PORT', '3306')
    db_name = os.environ.get('MYSQL_DATABASE', 'sped_feedback')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def clean_text(text):
    """
    Clean text by converting to lowercase and removing punctuation.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_unprocessed_feedback(**kwargs):
    """
    Extract unprocessed feedback from the MySQL database.
    
    Returns:
        dict: Dictionary containing information about the extraction process
    """
    # Create database connection
    connection_string = get_db_connection_string()
    engine = create_engine(connection_string)
    
    # Query for unprocessed feedback
    query = "SELECT * FROM feedback WHERE processed = 0"
    
    try:
        # Read data into a pandas DataFrame
        df = pd.read_sql(query, engine)
        
        # Store the DataFrame in XCom for the next task
        num_records = len(df)
        if num_records > 0:
            # Save dataframe to a temp file for next task
            temp_path = "/tmp/unprocessed_feedback.parquet"
            df.to_parquet(temp_path, index=False)
            
            print(f"Extracted {num_records} unprocessed feedback records")
            return {
                "status": "success",
                "record_count": num_records,
                "temp_file_path": temp_path
            }
        else:
            print("No unprocessed feedback records found")
            return {
                "status": "success",
                "record_count": 0,
                "temp_file_path": None
            }
            
    except Exception as e:
        print(f"Error extracting feedback: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def transform_feedback_data(**kwargs):
    """
    Transform and clean the feedback text.
    
    Returns:
        dict: Dictionary containing information about the transformation process
    """
    ti = kwargs['ti']
    
    # Get the extraction result from the previous task
    extraction_result = ti.xcom_pull(task_ids='extract_unprocessed_feedback')
    
    if extraction_result["status"] == "error":
        print(f"Error in previous task: {extraction_result['message']}")
        return {
            "status": "error",
            "message": "Error in extraction task"
        }
    
    if extraction_result["record_count"] == 0:
        print("No records to transform")
        return {
            "status": "success",
            "record_count": 0,
            "temp_file_path": None
        }
    
    try:
        # Load the DataFrame from the temporary file
        temp_path = extraction_result["temp_file_path"]
        df = pd.read_parquet(temp_path)
        
        # Clean the open_feedback text
        df['cleaned_feedback'] = df['open_feedback'].apply(clean_text)
        
        # Save the transformed data to a new temporary file
        transformed_path = "/tmp/transformed_feedback.csv"
        
        # Select needed columns for CSV export
        csv_df = df[['id', 'student_id', 'teacher_name', 'rating', 
                     'category', 'open_feedback', 'cleaned_feedback']]
        
        # Save to CSV
        csv_df.to_csv(transformed_path, index=False)
        
        print(f"Transformed {len(df)} feedback records and saved to {transformed_path}")
        return {
            "status": "success",
            "record_count": len(df),
            "temp_file_path": transformed_path,
            "original_file_path": temp_path,
            "feedback_ids": df['id'].tolist()
        }
        
    except Exception as e:
        print(f"Error transforming feedback: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def mark_feedback_processed(**kwargs):
    """
    Mark feedback as processed in the database.
    
    Returns:
        dict: Dictionary containing information about the update process
    """
    ti = kwargs['ti']
    
    # Get the transformation result from the previous task
    transform_result = ti.xcom_pull(task_ids='transform_feedback')
    
    if transform_result["status"] == "error":
        print(f"Error in previous task: {transform_result['message']}")
        return {
            "status": "error",
            "message": "Error in transformation task"
        }
    
    if transform_result["record_count"] == 0:
        print("No records to update")
        return {
            "status": "success",
            "updated_count": 0
        }
    
    try:
        # Get the list of feedback IDs to mark as processed
        feedback_ids = transform_result["feedback_ids"]
        
        # Create database connection
        connection_string = get_db_connection_string()
        engine = create_engine(connection_string)
        
        # Update the records to mark them as processed
        with engine.connect() as connection:
            # Construct the query to update all IDs at once
            id_list = ', '.join(map(str, feedback_ids))
            update_query = text(f"UPDATE feedback SET processed = 1 WHERE id IN ({id_list})")
            result = connection.execute(update_query)
            connection.commit()
            
            updated_count = result.rowcount
            
        print(f"Marked {updated_count} feedback records as processed")
        return {
            "status": "success",
            "updated_count": updated_count
        }
        
    except Exception as e:
        print(f"Error marking feedback as processed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# Define the tasks
extract_task = PythonOperator(
    task_id='extract_unprocessed_feedback',
    python_callable=extract_unprocessed_feedback,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_feedback',
    python_callable=transform_feedback_data,
    provide_context=True,
    dag=dag,
)

update_task = PythonOperator(
    task_id='mark_feedback_processed',
    python_callable=mark_feedback_processed,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
extract_task >> transform_task >> update_task
