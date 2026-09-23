from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db
from models import User, Post
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
import os
import bleach

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neighborhood.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")

db.init_app(app)
bcrypt = Bcrypt(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

with app.app_context():
    db.create_all()

# --- דף הבית ותצוגה ציבורית ---
@app.route('/')
def index():
    category = request.args.get('category')
    query = Post.query
    if category and category != 'הכל':
        query = query.filter_by(category=category)
    posts = query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, current_category=category)

# --- Auth Endpoints ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'resident')
    business_name = data.get('business_name') if role == 'business' else None
    business_category = data.get('business_category') if role == 'business' else None

    if not username or not email or not password:
        return jsonify({'error': 'נא למלא את כל שדות החובה'}), 400

    if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
        return jsonify({'error': 'שם המשתמש או האימייל כבר קיימים במערכת'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        role=role,
        is_approved=True,
        business_name=business_name,
        business_category=business_category
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'ההרשמה בוצעה בהצלחה!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):
        if user.is_blocked:
            return jsonify({'error': 'חשבון זה נחסם ע"י מנהל המערכת'}), 403

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        return jsonify({
            'message': 'התחברת בהצלחה',
            'user': user.to_dict()
        }), 200

    return jsonify({'error': 'שם משתמש או סיסמה שגויים'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'התנתקת בהצלחה'}), 200

@app.route('/api/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'user': None}), 200
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'user': None}), 200
    return jsonify({'user': user.to_dict()}), 200

# --- התחברות עם Google ---
@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        return redirect('/')

    email = user_info['email']
    name = user_info['name']
    user = User.query.filter_by(email=email).first()

    if not user:
        new_user = User(
            username=name,
            email=email,
            password_hash=None,
            role='resident',
            is_approved=False
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    if user.is_blocked:
        return "משתמש זה נחסם ע\"י מנהל", 403

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    if not user.is_approved:
        return redirect(url_for('complete_profile', user_id=user.id))

    return redirect('/')

@app.route('/complete-profile/<int:user_id>', methods=['GET', 'POST'])
def complete_profile(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        user.role = user_type
        user.is_approved = True
        if user_type == 'business':
            user.business_name = request.form.get('business_name')
            user.business_category = request.form.get('business_category')
        db.session.commit()
        session['role'] = user.role
        return redirect('/')

    return """
    <div style="font-family: Heebo, sans-serif; text-align: center; margin-top: 80px; direction: rtl; background-color: #f8f9fa; padding: 40px; border-radius: 12px; max-width: 450px; margin-left: auto; margin-right: auto;">
        <h2>כמעט סיימנו!</h2>
        <p>אנא בחר האם אתה דייר או בעל עסק בשכונה:</p>
        <form method="POST">
            <select name="user_type" id="userTypeSelect" onchange="toggleBiz()" style="padding: 10px; width: 100%; margin-bottom: 15px;">
                <option value="resident">דייר בשכונה</option>
                <option value="business">בעל עסק מקומי</option>
            </select>
            <div id="bizDiv" style="display: none; text-align: right; margin-bottom: 15px;">
                <label>שם העסק:</label><br>
                <input type="text" name="business_name" style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
                <label>קטגוריה:</label><br>
                <select name="business_category" style="width: 100%; padding: 8px;">
                    <option value="food">אוכל ומסעדות</option>
                    <option value="services">שירותים ותיקונים</option>
                    <option value="retail">חנויות ומסחר</option>
                    <option value="other">אחר</option>
                </select>
            </div>
            <button type="submit" style="padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">אישור והמשך</button>
        </form>
    </div>
    <script>
        function toggleBiz() {
            const val = document.getElementById('userTypeSelect').value;
            document.getElementById('bizDiv').style.display = (val === 'business') ? 'block' : 'none';
        }
    </script>
    """

# ==========================================
# SCRUM-7: CRUD Posts & Filtering (MVP)
# ==========================================

# SCRUM-17 + SCRUM-18: קבלת מודעות עם סינון לפי קטגוריה
@app.route('/api/posts', methods=['GET'])
def get_posts():
    category = request.args.get('category')
    query = Post.query
    if category and category != 'הכל':
        query = query.filter_by(category=category)
    posts = query.order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts]), 200

# SCRUM-19: יצירת מודעה חדשה ע"י משתמש מחובר
@app.route('/api/posts', methods=['POST'])
def create_post():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'יש להתחבר כדי לפרסם מודעה'}), 401

    user = User.query.get(user_id)
    if not user or user.is_blocked:
        return jsonify({'error': 'המשתמש אינו מורשה לבצע פעולה זו'}), 403

    data = request.get_json() or {}
    raw_title = data.get('title', '')
    raw_content = data.get('content', '')
    raw_category = data.get('category', 'כללי')

    if not raw_title.strip() or not raw_content.strip():
        return jsonify({'error': 'כותרת ותוכן הם שדות חובה'}), 400

    # SCRUM-24: חיטוי קלט להגנה מפני XSS - הסרת כל תגיות HTML זדוניות
    clean_title = bleach.clean(raw_title, tags=[], strip=True)
    clean_content = bleach.clean(raw_content, tags=[], strip=True)
    clean_category = bleach.clean(raw_category, tags=[], strip=True)

    new_post = Post(
        title=clean_title,
        content=clean_content,
        category=clean_category,
        user_id=user.id
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'המודעה פורסמה בהצלחה!', 'post': new_post.to_dict()}), 201
# SCRUM-20: עריכת מודעה ע"י היוצר בלבד
@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'יש להתחבר כדי לערוך מודעה'}), 401

    post = Post.query.get_or_404(post_id)
    if post.user_id != user_id:
        return jsonify({'error': 'אין לך הרשאה לערוך מודעה זו'}), 403

    data = request.get_json() or {}
    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    post.category = data.get('category', post.category)

    db.session.commit()
    return jsonify({'message': 'המודעה עודכנה בהצלחה!', 'post': post.to_dict()}), 200

# SCRUM-20 + SCRUM-21: מחיקת מודעה (ע"י היוצר או ע"י Admin)
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    user_id = session.get('user_id')
    user_role = session.get('role')
    if not user_id:
        return jsonify({'error': 'יש להתחבר כדי לבצע מחיקה'}), 401

    post = Post.query.get_or_404(post_id)
    # מאפשר מחיקה אם המשתמש הוא היוצר של המודעה או בעל הרשאת מנהל (admin)
    if post.user_id != user_id and user_role != 'admin':
        return jsonify({'error': 'אין לך הרשאות למחוק מודעה זו'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'המודעה נמחקה בהצלחה'}), 200

# ==========================================
# SCRUM-8: Admin Capabilities
# ==========================================

# פונקציית עזר לבדיקת הרשאת Admin
def is_admin():
    return session.get('role') == 'admin'

# קבלת רשימת כל המשתמשים עבור פאנל ניהול
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    if not is_admin():
        return jsonify({'error': 'גישה חסומה: נדרשות הרשאות מנהל'}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([user.to_dict() for user in users]), 200

# SCRUM-22: חסימה או הסרת חסימה של משתמש ע"י מנהל
@app.route('/api/admin/users/<int:target_user_id>/toggle-block', methods=['PATCH'])
def toggle_block_user(target_user_id):
    if not is_admin():
        return jsonify({'error': 'גישה חסומה: נדרשות הרשאות מנהל'}), 403

    user = User.query.get_or_404(target_user_id)
    if user.id == session.get('user_id'):
        return jsonify({'error': 'מנהל אינו יכול לחסום את עצמו'}), 400

    user.is_blocked = not user.is_blocked
    db.session.commit()
    status_str = 'נחסם' if user.is_blocked else 'שוחרר מחסימה'
    return jsonify({'message': f'המשתמש {user.username} {status_str} בהצלחה', 'user': user.to_dict()}), 200

# SCRUM-22: מחיקת משתמש לצמיתות ע"י מנהל
@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
def delete_user(target_user_id):
    if not is_admin():
        return jsonify({'error': 'גישה חסומה: נדרשות הרשאות מנהל'}), 403

    user = User.query.get_or_404(target_user_id)
    if user.id == session.get('user_id'):
        return jsonify({'error': 'מנהל אינו יכול למחוק את עצמו'}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'המשתמש {user.username} נמחק בהצלחה'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
