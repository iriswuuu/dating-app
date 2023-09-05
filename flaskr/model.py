"""Models for dating app."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

db = SQLAlchemy()

class User(db.Model):
    """A user."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True)
    profile = db.Column(db.Integer, nullable=True, unique=True)
    matches = db.Column(ARRAY(db.Integer), nullable=True)
    likes_sent = db.Column(ARRAY(db.Integer), nullable=True)
    likes_received = db.Column(ARRAY(db.Integer), nullable=True)
    users_seen = db.Column(ARRAY(db.Integer), nullable=True)

    def __repr__(self):
      """Return a string representation of the User object."""
      return f'<User with id {self.id}>'

    @classmethod
    def create(cls, username, password):
      """Create and return a new user."""
      return cls(username=username, password=password)

    @classmethod 
    def get_by_id(cls, id):
      """Get a user by their ID."""
      return cls.query.get(id)

    @classmethod
    def get_by_username(cls, username):
      """Get a user by their username."""
      return cls.query.filter(User.username == username).first()

    @classmethod
    def get_by_email(cls, email):
      """Get a user by their email."""
      return cls.query.filter(User.email == email).first()

    @classmethod
    def get_all(cls, ids):
       return cls.query.filter(User.id.in_(ids)).all()


class UserProfile(db.Model):
    """A user profile."""
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    firstname = db.Column(db.String(64), nullable=True)
    lastname = db.Column(db.String(64), nullable=True)
    birthday = db.Column(db.DateTime, nullable=True)
    gender = db.Column(db.Integer, nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text)
    interests = db.Column(ARRAY(db.String(255)))

    @classmethod
    def create(cls, user_id):
      """Create and return a new user profile."""
      return cls(user_id=user_id)

    @classmethod
    def get_by_id(cls, id):
      """Get a user profile by its ID."""
      return cls.query.get(id)
    
    @classmethod
    def get_by_user_id(cls, user_id):
      """Get a user profile by the user ID."""
      return cls.query.filter(UserProfile.user_id == user_id).first()
    
    @classmethod
    def get_one_with_explicit_out_user_list(cls, explicit_out_list):
      """Get a user profile that is not in the explicit out list."""
      return cls.query.filter(~UserProfile.user_id.in_(explicit_out_list)).first()
    
    @classmethod
    def get_with_user_ids(cls, user_ids):
       return cls.query.filter(UserProfile.user_id.in_(user_ids)).all()


class Message(db.Model):
    """A message between two users."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    send_time = db.Column(db.BigInteger, nullable=False)

    @classmethod
    def create(cls, sender_id, receiver_id, message, send_time):
      """Create and return a new user profile."""
      return cls(sender_id=sender_id, receiver_id=receiver_id, message=message, send_time=send_time)

    @classmethod
    def get_message_as_sender(cls, user_id):
       return cls.query.filter(Message.sender_id == user_id).all()
    
    @classmethod
    def get_message_receiver(cls, user_id):
       return cls.query.filter(Message.receiver_id == user_id).all()
    
    def toJSON(self):
        return {
           "sender_id": self.sender_id,
           "receiver_id": self.receiver_id,
           "message": self.message,
           "send_time": self.send_time
        }

def validate_database(db_uri):
     """Validates the existence of a database and creates a new one if it doesn't exist."""
     engine = create_engine(db_uri)
     if not database_exists(engine.url): # Checks for the first time  
         create_database(engine.url)     # Create new DB    
         print("New Database Created" + str(database_exists(engine.url))) # Verifies if database is there or not.
     else:
         print("Database Already Exists")


def connect_to_db(flask_app, db_uri="postgresql:///matchmeet", echo=True):
    """Connects to the database."""
    validate_database(db_uri)

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    flask_app.config['SQLALCHEMY_ECHO'] = echo
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.app = flask_app
    db.init_app(flask_app)

    print('Connected to the db!')

    with flask_app.app_context():
      db.create_all()

if __name__ == '__main__':
    from server import app
    connect_to_db(app)