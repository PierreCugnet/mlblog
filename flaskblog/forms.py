# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flaskblog.models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(),Length(min = 2, max = 20)])
    email = StringField("Email", validators = [DataRequired(), Email()])
    
    password = PasswordField("Password", validators=[DataRequired()])
    
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    
    submit = SubmitField("Sign up")
    
    def validate_username(self,username):
        user = User.query.filter_by(username = username.data).first()
        if user :
            raise ValidationError('That username is already taken, please choose a different one')
    
    def validate_email(self,email):
        user = User.query.filter_by(email = email.data).first()
        if user :
            raise ValidationError('That email is already taken, please choose a different one')
    
class LoginForm(FlaskForm):

    email = StringField("Email", validators = [DataRequired(), Email()])
    
    password = PasswordField("Password", validators=[DataRequired()])
    
    remember = BooleanField("Remember me")
    
    submit = SubmitField("Log in")
    

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(),Length(min = 2, max = 20)])
    email = StringField("Email", validators = [DataRequired(), Email()])
    
    picture = FileField(label = "Update your profile image", validators=[FileAllowed(["jpeg","png","jpg"])])
    
    submit = SubmitField("Update")
    
    def validate_username(self,username):
        if username.data != current_user.username:
            user = User.query.filter_by(username = username.data).first()
            if user :
                raise ValidationError('That username is already taken, please choose a different one')
    
    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email = email.data).first()
            if user :
                raise ValidationError('That email is already taken, please choose a different one')
        
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    
    content = TextAreaField("Content", validators=[DataRequired()])
    
    submit = SubmitField("Post")

class RequestResetForm(FlaskForm):
    email = StringField("Email", validators = [DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")
    
      
    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email = email.data).first()
            if user is None:
                raise ValidationError('If an account with this email address exists, a password reset message will be sent shortly.')
        
class ResetPasswordForm(FlaskForm):

    password = PasswordField("Password", validators=[DataRequired()])
    
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
  
    submit = SubmitField("Reset Password")
    
class CatsAndDogsPredictionForm(FlaskForm):
    
    picture = FileField(label = "Add a photo of a cat or a dog", validators=[FileAllowed(["jpeg","png","jpg"])])
    
    submit = SubmitField("Submit")