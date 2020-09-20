from flask import request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, SelectField
from wtforms.fields.html5 import EmailField, DateTimeLocalField
from wtforms.validators import ValidationError, DataRequired, Length, EqualTo, Email
from flask_wtf.file import FileField, FileAllowed
from wtforms import BooleanField, HiddenField
from flask_babel import _, lazy_gettext as _l
from app.models import User
import safe

class EditProfileForm(FlaskForm):
    name = StringField('Name',render_kw={'readonly': True})
    email = EmailField('Email address', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    password = PasswordField(_l('Confirm Password'), validators=[DataRequired()])
    submit_edit_profile = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        self.original_username = original_username
        super().__init__(*args, **kwargs)

    def validate_password(self, password):
        user = User.query.filter_by(username=self.original_username).first()
        if not user.check_password(password=password.data):
            raise ValidationError(_l('Invalid password.'))

    def validate_email(self, email):
        user = User.query.filter(User.email == email.data).first()
        if user is not None and user.username != self.original_username:
            raise ValidationError(_l('Please use a different email.'))

    def validate_phone_number(self, phone_number):
        user = User.query.filter(User.phone_number == phone_number.data).first()
        if user is not None and user.username != self.original_username:
            raise ValidationError(_l('Please use a different phone number.'))

class ChangePassForm(FlaskForm):
    old_password = PasswordField(_l('Old Password'), validators=[DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[DataRequired()])
    confirm = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('new_password')])
    submit_change_pass = SubmitField(_l('Change'))

    def __init__(self, original_username, *args, **kwargs):
        self.original_username = original_username
        super().__init__(*args, **kwargs)

    def validate_old_password(self, old_password):
        user = User.query.filter_by(username=self.original_username).first()
        if user is None or not user.check_password(password=old_password.data):
            raise ValidationError(_l('Invalid old password.'))

    def validate_new_password(self, new_password):
        user = User.query.filter_by(username=self.original_username).first()
        if user.check_password(password=new_password.data):
            raise ValidationError(_l('New password must different old password.'))

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    attach_file = FileField('Attach File', validators=[FileAllowed(ALLOWED_EXTENSIONS, "Wrong format!")])
    privacy = SelectField("Privacy", coerce=int, choices=[(0, "Public"), (1, "Private")], default=1)
    is_challenge = SelectField("Challenge", coerce=int, choices=[(0, "No"), (1, "Yes")], default=0)
    submit_post = SubmitField(_l('Submit'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_attach_file(self, is_challenge):
        if self.is_challenge.data == 1:
            if self.attach_file.data is None:
                raise ValidationError(_l('Challenge must be has a attach file.'))

class CommentForm(FlaskForm):
    post_id = HiddenField('post_id')
    body = TextAreaField('Comment something', validators=[DataRequired()])
    attach_file = FileField('Attach File', validators=[FileAllowed(ALLOWED_EXTENSIONS, 'Wrong format!')])
    submit_comment = SubmitField(_l('Submit'))

class AnswerForm(FlaskForm):
    challenge_id = HiddenField('challenge_id')
    answer = TextAreaField('Your answer', validators=[DataRequired()])
    submit_comment = SubmitField(_l('Submit'))

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit_send_message = SubmitField(_l('Submit'))

class MessageEditForm(FlaskForm):
    recipient = StringField('Recipient',render_kw={'readonly': True})
    send_date = DateTimeLocalField("Send Date",render_kw={'readonly': True})
    body = TextAreaField(_l('Message'), validators=[DataRequired(), Length(min=1, max=140)])
    submit_change_message = SubmitField(_l('Change'))
    submit_delete_message = SubmitField(_l('Delete'))

    def __init__(self, username, *args, **kwargs):
        self.username = username
        super().__init__(*args, **kwargs)


class CreateUserForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    phone_number = StringField(_l('Phone Number'), validators=[DataRequired()])
    is_active = BooleanField('Active', default= 1)
    is_admin = BooleanField('Admin', default= 0)
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
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
        if repr(check) in ('terrible', 'simple'):
            raise ValidationError(_l(f'A {repr(check)} password. Please use a different password.'))
