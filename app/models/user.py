from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    job_title = db.Column(db.String(120), nullable=True)
    experiences = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    theme_color = db.Column(db.String(20), default="#2C3E50")
    pdf_status = db.Column(db.String(20), default="PENDING")
    pdf_filename = db.Column(db.String(255), nullable=True)
    
    # Audit & Traçabilité Swarm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by_container = db.Column(db.String(64), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name or self.username or "",
            "last_name": self.last_name or "",
            "username": self.username,
            "email": self.email,
            "phone": self.phone or "",
            "job_title": self.job_title or "",
            "experiences": self.experiences,
            "skills": self.skills or "",
            "theme_color": self.theme_color,
            "pdf_status": self.pdf_status,
            "pdf_filename": self.pdf_filename,
            "created_at": self.created_at.isoformat(),
            "processed_by_container": self.processed_by_container
        }