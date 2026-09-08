from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(db.String(255), nullable=False, default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events = db.relationship('Event', backref='author', lazy=True,
                              cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'User("{self.name}", "{self.email}")'


class Event(db.Model):
    CATEGORIES = ['Music', 'Tech', 'Art', 'Sport', 'Education', 'Other']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    short_description = db.Column(db.String(300), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False, default=0.0)
    organizer = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    image = db.Column(db.String(255), nullable=False, default='default_event.jpg')

    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def is_upcoming(self):
        return self.event_date >= date.today()

    def __repr__(self):
        return f'Event("{self.title}", "{self.event_date}")'
