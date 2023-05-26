"""Server for dating app."""

import os
import model
from datetime import datetime
import uuid
from flask import Flask
from flask import abort, jsonify, session, url_for, request, redirect, render_template, g, flash
from sqlalchemy.exc import IntegrityError
from PIL import Image

from jinja2 import StrictUndefined
import functools

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)
app.jinja_env.undefined = StrictUndefined
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
current_dir = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(current_dir, 'static', 'photos')

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
                profile.firstname = 'Firstname'
                profile.lastname = 'Lastname'
                profile.birthday = datetime(1900, 1, 1)
                profile.description = ''
                profile.interests = []
                profile.gender = 0
                user.profile = profile.id
                user.matches = []
                user.likes_sent = []
                user.likes_received = []
                user.messages_sent = []
                user.messages_received = []
                user.users_seen = []
                model.db.session.add(user)
                model.db.session.add(profile)
                model.db.session.commit()

            except IntegrityError as e:
                error = f"User {username} is already registered."
                print(e)
            else:
                """Redirect to the login page after successful registration."""
                flash('Registered successfully.')
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
    current_user = model.User.get_by_id(session['user_id'])
    users_seen = current_user.users_seen if current_user.users_seen else []
    users_seen.append(current_user.id)

    random_profile = model.UserProfile.get_one_with_explicit_out_user_list(users_seen)
    if not random_profile:
        return render_template('rest.html')
    current_date = datetime.now().date()
    age = current_date.year - random_profile.birthday.year
    if current_date.month < random_profile.birthday.month or (current_date.month == random_profile.birthday.month and current_date.day < random_profile.birthday.day):
        age -= 1
    name = f'{random_profile.firstname} {random_profile.lastname}'
    gender = 'Male' if random_profile.gender == 0 else 'Female'
    return render_template('match.html',
                           name=name,
                           age=age,
                           gender=gender,
                           interests=random_profile.interests,
                           description=random_profile.description,
                           profile_photo=random_profile.photo,
                           profile_user_id=random_profile.user_id)


@app.route('/user/like/<user_id>', methods=['POST'])
@login_required
def like_user(user_id):
    current_user = model.User.get_by_id(session['user_id'])
    target_user = model.User.get_by_id(user_id)

    current_user.likes_sent.append(target_user.id)
    target_user.likes_received.append(current_user.id)

    if target_user.id in current_user.likes_received:
        current_user.matches.append(target_user.id)
        target_user.matches.append(current_user.id)
    
    current_user.users_seen.append(target_user.id)
    # print(current_user.users_seen)
    # print(target_user.users_seen)
    # model.db.session.add(current_user)
    # model.db.session.add(target_user)
    model.db.session.commit()

    return redirect(url_for('index'))


@app.route('/user/dislike/<user_id>', methods=['POST'])
@login_required
def dislike_user(user_id):
    current_user = model.User.get_by_id(session['user_id'])
    target_user = model.User.get_by_id(user_id)
    current_user.users_seen.append(target_user.id)

    model.db.session.add(current_user)
    model.db.session.commit()
    return redirect(url_for('index'))

@app.route('/settings')
@login_required
def settings():
    name = 'John Doe'
    age = 25
    gender = 'male'
    interests = 'Sports, Music, Travel'
    description = 'I am very rich.'
    profileUrl = '../static/eg-profile-photo.jpg'
    return render_template('match.html', profile_user_id=12, name=name, age=age, gender=gender, interests=interests, description=description, profile_photo=profileUrl)


@app.route('/profile/<user_id>', methods=['GET'])
@login_required
def profile(user_id):
    profile = model.UserProfile.get_by_user_id(user_id)
    isCurrentUser = str(user_id) == str(session['user_id'])
    print(profile.birthday)
    return render_template('profile.html', profile=profile, isCurrentUser=isCurrentUser)

@app.route('/profile/<user_id>/photo', methods=['POST'])
@login_required
def photo_upload(user_id):
    if 'file' not in request.files:
        abort(400, 'No file uploaded')

    file = request.files['file']
    if file.filename == '':
        abort(400, 'No file selected')

    if not allowed_file_size(file):
        abort(400, 'File size exceeds the limit')

    filename = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + extension)
    file.seek(0)
    file.save(save_path)

    image = Image.open(save_path)
    cropped_image = image.resize((500, 500))
    cropped_filename = filename + '_cropped' + extension
    cropped_save_path = os.path.join(app.config['UPLOAD_FOLDER'], cropped_filename)
    cropped_image.save(cropped_save_path)

    photo_url = f'../static/photos/{cropped_filename}'
    profile = model.UserProfile.get_by_user_id(user_id)
    profile.photo = photo_url

    model.db.session.add(profile)
    model.db.session.commit()
    return redirect(url_for('profile', user_id=user_id))

def allowed_file_size(file):
    max_size = 20 * 1024 * 1024  # 20MB
    return len(file.read()) <= max_size


@app.route('/profile/<user_id>', methods=['POST'])
@login_required
def profile_update(user_id):
    birthday = request.form['birthday']
    date_obj = datetime.strptime(birthday, "%Y-%m-%d")

    profile = model.UserProfile.get_by_user_id(user_id)
    profile.firstname = request.form['firstname']
    profile.lastname = request.form['lastname']
    profile.gender = request.form['gender']
    profile.description = request.form['description']
    profile.birthday = date_obj

    model.db.session.add(profile)
    model.db.session.commit()

    return redirect(url_for('profile', user_id=user_id))


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