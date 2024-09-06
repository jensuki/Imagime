from flask_wtf import FlaskForm
from wtforms import StringField, FileField, PasswordField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Email, Length, URL, Optional
from flask_wtf.file import FileAllowed

# methods to ensure user provides only one image source (not both or none)
def validate_profile_img(form, field):
    if form.profile_img_url.data and form.profile_img_file.data:
        raise ValidationError('Please provide only one image source')

def validate_post_img(form, field):
    if form.image_url.data and form.image_file.data:
        raise ValidationError('Please provide only one image source')
    elif not form.image_url.data and not form.image_file.data:
        raise ValidationError('You must provide an image URL or upload an image file')

class SignUpForm(FlaskForm):
    """Form for signing up new user to the DB"""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters')])
    profile_img_url = StringField('Profile Image URL or Attach a file below', validators=[Optional(), URL(), validate_profile_img])
    profile_img_file = FileField('Upload Profile Image', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg']), validate_profile_img])

class LoginForm(FlaskForm):
    """Form for logging in user"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class EditProfileForm(FlaskForm):
    """Form for editing a users profile"""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    profile_img_url = StringField('Profile Image URL or Attach a file below', validators=[Optional(), URL(), validate_profile_img])
    profile_img_file = FileField('Upload Profile Image', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg']), validate_profile_img])
    bio = TextAreaField('Bio')

class AddImageForm(FlaskForm):
    """Form for posting a new image"""

    image_url = StringField('Image URL or Attach a file below', validators=[URL(), Length(max=255), Optional(), validate_post_img])
    image_file = FileField('Upload Image', validators=[FileAllowed(['png', 'jpg', 'jpeg']), validate_post_img])
    description = TextAreaField('Caption', validators=[Optional()])