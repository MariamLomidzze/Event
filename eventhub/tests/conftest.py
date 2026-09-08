import sys
import os
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from models import User, Event


@pytest.fixture
def app():
    flask_app = app_module.app
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
    )

    with flask_app.app_context():
        app_module.db.create_all()
        yield flask_app
        app_module.db.session.remove()
        app_module.db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return app_module.db


@pytest.fixture
def sample_user(app, db):
    user = User(name='Test User', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_user(app, db):
    user = User(name='Other User', email='other@example.com')
    user.set_password('password456')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_event(app, db, sample_user):
    event = Event(
        title='Test Concert',
        short_description='A short description',
        full_description='A much longer full description of the event.',
        location='Tbilisi',
        event_date=date(2026, 12, 1),
        ticket_price=25.0,
        organizer='Test Organizer',
        category='Music',
        user_id=sample_user.id,
    )
    db.session.add(event)
    db.session.commit()
    return event


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password},
                        follow_redirects=True)
