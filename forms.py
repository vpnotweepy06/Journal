from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    
class EntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    tags = StringField("Tags (comma-separated)")
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Save")
