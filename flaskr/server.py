"""Server for dating app."""

import os
import model
from datetime import datetime
import uuid
import json
from flask import Flask
from flask import abort, jsonify, session, url_for, request, redirect, render_template, g, flash
from sqlalchemy.exc import IntegrityError
from flask_socketio import SocketIO
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
app.config['SECRET_KEY'] = 'somesecretkey#'
socketio = SocketIO(app)

@app.route('/register', methods=('GET', 'POST'))
def register():
    """Register route for user registration. Handles both GET and POST requests."""
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
                profile.birthday = datetime(1900, 1, 1) # Default birthday
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
    """Load the logged-in user before each request.
    Retrieves the user ID from the session and loads the corresponding user object from the database.
    """
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        """Load the user object from the database based on the user ID stored in the session."""
        g.user = model.User.get_by_id(user_id)


@app.route('/logout')
def logout():
    """Logout route for clearing the session and logging out the user."""
    session.clear()
    return redirect(url_for('login'))


def login_required(view):
    """Decorator to require login for accessing a view.
    If the user is not logged in, it redirects to the login page.
    """
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
    """Homepage route.
    Displays a random user profile to the logged-in user. 
    If there are no more profiles to display, it renders a rest.html template.
    """
    current_user = model.User.get_by_id(session['user_id'])
    users_seen = current_user.users_seen
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
    """Like a user.

    Adds the liked user to the current user's likes sent and the liked user's likes received.
    If there is a mutual like (both users have liked each other), it adds a match between them.
    The user who receives the like is also added to the current user's list of seen users.

    """

    current_user = model.User.get_by_id(session['user_id'])
    target_user = model.User.get_by_id(user_id)

    current_user_users_seen = current_user.users_seen
    current_user_likes_sent = current_user.likes_sent
    target_user_likes_received = target_user.likes_received
    current_user_likes_sent.append(target_user.id)
    target_user_likes_received.append(current_user.id)
    current_user_users_seen.append(target_user.id)

    current_user.likes_sent = None
    target_user.likes_received = None
    current_user.users_seen = None
    model.db.session.commit()

    current_user.likes_sent = current_user_likes_sent
    target_user.likes_received = target_user_likes_received
    current_user.users_seen = current_user_users_seen
    model.db.session.commit()

    if current_user.id in target_user.likes_sent:
        current_user_matches = current_user.matches
        target_user_matches = target_user.matches
        current_user_matches.append(target_user.id)
        target_user_matches.append(current_user.id)
        current_user.matches = None
        target_user.matches = None
        model.db.session.commit()

        current_user.matches = current_user_matches
        target_user.matches = target_user_matches
        model.db.session.commit()

    return redirect(url_for('index'))


@app.route('/user/dislike/<user_id>', methods=['POST'])
@login_required
def dislike_user(user_id):
    """Dislike a user.
    Adds the disliked user to the current user's list of seen users.
    """
    current_user = model.User.get_by_id(session['user_id'])
    target_user = model.User.get_by_id(user_id)

    current_user_users_seen = current_user.users_seen
    current_user.users_seen = None
    model.db.session.commit()

    current_user_users_seen.append(target_user.id)
    current_user.users_seen = current_user_users_seen
    model.db.session.commit()
    return redirect(url_for('index'))

@app.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    name = 'John Doe'
    age = 25
    gender = 'male'
    interests = 'Sports, Music, Travel'
    description = 'I am very rich.'
    profileUrl = 'eg-profile-photo.jpg'
    return render_template('match.html', profile_user_id=12, name=name, age=age, gender=gender, interests=interests, description=description, profile_photo=profileUrl)


@app.route('/profile/<user_id>', methods=['GET'])
@login_required
def profile(user_id):
    """Render the user's profile page."""
    profile = model.UserProfile.get_by_user_id(user_id)
    isCurrentUser = str(user_id) == str(session['user_id'])
    return render_template('profile.html', profile=profile, isCurrentUser=isCurrentUser)


@app.route('/profile/<user_id>/photo', methods=['POST'])
@login_required
def photo_upload(user_id):
    """Upload a user's profile photo.

    Saves the uploaded file, resizes and crops it, updates the user's profile with the photo URL,
    and commits the changes to the database.

    """
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
    width, height = image.size
    #crop to 500*500
    left = (width - 500) // 2
    top = (height - 500) // 2
    right = left + 500
    bottom = top + 500

    cropped_image = image.crop((left, top, right, bottom))
    cropped_filename = filename + '_cropped' + extension
    cropped_save_path = os.path.join(app.config['UPLOAD_FOLDER'], cropped_filename)
    cropped_image.save(cropped_save_path)

    photo_url = f'{cropped_filename}'
    profile = model.UserProfile.get_by_user_id(user_id)
    profile.photo = photo_url

    model.db.session.add(profile)
    model.db.session.commit()
    return redirect(url_for('profile', user_id=user_id))

def allowed_file_size(file):
    """Check if the uploaded file size is within the limit."""
    max_size = 20 * 1024 * 1024  # 20MB
    return len(file.read()) <= max_size


@app.route('/profile/<user_id>', methods=['POST'])
@login_required
def profile_update(user_id):
    """Update a user's profile.

    Retrieves the form data, converts the birthday string to a datetime object,
    updates the user's profile with the new data, and commits the changes to the database.

    """
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


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    user_id = session.get('user_id')
    user = model.User.get_by_id(user_id)
    matches = user.matches
    user_profiles = model.UserProfile.get_with_user_ids(matches)
    messages_sent = model.Message.get_message_as_sender(user_id)
    messages_received = model.Message.get_message_receiver(user_id)

    message_by_friend_id = {}
    for message in messages_sent:
        if not message_by_friend_id[message.receiver_id]:
            message_by_friend_id[message.receiver_id] = []
        message_by_friend_id[message.receiver_id].append(message)
    
    for message in messages_received:
        if not message_by_friend_id[message.sender_id]:
            message_by_friend_id[message.sender_id] = []
        message_by_friend_id[message.sender_id].append(message)

    message_by_friend_id_str = json.dumps(message_by_friend_id)
    return render_template('chat.html',
                           friends=user_profiles,
                           message_by_friend_id_str=message_by_friend_id_str)

@socketio.on('message')
def handle_message(data):
    message = data['message']
    timestamp = data['timestamp']
    model.db.session.add(model.Message.create(
        int(data['sender']),
        session.get('user_id'),
        message,
        timestamp
    ))
    model.db.session.commit()
    sender_profile = model.UserProfile.get_by_user_id(data['sender'])

    socketio.emit('reply', {
        'message': message,
        'timestamp': timestamp,
        'name': f'{sender_profile.firstname} {sender_profile.lastname}' if sender_profile.user_id != session.get('user_id') else 'Me'
    })

# Restful APIs
@app.route('/api/profile/userid/<id>', methods=['GET'])
def get_user_profile(id):
    """Retrieve a user's profile based on the user ID."""
    profile = model.UserProfile.get_by_user_id(id)
    return jsonify(profile)


@app.route('/api/user/<id>', methods=['GET'])
def get_user(id):
    """Retrieve a user's information based on the user ID."""
    user = model.User.get_by_id(id)
    del user.password
    return jsonify(user)


@app.route('/api/profile/<id>', methods=['POST'])
def update_user_profile(id):
    """Update a user's profile."""
    profile = model.UserProfile.get_by_user_id(id)
    # Update the profile attributes based on the request data
    if 'firstname' in request.json:
        profile.firstname = request.json['firstname']
    if 'lastname' in request.json:
        profile.lastname = request.json['lastname']
    if 'gender' in request.json:
        profile.gender = request.json['gender']
    if 'description' in request.json:
        profile.description = request.json['description']
    if 'birthday' in request.json:
        birthday = request.json['birthday']
        date_obj = datetime.strptime(birthday, "%Y-%m-%d")
        profile.birthday = date_obj

    model.db.session.commit()

    return jsonify(profile)

def setup_testuser(test_user):
    model.db.session.add(model.User.create(test_user['username'], test_user['password']))
    model.db.session.commit()
    user = model.User.get_by_username(test_user['username'])

    model.db.session.add(model.UserProfile.create(user.id))
    model.db.session.commit()

    profile = model.UserProfile.get_by_user_id(user.id)
    profile.photo = test_user['photo']
    profile.firstname = test_user['firstname']
    profile.lastname = test_user['lastname']
    profile.birthday = datetime(test_user['birth_year'], test_user['birth_mon'], test_user['birth_day'])
    profile.description = test_user['description']
    profile.interests = []
    profile.gender = test_user['gender']
    user.profile = profile.id
    user.matches = []
    user.likes_sent = []
    user.likes_received = []
    user.messages_sent = []
    user.messages_received = []
    user.users_seen = []
    model.db.session.commit()

@app.route('/test_users', methods=['GET'])
def setup_test_users():
    data = {}
    try:
        with app.open_resource("static/data.json") as file:
            data = json.load(file)
    except FileNotFoundError:
        pass
    for test_user in data:
        setup_testuser(test_user)
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    """Connect to the database."""
    model.connect_to_db(app)
    socketio.run(app, host='127.0.0.1', debug=True)

