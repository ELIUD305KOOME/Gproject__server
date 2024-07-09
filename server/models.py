from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import MetaData, event
from sqlalchemy.orm import validates
import re
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)

class UserRole:
    EMPLOYEE = 'employee'
    ADMIN = 'admin'

class User(db.Model, SerializerMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='EMPLOYEE')
    contacts = db.Column(db.String(150))
    arrivaltime = db.Column(db.Integer)
    time_entries = db.relationship('TimeEntry', backref='user', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    last_login = db.Column(db.DateTime)

    def __repr__(self):
        return f"<User id={self.id}, firstname={self.firstname}, lastname={self.lastname}, email={self.email}, role={self.role}>"

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email is required")
        
        # Regular expression for email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        # Check if email is already taken
        existing_user = User.query.filter(User.email == email).first()
        if existing_user and existing_user.id != self.id:
            raise ValueError("Email address is already registered")

        return email.lower()  # Normalize email to lowercase

    @validates('password')
    def validate_password(self, key, password):
        if not password:
            raise ValueError("Password is required")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return password

    def update_stats(self):
        stats = UserStats.query.filter_by(role=self.role).first()
        if not stats:
            stats = UserStats(role=self.role, active_users=0, total_users=0)
            db.session.add(stats)

        if self.subscription_active:
            stats.active_users += 1
        stats.total_users += 1

        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'gender': self.gender,
            'email': self.email,
            'role': self.role,
            'contacts': self.contacts,
            'arrivaltime': self.arrivaltime,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

class Admin(db.Model, SerializerMixin):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship("User", backref="admin")
    arrivaltime = db.Column(db.Integer)
    leaves = db.relationship('Leave', backref='admin', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)

class Employee(db.Model, SerializerMixin):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship("User", backref="employee")
    employee_id = db.Column(db.Integer, unique=True)
    salary = db.Column(db.Float)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    arrivaltime = db.Column(db.Integer)
    leaves = db.relationship('Leave', backref='employee', lazy=True)
    posts = db.relationship('Post', backref='employee', lazy=True)

class UserStats(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    active_users = db.Column(db.Integer, default=0)
    total_users = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<UserStats id={self.id}, role={self.role}, active_users={self.active_users}, total_users={self.total_users}>"

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'active_users': self.active_users,
            'total_users': self.total_users
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    arrivaltime = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<TimeEntry user_id={self.user_id}, arrivaltime={self.arrivaltime}, timestamp={self.timestamp}>"

def update_user_stats(mapper, connection, target):
    stats = UserStats.query.filter_by(role=target.role).first()
    if not stats:
        stats = UserStats(role=target.role, active_users=0, total_users=0)
        db.session.add(stats)

    if target.subscription_active:
        stats.active_users += 1
    stats.total_users += 1
    db.session.commit()

def deactivate_user_stats(mapper, connection, target):
    stats = UserStats.query.filter_by(role=target.role).first()
    if target.subscription_active:
        stats.active_users -= 1
    stats.total_users -= 1
    db.session.commit()

def log_arrivaltime(mapper, connection, target):
    if target.arrivaltime:
        time_entry = TimeEntry(user_id=target.id, arrivaltime=target.arrivaltime)
        db.session.add(time_entry)
        db.session.commit()

event.listen(User, 'after_insert', update_user_stats)
event.listen(User, 'before_update', update_user_stats)
event.listen(User, 'before_delete', deactivate_user_stats)
event.listen(User, 'before_update', log_arrivaltime)
