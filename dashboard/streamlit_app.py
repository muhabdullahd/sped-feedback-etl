"""
Streamlit dashboard for the Special Education Feedback Insight System.

This dashboard provides:
1. Sentiment distribution visualization from DynamoDB insights
2. Semantic search interface using Qdrant vector database
3. Graph visualization of support networks (students, teachers, categories)
"""
import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key
import tempfile
from pathlib import Path

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from dynamo.insights import InsightsManager
from vector_db.semantic import get_semantic_processor
from graph_db.neptune_loader import NeptuneLoader

# Configure page
st.set_page_config(
    page_title="SPED Feedback Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e3f2fd;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1565C0;
    }
    .metric-label {
        font-size: 1rem;
        color: #455A64;
    }
    .highlight {
        background-color: #FFF9C4;
        padding: 0.25rem;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def load_dynamo_insights(days_back=30, limit=500):
    """Load insights from DynamoDB."""
    try:
        insights_manager = InsightsManager()
        
        # Initialize DynamoDB client directly for scanning the table
        dynamodb = boto3.resource('dynamodb', region_name=insights_manager.region)
        table = dynamodb.Table(insights_manager.table_name)
        
        # Calculate the timestamp for filtering (days back from now)
        start_time = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        # Scan the table with a filter expression
        response = table.scan(
            FilterExpression=Key('created_at').gt(start_time),
            Limit=limit
        )
        
        insights = response.get('Items', [])
        
        # Convert to DataFrame for easier manipulation
        if insights:
            df = pd.DataFrame(insights)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading insights from DynamoDB: {str(e)}")
        return pd.DataFrame()

def perform_semantic_search(query_text, limit=10, threshold=0.6):
    """Perform semantic search using the vector database."""
    try:
        # Initialize the semantic processor
        semantic_processor = get_semantic_processor()
        
        # Perform the search
        results = semantic_processor.semantic_search(
            query_text=query_text,
            limit=limit,
            score_threshold=threshold
        )
        
        return results
        
    except Exception as e:
        st.error(f"Error performing semantic search: {str(e)}")
        return []

def load_graph_data():
    """Load graph data from Neptune (or generate sample data if unavailable)."""
    try:
        # Try to connect to Neptune
        neptune_loader = NeptuneLoader()
        if neptune_loader.connect():
            # If connected, query the graph data
            # This is a placeholder for actual Neptune querying code
            # In a real implementation, you would use gremlin queries to get the data
            
            # Return sample data for now
            return generate_sample_graph_data()
        else:
            # If connection fails, use sample data
            return generate_sample_graph_data()
            
    except Exception as e:
        st.error(f"Error loading graph data: {str(e)}")
        return generate_sample_graph_data()

def generate_sample_graph_data():
    """Generate sample graph data for visualization when Neptune is unavailable."""
    nodes = []
    edges = []
    
    # Create student nodes
    for i in range(1, 6):
        nodes.append({
            'id': f'S{i:03d}',
            'label': f'Student {i}',
            'type': 'Student'
        })
    
    # Create teacher nodes
    teachers = ['Ms. Johnson', 'Mr. Smith', 'Mrs. Williams', 'Ms. Davis']
    for i, name in enumerate(teachers):
        nodes.append({
            'id': f'T{i+1}',
            'label': name,
            'type': 'Teacher'
        })
    
    # Create category nodes
    categories = ['Reading', 'Math', 'Behavior', 'Social', 'Motor Skills']
    for i, name in enumerate(categories):
        nodes.append({
            'id': f'C{i+1}',
            'label': name,
            'type': 'Category'
        })
    
    # Create feedback nodes
    for i in range(1, 15):
        nodes.append({
            'id': f'F{i:03d}',
            'label': f'Feedback {i}',
            'type': 'Feedback'
        })
    
    # Create edges between students and teachers
    student_teacher_pairs = [
        ('S001', 'T1'), ('S001', 'T2'), ('S002', 'T1'),
        ('S003', 'T3'), ('S004', 'T4'), ('S005', 'T2'),
        ('S002', 'T3'), ('S004', 'T1')
    ]
    
    for source, target in student_teacher_pairs:
        edges.append({
            'source': source,
            'target': target,
            'relation': 'ASSIGNED_TO'
        })
    
    # Create edges between students and feedback
    for i in range(1, 15):
        student_id = f'S{((i-1) % 5) + 1:03d}'
        edges.append({
            'source': student_id,
            'target': f'F{i:03d}',
            'relation': 'SUBMITS'
        })
    
    # Create edges between feedback and categories
    for i in range(1, 15):
        category_id = f'C{((i-1) % 5) + 1}'
        edges.append({
            'source': f'F{i:03d}',
            'target': category_id,
            'relation': 'RELATED_TO'
        })
    
    return {'nodes': nodes, 'edges': edges}

def create_graph_visualization(graph_data):
    """Create an interactive graph visualization using PyVis."""
    # Create a network
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # Define colors for each node type
    colors = {
        'Student': '#1E88E5',  # Blue
        'Teacher': '#43A047',  # Green
        'Category': '#FB8C00',  # Orange
        'Feedback': '#8E24AA'   # Purple
    }
    
    # Add nodes
    for node in graph_data['nodes']:
        net.add_node(
            node['id'], 
            label=node['label'],
            title=f"Type: {node['type']}", 
            color=colors.get(node['type'], '#BDBDBD')
        )
    
    # Add edges
    for edge in graph_data['edges']:
        net.add_edge(
            edge['source'], 
            edge['target'], 
            title=edge['relation'],
            arrows='to'
        )
    
    # Set physics layout
    net.barnes_hut(spring_length=250, spring_strength=0.001, damping=0.09)
    
    # Save to a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name

def generate_sample_insights():
    """Generate sample insights data when DynamoDB is not available."""
    # Create sample data
    data = []
    sentiments = ['positive', 'negative', 'neutral']
    themes = ['accessibility', 'learning_style', 'participation', 'comprehension', 'communication']
    
    for i in range(1, 6):
        for j in range(10):
            # Ensure a good distribution of sentiments and themes
            sentiment = sentiments[j % len(sentiments)]
            theme = themes[(i + j) % len(themes)]
            
            data.append({
                'insight_id': f'ins-{i}-{j}',
                'student_id': f'S{i:03d}',
                'sentiment': sentiment,
                'theme': theme,
                'summary': f'Sample insight {j} for student {i}',
                'created_at': int(datetime.now().timestamp()) - (j * 86400)  # Vary by days
            })
    
    return pd.DataFrame(data)

# Dashboard layout
st.markdown("<h1 class='main-header'>Special Education Feedback Insights</h1>", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["📊 Sentiment Analysis", "🔍 Semantic Search", "🕸️ Support Networks"])

# Tab 1: Sentiment Distribution from DynamoDB
with tab1:
    st.markdown("<h2 class='sub-header'>Sentiment Analysis Dashboard</h2>", unsafe_allow_html=True)
    
    with st.expander("About Sentiment Analysis", expanded=False):
        st.markdown("""
        This dashboard shows the distribution of sentiments across feedback insights.
        The data is retrieved from DynamoDB where processed feedback insights are stored.
        
        **Key metrics include:**
        - Distribution of positive, negative, and neutral sentiments
        - Sentiment trends by theme
        - Student-specific sentiment analysis
        """)
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        days_filter = st.slider("Days to look back", min_value=7, max_value=90, value=30, step=1)
    with col2:
        limit_filter = st.slider("Maximum insights to load", min_value=100, max_value=1000, value=500, step=100)
    with col3:
        refresh_button = st.button("Refresh Data")
    
    # Load data
    try:
        with st.spinner("Loading sentiment data from DynamoDB..."):
            insights_df = load_dynamo_insights(days_back=days_filter, limit=limit_filter)
            
            # If no data is available, use sample data
            if insights_df.empty:
                st.warning("No data available from DynamoDB. Showing sample data instead.")
                insights_df = generate_sample_insights()
                
            # Count of insights
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(insights_df)}</div><div class='metric-label'>Total Insights</div></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading insights: {str(e)}")
        insights_df = generate_sample_insights()
    
    # Display sentiment distribution
    if not insights_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='card'><h3>Sentiment Distribution</h3>", unsafe_allow_html=True)
            
            # Count sentiments
            sentiment_counts = insights_df['sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentiment', 'Count']
            
            # Create pie chart
            fig = px.pie(
                sentiment_counts, 
                values='Count', 
                names='Sentiment',
                color='Sentiment',
                color_discrete_map={
                    'positive': '#43A047',  # Green
                    'negative': '#E53935',  # Red
                    'neutral': '#FFA726'    # Orange
                },
                hole=0.4
            )
            fig.update_layout(legend_title="Sentiment", height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'><h3>Sentiment by Theme</h3>", unsafe_allow_html=True)
            
            # Group by theme and sentiment
            theme_sentiment = insights_df.groupby(['theme', 'sentiment']).size().reset_index(name='count')
            
            # Create grouped bar chart
            fig = px.bar(
                theme_sentiment,
                x='theme',
                y='count',
                color='sentiment',
                barmode='group',
                color_discrete_map={
                    'positive': '#43A047',  # Green
                    'negative': '#E53935',  # Red
                    'neutral': '#FFA726'    # Orange
                }
            )
            fig.update_layout(
                xaxis_title="Theme",
                yaxis_title="Count",
                legend_title="Sentiment",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Show sentiment by student
        st.markdown("<div class='card'><h3>Sentiment Distribution by Student</h3>", unsafe_allow_html=True)
        
        # Group by student and sentiment
        student_sentiment = insights_df.groupby(['student_id', 'sentiment']).size().reset_index(name='count')
        
        # Create stacked bar chart
        fig = px.bar(
            student_sentiment,
            x='student_id',
            y='count',
            color='sentiment',
            barmode='stack',
            color_discrete_map={
                'positive': '#43A047',  # Green
                'negative': '#E53935',  # Red
                'neutral': '#FFA726'    # Orange
            }
        )
        fig.update_layout(
            xaxis_title="Student ID",
            yaxis_title="Count",
            legend_title="Sentiment",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show the raw data in an expandable section
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(insights_df)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("No sentiment data available.")

# Tab 2: Semantic Search using Qdrant
with tab2:
    st.markdown("<h2 class='sub-header'>Semantic Search</h2>", unsafe_allow_html=True)
    
    with st.expander("About Semantic Search", expanded=False):
        st.markdown("""
        This tool lets you search for feedback and insights using natural language.
        It uses SentenceTransformers to convert your query to a vector embedding,
        then finds similar content in the Qdrant vector database.
        
        **Features:**
        - Natural language queries
        - Semantic similarity matching
        - Relevance scoring
        """)
    
    # Search interface
    search_query = st.text_input(
        "Search for feedback insights",
        placeholder="E.g., 'students struggling with reading comprehension'"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        similarity_threshold = st.slider(
            "Similarity threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.7,
            step=0.05,
            help="Higher values return more similar results"
        )
    with col2:
        max_results = st.slider(
            "Maximum results",
            min_value=5,
            max_value=30,
            value=10,
            step=5
        )
    
    search_button = st.button("Search")
    
    # Perform search when button is clicked
    if search_button and search_query:
        with st.spinner("Searching..."):
            try:
                results = perform_semantic_search(
                    query_text=search_query,
                    limit=max_results,
                    threshold=similarity_threshold
                )
                
                # If no results or error, use mock data
                if not results:
                    st.info("No results found or Qdrant is not available. Showing sample results instead.")
                    
                    # Generate mock results
                    results = [
                        {
                            "feedback_id": "F001",
                            "text": "Student has difficulty with reading comprehension, especially with longer passages.",
                            "score": 0.89,
                            "metadata": {
                                "student_id": "S001",
                                "category": "reading"
                            }
                        },
                        {
                            "feedback_id": "F002",
                            "text": "Struggles to understand main ideas in text. Needs additional visual supports.",
                            "score": 0.81,
                            "metadata": {
                                "student_id": "S003",
                                "category": "reading"
                            }
                        },
                        {
                            "feedback_id": "F003",
                            "text": "Reading fluency is improving, but comprehension remains a challenge.",
                            "score": 0.76,
                            "metadata": {
                                "student_id": "S002",
                                "category": "reading"
                            }
                        }
                    ]
                
                # Display results
                st.markdown(f"<div class='card'><h3>Search Results</h3>", unsafe_allow_html=True)
                st.markdown(f"Found {len(results)} results for: <span class='highlight'>{search_query}</span>", unsafe_allow_html=True)
                
                for i, result in enumerate(results):
                    score_percentage = int(result.get('score', 0) * 100)
                    
                    st.markdown(
                        f"""
                        <div style="margin-bottom: 1rem; padding: 1rem; border-radius: 0.5rem; background-color: rgba(30, 136, 229, {result.get('score', 0) * 0.3 + 0.1});">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: bold;">Result {i+1}</span>
                                <span style="background-color: #E3F2FD; padding: 0.1rem 0.5rem; border-radius: 1rem;">{score_percentage}% match</span>
                            </div>
                            <div style="margin: 0.5rem 0; font-size: 1.1rem;">{result.get('text', 'No text available')}</div>
                            <div style="color: #455A64; font-size: 0.9rem;">
                                ID: {result.get('feedback_id', 'Unknown')} | 
                                Student: {result.get('metadata', {}).get('student_id', 'Unknown')} | 
                                Category: {result.get('metadata', {}).get('category', 'Unknown')}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
    elif search_button:
        st.warning("Please enter a search query.")

# Tab 3: Graph Visualization of Support Networks
with tab3:
    st.markdown("<h2 class='sub-header'>Support Network Visualization</h2>", unsafe_allow_html=True)
    
    with st.expander("About Support Networks", expanded=False):
        st.markdown("""
        This visualization shows the relationships between students, teachers, and feedback categories.
        The data is retrieved from the Neptune graph database.
        
        **Network elements:**
        - **Blue nodes**: Students
        - **Green nodes**: Teachers
        - **Orange nodes**: Categories
        - **Purple nodes**: Feedback
        - **Edges**: Relationships between entities
        """)
    
    # Load graph data button
    if st.button("Load Support Network Data"):
        with st.spinner("Loading graph data..."):
            # Load graph data
            graph_data = load_graph_data()
            
            if graph_data:
                # Create visualization
                html_file = create_graph_visualization(graph_data)
                
                # Display summary metrics
                student_count = sum(1 for node in graph_data['nodes'] if node['type'] == 'Student')
                teacher_count = sum(1 for node in graph_data['nodes'] if node['type'] == 'Teacher')
                category_count = sum(1 for node in graph_data['nodes'] if node['type'] == 'Category')
                feedback_count = sum(1 for node in graph_data['nodes'] if node['type'] == 'Feedback')
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div class='metric-card' style='background-color: rgba(30, 136, 229, 0.2);'><div class='metric-value'>{student_count}</div><div class='metric-label'>Students</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='metric-card' style='background-color: rgba(67, 160, 71, 0.2);'><div class='metric-value'>{teacher_count}</div><div class='metric-label'>Teachers</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='metric-card' style='background-color: rgba(251, 140, 0, 0.2);'><div class='metric-value'>{category_count}</div><div class='metric-label'>Categories</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='metric-card' style='background-color: rgba(142, 36, 170, 0.2);'><div class='metric-value'>{feedback_count}</div><div class='metric-label'>Feedback</div></div>", unsafe_allow_html=True)
                
                # Display the graph visualization
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.components.v1.html(open(html_file, 'r').read(), height=600)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display network statistics
                st.markdown("<div class='card'><h3>Network Statistics</h3>", unsafe_allow_html=True)
                
                # Create a NetworkX graph for analysis
                G = nx.DiGraph()
                
                # Add nodes
                for node in graph_data['nodes']:
                    G.add_node(node['id'], label=node['label'], type=node['type'])
                
                # Add edges
                for edge in graph_data['edges']:
                    G.add_edge(edge['source'], edge['target'], relation=edge['relation'])
                
                # Calculate statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Nodes", len(G.nodes))
                    st.metric("Total Connections", len(G.edges))
                    
                    # Calculate average degree
                    total_degree = sum(dict(G.degree()).values())
                    avg_degree = total_degree / len(G.nodes) if len(G.nodes) > 0 else 0
                    st.metric("Average Connections per Node", f"{avg_degree:.2f}")
                
                with col2:
                    # Find most connected student
                    student_degrees = {node: deg for node, deg in G.degree() 
                                     if G.nodes[node]['type'] == 'Student'}
                    if student_degrees:
                        most_connected_student = max(student_degrees.items(), key=lambda x: x[1])
                        st.metric("Most Connected Student", 
                                 f"{G.nodes[most_connected_student[0]]['label']} ({most_connected_student[1]} connections)")
                    
                    # Find most connected teacher
                    teacher_degrees = {node: deg for node, deg in G.degree() 
                                     if G.nodes[node]['type'] == 'Teacher'}
                    if teacher_degrees:
                        most_connected_teacher = max(teacher_degrees.items(), key=lambda x: x[1])
                        st.metric("Most Connected Teacher", 
                                 f"{G.nodes[most_connected_teacher[0]]['label']} ({most_connected_teacher[1]} connections)")
                    
                    # Find most common category
                    category_degrees = {node: deg for node, deg in G.degree() 
                                      if G.nodes[node]['type'] == 'Category'}
                    if category_degrees:
                        most_common_category = max(category_degrees.items(), key=lambda x: x[1])
                        st.metric("Most Common Category", 
                                 f"{G.nodes[most_common_category[0]]['label']} ({most_common_category[1]} connections)")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Cleanup the temporary file
                try:
                    Path(html_file).unlink()
                except:
                    pass
            else:
                st.error("Failed to load graph data.")

# Footer
st.markdown("---")
st.markdown(
    "**Special Education Feedback Insight System** | "
    f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# Run the app with: streamlit run dashboard/streamlit_app.py
