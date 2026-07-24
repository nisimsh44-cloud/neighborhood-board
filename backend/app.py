from flask import Flask, request, jsonify
from database import db, bcrypt
from models import User, Post

app = Flask(__name__)

#  SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db.init_app(app)
bcrypt.init_app(app)

# create database
with app.app_context():
    db.create_all()

# Endpoint whith bcrypt (SCRUM-15)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    # check if user existing 
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({'message': 'Username or email already exists'}), 400

    # hashed password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # create new user and save in database
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)
