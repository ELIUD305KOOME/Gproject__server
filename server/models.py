from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import datetime
from sqlalchemy import MetaData
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
    USER = 'user'
    ADMIN = 'admin'


class Location(db.Model, SerializerMixin):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    county = db.Column(db.String(100), nullable=False)
    town = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)

    user = db.relationship('User', back_populates='locations')

    def __repr__(self):
        return f"<Location id={self.id}, country={self.country}, county={self.county}, town={self.town}, postal_code={self.postal_code}>"

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country,
            'county': self.county,
            'town': self.town,
            'postal_code': self.postal_code,
        }

class User(db.Model, SerializerMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='USER')
    contacts = db.relationship('Contact', backref='user', lazy=True)
    display_photo = db.Column(db.String(200))  # Add this field for display photo URL/path
    locations = db.relationship('Location', back_populates='user', lazy=True)  # Add this field for locations
    

    def __repr__(self):
        return f"<User id={self.id}, name={self.name}, email={self.email}, role={self.role}>"

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
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'contacts': [contact.to_dict() for contact in self.contacts],
            'display_photo': self.display_photo,  # Include display photo URL/path
        }
    
class UserStats(db.Model,SerializerMixin):
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
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"



from sqlalchemy import event

event.listen(User, 'after_insert', update_user_stats)
event.listen(User, 'before_update', update_user_stats)
event.listen(User, 'before_delete', deactivate_user_stats)