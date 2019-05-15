from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from database_setup import Base,User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def connect(self):
        """ Connect to database"""
        engine = create_engine('sqlite:///cantinadesantiago.db')
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind = engine)
        session = DBSession()
        return session

    def validate_email(self, email):
        session = self.connect()
        user = session.query(User).filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')