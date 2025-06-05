from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_app.models import db, Feedback
from flask_app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy", "service": "sped-feedback-etl"}), 200

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """
    Endpoint to submit structured feedback for special education students.
    
    Accepts:
    - student_id: Identifier for the student
    - teacher_name: Name of the teacher providing feedback
    - rating: Numerical rating (typically 1-5)
    - category: Category of feedback (e.g., 'academics', 'behavior', 'social')
    - open_feedback: Open-ended text feedback
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'teacher_name', 'rating', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Validate rating is a number between 1-5
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                return jsonify({
                    "status": "error", 
                    "message": "Rating must be between 1 and 5"
                }), 400
        except ValueError:
            return jsonify({
                "status": "error", 
                "message": "Rating must be a number"
            }), 400
        
        # Create a new feedback entry
        feedback = Feedback(
            student_id=data['student_id'],
            teacher_name=data['teacher_name'],
            rating=rating,
            category=data['category'],
            open_feedback=data.get('open_feedback')  # Optional field
        )
        
        # Save to database
        db.session.add(feedback)
        db.session.commit()
        
        # Queue open feedback for asynchronous processing with Celery
        from celery_tasks.process_feedback import process_open_feedback
        if feedback.open_feedback:
            process_open_feedback.delay(feedback.id, feedback.open_feedback)
            processing_message = "Open feedback queued for processing"
        else:
            processing_message = "No open feedback to process"
        
        return jsonify({
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id,
            "processing_status": processing_message
        }), 201
        
    except Exception as e:
        # Log the exception
        app.logger.error(f"Error submitting feedback: {str(e)}")
        # Rollback in case of error
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "An error occurred while processing your request"
        }), 500

@app.route('/api/feedback', methods=['POST'])
def receive_feedback():
    """Endpoint to receive new feedback data."""
    data = request.get_json()
    
    # TODO: Implement feedback processing logic
    # - Validate input data
    # - Store in database
    # - Trigger processing via Celery
    
    return jsonify({"status": "received", "message": "Feedback received successfully"}), 201

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """Endpoint to retrieve insights from processed feedback."""
    # TODO: Implement insights retrieval logic
    # - Query from databases (vector, graph, dynamo)
    # - Format response
    
    # Placeholder response
    insights = {
        "summary": "Sample insights will appear here",
        "trends": [],
        "recommendations": []
    }
    
    return jsonify(insights), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
