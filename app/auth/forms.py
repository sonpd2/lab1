from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from flask_babel import _, lazy_gettext as _l
import safe

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={"placeholder": "Password"})
    recaptcha = RecaptchaField()
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    phone_number = StringField(_l('Phone Number'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit_create_user = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different phone number.'))

    def validate_password(self, password):
        check = safe.check(password.data)
        if repr(check) in ('terrible','simple'):
            raise ValidationError(_l(f'A {repr(check)} password. Please use a different password.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))
    
    def validate_password(self, password):
        check = safe.check(password.data)
        if repr(check) in ('terrible', 'simple'):
            raise ValidationError(_l(f'A {repr(check)} password. Please use a different password.'))
