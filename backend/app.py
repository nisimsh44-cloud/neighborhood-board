from flask import Flask, jsonify, request, render_template, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db
from models import User, Post
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)

# תמיכה בכתובות HTTPS של ngrok
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# הגדרות בסיס נתונים ואבטחה
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neighborhood.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db.init_app(app)
bcrypt = Bcrypt(app)

# הגדרת Google OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


with app.app_context():
    db.create_all()

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'resident')
    business_name = data.get('business_name') if role == 'business' else None
    business_category = data.get('business_category') if role == 'business' else None

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'האימייל כבר קיים במערכת'}), 400

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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({
            'message': 'התחברת בהצלחה',
            'user': {
                'username': user.username,
                'role': user.role
            }
        }), 200

    return jsonify({'error': 'שם משתמש או סיסמה שגויים'}), 401

# התחברות עם Google
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
        # משתמש חדש מגוגל - דורש אישור פרטים/תפקיד
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

    # אם המשתמש טרם השלים את בחירת התפקיד והפרטים
    if not user.is_approved:
        return redirect(url_for('complete_profile', user_id=user.id))

    return f"""
    <script>
        localStorage.setItem("username", "{user.username}");
        localStorage.setItem("role", "{user.role}");
        window.location.href = "/";
    </script>
    """

# מסך השלמת פרטים למשתמשי Google חדשים
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
        
        return f"""
        <script>
            localStorage.setItem("username", "{user.username}");
            localStorage.setItem("role", "{user.role}");
            window.location.href = "/";
        </script>
        """
        
    return """
    <div style="font-family: Heebo, sans-serif; text-align: center; margin-top: 80px; direction: rtl; background-color: #f8f9fa; padding: 40px; border-radius: 12px; max-width: 450px; margin-left: auto; margin-right: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="color: #0d6efd; margin-bottom: 20px;">כמעט סיימנו!</h2>
        <p style="color: #555; margin-bottom: 20px;">אנא בחר האם אתה דייר או בעל עסק בשכונה:</p>
        <form method="POST">
            <select name="user_type" id="userTypeSelect" onchange="toggleBiz()" style="padding: 12px; font-size: 16px; border-radius: 8px; width: 100%; margin-bottom: 20px; border: 1px solid #ccc;">
                <option value="resident">דייר בשכונה</option>
                <option value="business">בעל עסק מקומי</option>
            </select><br>
            
            <div id="bizDiv" style="display: none; text-align: right; margin-bottom: 20px;">
                <label style="font-size: 14px; color: #333;">שם העסק:</label><br>
                <input type="text" name="business_name" style="padding: 10px; font-size: 14px; border-radius: 8px; width: 100%; margin-bottom: 10px; border: 1px solid #ccc;"><br>
                <label style="font-size: 14px; color: #333;">קטגוריה:</label><br>
                <select name="business_category" style="padding: 10px; font-size: 14px; border-radius: 8px; width: 100%; border: 1px solid #ccc;">
                    <option value="food">אוכל ומסעדות</option>
                    <option value="services">שירותים ותיקונים</option>
                    <option value="retail">חנויות ומסחר</option>
                    <option value="other">אחר</option>
                </select>
            </div>

            <button type="submit" style="padding: 12px 20px; background: #0d6efd; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; font-weight: bold;">אישור והמשך</button>
        </form>
    </div>
    <script>
        function toggleBiz() {
            const val = document.getElementById('userTypeSelect').value;
            document.getElementById('bizDiv').style.display = (val === 'business') ? 'block' : 'none';
        }
    </script>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)
