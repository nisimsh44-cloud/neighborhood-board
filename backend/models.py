from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True) # מאפשר ערך ריק למשתמשי Google
    role = db.Column(db.String(20), default='resident', nullable=False) # 'resident', 'business', 'admin'
    is_approved = db.Column(db.Boolean, default=True, nullable=False)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False) # חסימת משתמש ע"י אדמין
    
    # שדות ייעודיים לבעלי עסקים
    business_name = db.Column(db.String(100), nullable=True)
    business_category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_approved': self.is_approved,
            'is_blocked': self.is_blocked,
            'business_name': self.business_name,
            'business_category': self.business_category,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='כללי', nullable=False) # קטגוריה לסינון מודעות
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'user_id': self.user_id,
            'author_name': self.author.username if self.author else 'לא ידוע'
        }

    def __repr__(self):
        return f'<Post {self.title}>'
