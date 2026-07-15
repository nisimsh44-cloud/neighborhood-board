from flask import Flask, jsonify
from database import db  
import os

app = Flask(__name__)

# הגדרת נתיב לקובץ ה-SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#  יצירת את תיקיית instance 
os.makedirs(instance_path, exist_ok=True)

# אתחול ה-Database עם האפליקציה
db.init_app(app)

# מייבא את המודלים 
from models import User, Post

# יצירת הטבלאות בתוך ה-Database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Welcome to Neighborhood Board!"

@app.route('/api/posts')
def get_posts():
    # 1. שליפת כל הפוסטים מהדאטהבייס באמצעות SQLAlchemy
    db_posts = Post.query.all()
    
    # 2. המרת האובייקטים לפונקציות/מילונים של פייתון כדי שנוכל להחזיר אותם כ-JSON
    posts_list = []
    for post in db_posts:
        posts_list.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else None,
            "author": post.author.username  # גישה ישירות לשם של כותב הפוסט
        })
        
    return jsonify(posts_list)

if __name__ == '__main__':
    app.run(debug=True)
