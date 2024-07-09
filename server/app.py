
from flask_login import LoginManager, login_required, current_user, logout_user

from flask.views import MethodView
#!/usr/bin/env python3
from flask import Flask, request, make_response, jsonify, send_from_directory, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os
from werkzeug.utils import secure_filename
from models import db, User

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.config['SECRET_KEY'] = '2#fJ7$kd_9W!sL@0'
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Serving uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# Role-Based Access Control (RBAC)
def role_required(role):
    def decorator(func):
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                return jsonify({"error": "You do not have access to this resource"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator




class Home(MethodView):
    def get(self):
        return "<h1>user application</h1>"
    
    def post(self):
        return "<h1>Welcome to user applicaton!</h1>"
# User Resources
class Users(Resource):
    @login_required
    def get(self):
        users = [user.to_dict() for user in User.query.all()]
        return make_response(jsonify(users), 200)

    def post(self):
        data = request.form
        file = request.files.get('display_photo')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            display_photo_url = f"/uploads/{filename}"
        else:
            display_photo_url = ''

        new_user = User(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user'),
            contacts=data.get("contacts", ''),
            locations=data.get("locations", ''),
            display_photo=display_photo_url
        )
        db.session.add(new_user)
        db.session.commit()
        return make_response(new_user.to_dict(), 201)

class UserByID(Resource):
    @role_required('admin')
    def get(self, id):
        user = User.query.get(id)
        if user is None:
            return {"error": "User not found"}, 404
        return make_response(user.to_dict(), 200)

    def delete(self, id):
        user = User.query.get(id)
        if user is None:
            return {"error": "User not found"}, 404
        db.session.delete(user)
        db.session.commit()
        return {}, 204

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            return make_response(user.to_dict(), 200)
        return {"error": "Invalid credentials"}, 401

class UserRegister(Resource):
    def post(self):
        data = request.form
        file = request.files.get('display_photo')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            display_photo_url = f"/uploads/{filename}"
        else:
            display_photo_url = ''

        new_user = User(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user'),
            contacts=data.get("contacts", ''),
            locations=data.get("locations", ''),
            display_photo=display_photo_url
        )
        db.session.add(new_user)
        db.session.commit()
        return make_response(new_user.to_dict(), 201)

class UserPasswordReset(Resource):
    @login_required
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user:
            user.password = data['new_password']
            db.session.commit()
            return {"message": "Password reset successful"}, 200
        return {"error": "User not found"}, 404

class UserProfile(Resource):
    @login_required
    def get(self):
        user = current_user
        return make_response(user.to_dict(), 200)
    
    @role_required('admin')
    def get(self, id):
        user = User.query.get(id)
        if user is None:
            return {"error": "User not found"}, 404
        return make_response(user.to_dict(), 200)

class UserProfileUpdate(Resource):
    @login_required
    def put(self):
        user = current_user
        if user is None:
            return {"error": "User not found"}, 404
        data = request.form
        file = request.files.get('display_photo')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.display_photo = f"/uploads/{filename}"

        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return make_response(user.to_dict(), 200)
    
    @role_required('admin')
    def patch(self, id):
        user = User.query.get(id)
        if user is None:
            return {"error": "User not found"}, 404
        data = request.form
        file = request.files.get('display_photo')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.display_photo = f"/uploads/{filename}"

        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return make_response(user.to_dict(), 200)







# API Resource Routing
api.add_resource(Users, "/users")
api.add_resource(Login, "/login")
api.add_resource(UserRegister, "/register")
api.add_resource(UserPasswordReset, "/password/reset")
api.add_resource(UserProfile, "/users/<int:id>")
api.add_resource(UserProfileUpdate, "/users/<int:id>/update")
# api.add_resource(Logout, "/logout")



# api.add_resource(UserStatsResource, "/user_stats")
# api.add_resource(Contacts, "/contacts")

app.add_url_rule('/', view_func=Home.as_view('home'))

if __name__ == "__main__":
    app.run(port=5555, debug=True)
