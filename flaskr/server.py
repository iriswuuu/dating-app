"""Server for dating app."""

import os
import model
from datetime import datetime
from flask import Flask
from flask import jsonify, session, url_for, request, redirect, render_template, g, flash
from sqlalchemy.exc import IntegrityError

from jinja2 import StrictUndefined
import functools

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)
app.jinja_env.undefined = StrictUndefined

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        if error is None:
            try:
                """Add a new user to the database."""
                model.db.session.add(model.User.create(username, password))
                model.db.session.commit()
                user = model.User.get_by_username(username)

                model.db.session.add(model.UserProfile.create(user.id))
                model.db.session.commit()

                profile = model.UserProfile.get_by_user_id(user.id)
                profile.photo = '../static/unkown_user.png'
                user.profile = profile.id
                model.db.session.add(user)
                model.db.session.add(profile)
                model.db.session.commit()

            except IntegrityError as e:
                error = f"User {username} is already registered."
                print(e)
            else:
                """Redirect to the login page after successful registration."""
                return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = model.User.get_by_username(username)

        if user is None:
            error = 'Incorrect username.'
        elif user.password != password:
            error = 'Incorrect password.'

        if error is None:
            """Store the user ID in the session to keep the user logged in."""
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        """Load the user object from the database based on the user ID stored in the session."""
        g.user = model.User.get_by_id(user_id)


@app.route('/logout')
def logout():
    """Clear the session to log the user out."""
    session.clear()
    return redirect(url_for('login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            """Redirect to the login page if the user is not logged in."""
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view


@app.route('/')
@login_required
def index():
    name = 'John Doe'
    age = 25
    gender = 'male'
    interests = 'Sports, Music, Travel'
    description = 'I am very rich.'
    profileUrl = '../static/eg-profile-photo.jpg'
    return render_template('match.html', name=name, age=age, gender=gender, interests=interests, description=description, profileUrl=profileUrl)


@app.route('/settings')
@login_required
def settings():
    name = 'John Doe'
    age = 25
    gender = 'male'
    interests = 'Sports, Music, Travel'
    description = 'I am very rich.'
    profileUrl = '../static/eg-profile-photo.jpg'
    return render_template('match.html', name=name, age=age, gender=gender, interests=interests, description=description, profileUrl=profileUrl)


@app.route('/profile/<user_id>', methods=['GET'])
@login_required
def profile(user_id):
    profile = model.UserProfile.get_by_user_id(user_id)
    name = f'{profile.firstname} {profile.lastname}'

    current_date = datetime.now()

    if profile.birthday:
        age = current_date.year - profile.birthday.year

        if current_date.month < profile.birthday.month or (current_date.month == profile.birthday.month and current_date.day < profile.birthday.day):
            age -= 1
    else:
        age = None

    gender = profile.gender
    interests = None if not profile.interests else ','.join(profile.interests)
    description = profile.description
    profileUrl = profile.photo
    return render_template('profile.html', name=name, age=age, gender=gender, interests=interests, description=description, profileUrl=profileUrl)

# Restful APIs
@app.route('/api/profile/userid/<id>', methods=['GET'])
def get_user_profile(id):
    profile = model.UserProfile.get_by_user_id(id)
    return jsonify(profile)

@app.route('/api/user/<id>', methods=['GET'])
def get_user(id):
    user = model.User.get_by_id(id)
    del user.password
    return jsonify(user)

@app.route('/api/profile/<id>', methods=['POST'])
def update_user_profile(id):
    profile = model.UserProfile.get_by_user_id(id)
    return jsonify(profile)

if __name__ == '__main__':
    """Connect to the database."""
    model.connect_to_db(app)
    app.run(host='127.0.0.1', debug=True)