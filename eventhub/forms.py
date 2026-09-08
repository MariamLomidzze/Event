from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, TextAreaField, DateField, \
    FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    NumberRange, ValidationError

from models import User, Event


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    short_description = StringField(
        'Short Description', validators=[DataRequired(), Length(max=300)]
    )
    full_description = TextAreaField('Full Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=150)])
    event_date = DateField('Event Date', validators=[DataRequired()], format='%Y-%m-%d')
    ticket_price = FloatField(
        'Ticket Price', validators=[NumberRange(min=0)], default=0.0
    )
    organizer = StringField('Organizer', validators=[DataRequired(), Length(max=150)])
    category = SelectField('Category', choices=[(c, c) for c in Event.CATEGORIES])
    image = FileField('Event Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save Event')


class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Update')

    def validate_email(self, field):
        if field.data.lower() != current_user.email:
            user = User.query.filter_by(email=field.data.lower()).first()
            if user:
                raise ValidationError('This email is already registered.')
