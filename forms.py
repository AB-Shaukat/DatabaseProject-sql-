from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    display_name = StringField('Display Name', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from wtforms import SelectField, SubmitField, TextAreaField

class ClassRegistrationForm(FlaskForm):
    available_classes = SelectField('Available Classes', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Register for Class')


class FeedbackForm(FlaskForm):
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    feedback = TextAreaField('Feedback', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class EditFeedbackForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired()])
    submit = SubmitField('Update Feedback')
