from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Feedback(db.Model):
    """Model for storing special education feedback data."""
    
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False, index=True)
    teacher_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    open_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    
    def __init__(self, student_id, teacher_name, rating, category, open_feedback=None):
        self.student_id = student_id
        self.teacher_name = teacher_name
        self.rating = rating
        self.category = category
        self.open_feedback = open_feedback
    
    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teacher_name': self.teacher_name,
            'rating': self.rating,
            'category': self.category,
            'open_feedback': self.open_feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed': self.processed
        }
    
    def __repr__(self):
        return f'<Feedback {self.id} - Student: {self.student_id} - Category: {self.category}>'
