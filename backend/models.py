from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True) # מאפשר ערך ריק למשתמשי Google
    role = db.Column(db.String(20), default='resident', nullable=False) # 'resident' לדייר או 'business' לבעל עסק
    is_approved = db.Column(db.Boolean, default=True, nullable=False) # מוודא שהמשתמש סיים לבחור תפקיד/פרטים
    
    # שדות ייעודיים לבעלי עסקים
    business_name = db.Column(db.String(100), nullable=True)
    business_category = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'