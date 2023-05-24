"""Models for movie ratings app."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
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
    matches = db.Column(ARRAY(db.Integer), nullable=True, unique=True)
    likes_sent = db.Column(ARRAY(db.Integer), nullable=True, unique=True)
    likes_received = db.Column(ARRAY(db.Integer), nullable=True, unique=True)
    messages_sent = db.Column(ARRAY(db.Integer), nullable=True, unique=True)
    messages_received = db.Column(ARRAY(db.Integer), nullable=True, unique=True)

    def __repr__(self):
      return f'<User with id {self.id}>'

    @classmethod
    def create(cls, username, password):
      """Create and return a new user."""
      return cls(username=username, password=password)

    @classmethod
    def get_by_id(cls, id):
      return cls.query.get(id)

    @classmethod
    def get_by_username(cls, username):
      return cls.query.filter(User.username == username).first()

    @classmethod
    def get_by_email(cls, email):
      return cls.query.filter(User.email == email).first()


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
    description = db.Column(db.String(255))
    interests = db.Column(ARRAY(db.String(255)))

    @classmethod
    def create(cls, user_id):
      """Create and return a new user profile."""
      return cls(user_id=user_id)

    @classmethod
    def get_by_id(cls, id):
      return cls.query.get(id)
    
    @classmethod
    def get_by_user_id(cls, user_id):
      return cls.query.filter(UserProfile.user_id == user_id).first()


class Match(db.Model):
    """A match between two users."""
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_1 = db.Column(db.Integer, nullable=False)
    user_id_2 = db.Column(db.Integer, nullable=False)
    match_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Like(db.Model):
    """A user's like for another user."""
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_1 = db.Column(db.Integer, nullable=False)
    user_id_2 = db.Column(db.Integer, nullable=False)
    match_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Message(db.Model):
    """A message between two users."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    send_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def validate_database(db_uri):
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