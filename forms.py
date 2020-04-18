from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username:', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField(
        'Password:', validators=[DataRequired(message="Please enter a password"), EqualTo('confirmPassword', message="Passwords must match")])
    confirmPassword = PasswordField(
        'Repeat Password:', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username:', [Length(min=4, max=25)])
    password = PasswordField('Password:', [DataRequired()])
    submit = SubmitField('Log In')


class SearchForm(FlaskForm):

    search_select = SelectField("Search by: ", choices=[
        ('isbn_id', 'ISBN #'), ('author', 'Author'), ('title', 'Title')], default='title')
    search_value = StringField('Search for Book', validators=[DataRequired()])
    submit = SubmitField('Find my book!')


class ReviewForm(FlaskForm):
    rating = SelectField(
        "Rating(1-5):", choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], validators=[DataRequired("Please select rating")])
    text = StringField("Review: ", widget=TextArea())
    submit = SubmitField('Submit Review')
