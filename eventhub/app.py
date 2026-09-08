import os
import secrets
import logging
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_wtf import CSRFProtect

from config import Config
from models import db, bcrypt, User, Event
from forms import RegisterForm, LoginForm, EventForm, UpdateProfileForm

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'გთხოვთ გაიაროთ ავტორიზაცია!'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
log_dir = os.path.dirname(app.config['LOG_FILE'])
os.makedirs(log_dir, exist_ok=True)
file_handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('EventHub startup')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def save_picture(form_picture, subfolder):
    """Saves an uploaded image under static/<subfolder> with a random filename
    and returns just the filename. `subfolder` is e.g. 'profile_pics' or 'event_pics'."""
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + file_extension
    picture_path = os.path.join(app.root_path, 'static', subfolder, picture_filename)
    form_picture.save(picture_path)
    return picture_filename


def get_weather_for_location(location):
    """Calls OpenWeatherMap for the current weather at an event's location."""
    api_key = app.config.get('OPENWEATHER_API_KEY')
    if not api_key:
        return None

    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': location, 'appid': api_key, 'units': 'metric'}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            'description': data['weather'][0]['description'].title(),
            'temp': round(data['main']['temp']),
        }
    except requests.exceptions.RequestException as e:
        app.logger.error(f'API request error (weather for "{location}"): {e}')
        return None
    except (KeyError, IndexError) as e:
        app.logger.error(f'API response parse error (weather for "{location}"): {e}')
        return None


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        app.logger.info(f'New user registered: {user.email}')
        flash('ანგარიში წარმატებით შეიქმნა! გთხოვთ გაიაროთ ავტორიზაცია.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            app.logger.info(f'Successful login: {user.email}')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            app.logger.warning(f'Failed login attempt for email: {form.email.data.lower()}')
            flash('იმეილი ან პაროლი არასწორია.', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    app.logger.info(f'User logged out: {current_user.email}')
    logout_user()
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Main / static pages
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')

    query = Event.query

    if category:
        query = query.filter_by(category=category)

    if sort == 'oldest':
        query = query.order_by(Event.date_posted.asc())
    elif sort == 'date':
        query = query.order_by(Event.event_date.asc())
    else:  # newest posted first (default)
        query = query.order_by(Event.date_posted.desc())

    pagination = query.paginate(
        page=page, per_page=app.config['EVENTS_PER_PAGE'], error_out=False
    )

    return render_template(
        'index.html',
        events=pagination.items,
        pagination=pagination,
        categories=Event.CATEGORIES,
        selected_category=category,
        selected_sort=sort,
    )


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'profile_pics')
            current_user.profile_image = picture_file

        current_user.name = form.name.data
        current_user.email = form.email.data.lower()
        db.session.commit()
        app.logger.info(f'Profile updated: {current_user.email}')
        flash('პროფილი განახლდა წარმატებით!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.profile_image)
    return render_template('profile.html', title='Profile', form=form, image_file=image_file)


# ---------------------------------------------------------------------------
# Event CRUD routes
# ---------------------------------------------------------------------------
@app.route('/event/new', methods=['GET', 'POST'])
@login_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        image_filename = 'default_event.jpg'
        if form.image.data:
            image_filename = save_picture(form.image.data, 'event_pics')

        event = Event(
            title=form.title.data,
            short_description=form.short_description.data,
            full_description=form.full_description.data,
            location=form.location.data,
            event_date=form.event_date.data,
            ticket_price=form.ticket_price.data,
            organizer=form.organizer.data,
            category=form.category.data,
            image=image_filename,
            author=current_user,
        )
        db.session.add(event)
        db.session.commit()
        app.logger.info(f'Event created: "{event.title}" by {current_user.email}')
        flash('ღონისძიება დაემატა წარმატებით!', 'success')
        return redirect(url_for('event_detail', event_id=event.id))

    return render_template('event_form.html', title='Add Event', form=form)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    weather = get_weather_for_location(event.location)
    return render_template('event.html', title=event.title, event=event, weather=weather)


@app.route('/event/<int:event_id>/update', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.author != current_user:
        app.logger.warning(
            f'Unauthorized edit attempt on event {event_id} by {current_user.email}'
        )
        abort(403)

    form = EventForm()
    if form.validate_on_submit():
        if form.image.data:
            event.image = save_picture(form.image.data, 'event_pics')

        event.title = form.title.data
        event.short_description = form.short_description.data
        event.full_description = form.full_description.data
        event.location = form.location.data
        event.event_date = form.event_date.data
        event.ticket_price = form.ticket_price.data
        event.organizer = form.organizer.data
        event.category = form.category.data
        db.session.commit()
        app.logger.info(f'Event edited: "{event.title}" (id={event.id}) by {current_user.email}')
        flash('ღონისძიება განახლდა!', 'success')
        return redirect(url_for('event_detail', event_id=event.id))
    elif request.method == 'GET':
        form.title.data = event.title
        form.short_description.data = event.short_description
        form.full_description.data = event.full_description
        form.location.data = event.location
        form.event_date.data = event.event_date
        form.ticket_price.data = event.ticket_price
        form.organizer.data = event.organizer
        form.category.data = event.category

    return render_template('event_form.html', title='Update Event', form=form, event=event)


@app.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.author != current_user:
        app.logger.warning(
            f'Unauthorized delete attempt on event {event_id} by {current_user.email}'
        )
        abort(403)

    title = event.title
    db.session.delete(event)
    db.session.commit()
    app.logger.info(f'Event deleted: "{title}" (id={event_id}) by {current_user.email}')
    flash('ღონისძიება წაიშალა.', 'info')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
