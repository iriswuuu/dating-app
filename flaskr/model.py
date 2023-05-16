from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False)
    matches = db.relationship("Match", backref="users", lazy=True, primaryjoin="User.id==Match.user_id_1")
    likes_sent = db.relationship("Like", backref="sender", lazy=True, foreign_keys="[Like.user_id_1]", primaryjoin="User.id==Like.user_id_1")
    likes_received = db.relationship("Like", backref="receiver", lazy=True, foreign_keys="[Like.user_id_2]", primaryjoin="User.id==Like.user_id_1")
    messages_sent = db.relationship("Message", backref="sender", lazy=True, foreign_keys="[Message.sender_id]", primaryjoin="User.id==Message.sender_id")
    messages_received = db.relationship("Message", backref="receiver", lazy=True, foreign_keys="[Message.receiver_id]", primaryjoin="User.id==Message.sender_id")

    def __repr__(self):
      return f'<User with id {self.id}>'

    @classmethod
    def create(cls, username, password):
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
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    photo = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    interests = db.Column(db.String(255))


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_1 = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_id_2 = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    match_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_1 = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_id_2 = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    like_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    send_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def connect_to_db(flask_app, db_uri="postgresql:///matchmeet", echo=True):
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    flask_app.config['SQLALCHEMY_ECHO'] = echo
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.app = flask_app
    db.init_app(flask_app)

    print('Connected to the db!')

if __name__ == '__main__':
    from server import app
    connect_to_db(app)