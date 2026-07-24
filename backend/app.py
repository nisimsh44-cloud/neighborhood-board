from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# בסיס נתונים זמני של משתמשים
users_db = {
    "admin": {
        "email": "admin@board.com",
        "password": bcrypt.generate_password_hash("admin123").decode('utf-8'),
        "role": "admin",
        "is_blocked": False
    },
    "eyal root": {
        "email": "eyal@board.com",
        "password": bcrypt.generate_password_hash("123456").decode('utf-8'),
        "role": "user",
        "is_blocked": False
    },
    "Nisim": {
        "email": "nisim@board.com",
        "password": bcrypt.generate_password_hash("123456").decode('utf-8'),
        "role": "user",
        "is_blocked": False
    }
}

posts_db = [
    {
        "id": 1,
        "title": "ספת סלון במצב מעולה",
        "content": "מוכר ספה דו-מושבית שמורה כחדשה, איסוף מקומה 2.",
        "category": "ריהוט",
        "author": "eyal root",
        "created_at": "2026-07-24"
    },
    {
        "id": 2,
        "title": "שיעורים פרטיים בפייתון",
        "content": "סטודנט למדמ\"ש מציע שיעורים פרטיים למתחילים ולמתקדמים.",
        "category": "לימודים",
        "author": "Nisim",
        "created_at": "2026-07-24"
    }
]

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'user')

    if not username or not password or not email:
        return jsonify({'error': 'יש למלא את כל השדות'}), 400

    if username in users_db:
        return jsonify({'error': 'שם המשתמש כבר קיים'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users_db[username] = {
        'email': email,
        'password': hashed_password,
        'role': role,
        'is_blocked': False
    }

    return jsonify({'message': 'ההרשמה בוצעה בהצלחה!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users_db.get(username)
    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'error': 'שם משתמש או סיסמה שגויים'}), 401

    if user.get('is_blocked', False):
        return jsonify({'error': 'חשבון זה נחסם על ידי מנהל המערכת'}), 403

    return jsonify({
        'message': 'התחברת בהצלחה!',
        'access_token': f'fake-jwt-token-for-{username}',
        'username': username,
        'role': user.get('role', 'user')
    }), 200

# קבלת רשימת כל המשתמשים (עבור אדמין בלבד)
@app.route('/api/users', methods=['GET'])
def get_users():
    requester = request.args.get('username')
    requester_user = users_db.get(requester, {})

    if requester_user.get('role') != 'admin':
        return jsonify({'error': 'אין לך הרשאת אדמין'}), 403

    users_list = [
        {
            'username': uname,
            'email': udata.get('email'),
            'role': udata.get('role', 'user'),
            'is_blocked': udata.get('is_blocked', False)
        }
        for uname, udata in users_db.items()
    ]
    return jsonify(users_list), 200

# מחיקת משתמש (עבור אדמין)
@app.route('/api/users/<string:target_user>', methods=['DELETE'])
def delete_user(target_user):
    data = request.get_json() or {}
    requester = data.get('username')

    if users_db.get(requester, {}).get('role') != 'admin':
        return jsonify({'error': 'אין לך הרשאת אדמין'}), 403

    if target_user == requester:
        return jsonify({'error': 'מנהל אינו יכול למחוק את עצמו'}), 400

    if target_user in users_db:
        del users_db[target_user]

        # מחיקת כל המודעות של המשתמש שנמחק
        global posts_db
        posts_db = [p for p in posts_db if p['author'] != target_user]

        return jsonify({'message': f'המשתמש {target_user} נמחק בהצלחה'}), 200

    return jsonify({'error': 'המשתמש לא נמצא'}), 404

# חסימה/ביטול חסימה של משתמש (עבור אדמין)
@app.route('/api/users/<string:target_user>/toggle-block', methods=['POST'])
def toggle_block_user(target_user):
    data = request.get_json() or {}
    requester = data.get('username')

    if users_db.get(requester, {}).get('role') != 'admin':
        return jsonify({'error': 'אין לך הרשאת אדמין'}), 403

    if target_user == requester:
        return jsonify({'error': 'מנהל אינו יכול לחסום את עצמו'}), 400

    user = users_db.get(target_user)
    if not user:
        return jsonify({'error': 'המשתמש לא נמצא'}), 404

    user['is_blocked'] = not user.get('is_blocked', False)
    status = 'חסום' if user['is_blocked'] else 'פעיל'
    return jsonify({'message': f'סטטוס המשתמש {target_user} שונה ל-{status}', 'is_blocked': user['is_blocked']}), 200

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts_db), 200

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', 'כללי')
    author = data.get('author', 'אורח')

    if not title or not content:
        return jsonify({'error': 'כותרת ותוכן הם שדות חובה'}), 400

    new_id = max([p['id'] for p in posts_db], default=0) + 1

    new_post = {
        "id": new_id,
        "title": title,
        "content": content,
        "category": category,
        "author": author,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    posts_db.insert(0, new_post)
    return jsonify({'message': 'המודעה פורסמה בהצלחה!', 'post': new_post}), 201

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.get_json() or {}
    requester = data.get('username')

    global posts_db
    post = next((p for p in posts_db if p['id'] == post_id), None)

    if not post:
        return jsonify({'error': 'המודעה לא נמצאה'}), 404

    requester_user = users_db.get(requester, {})
    is_admin = requester_user.get('role') == 'admin'

    if post['author'] != requester and not is_admin:
        return jsonify({'error': 'אין לך הרשאה למחוק מודעה זו'}), 403

    posts_db = [p for p in posts_db if p['id'] != post_id]
    return jsonify({'message': 'המודעה נמחקה בהצלחה!'}), 200

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json() or {}
    requester = data.get('username')

    post = next((p for p in posts_db if p['id'] == post_id), None)

    if not post:
        return jsonify({'error': 'המודעה לא נמצאה'}), 404

    requester_user = users_db.get(requester, {})
    is_admin = requester_user.get('role') == 'admin'

    if post['author'] != requester and not is_admin:
        return jsonify({'error': 'אין לך הרשאה לערוך מודעה זו'}), 403

    post['title'] = data.get('title', post['title'])
    post['content'] = data.get('content', post['content'])
    post['category'] = data.get('category', post['category'])

    return jsonify({'message': 'המודעה עודכנה בהצלחה!', 'post': post}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
