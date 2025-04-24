from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash
from wtforms import StringField, PasswordField, DateField, SubmitField, IntegerField, TextAreaField, SelectField, FloatField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Optional
from flask_login import current_user
from wtforms.validators import InputRequired, Email, Length, EqualTo, DataRequired, ValidationError
from datetime import date
from models import db, User, Review  

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=4, max=100)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=200)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    phone = StringField('Phone', validators=[Length(max=20)])
    role = StringField('Role', default='customer', validators=[Length(max=20)])
    submit = SubmitField('Register')

    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data).first()
        if existing_user:
            raise ValidationError("That email is already taken. Please choose a different one.")

    def save_user(self):
        hashed_password = generate_password_hash(self.password.data)
        user = User(
            name=self.name.data,
            email=self.email.data,
            password=hashed_password,
            phone=self.phone.data,
            role=self.role.data
        )
        db.session.add(user)
        db.session.commit()

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

    def validate_login(self):
        user = User.query.filter_by(email=self.email.data).first()
        if user and not user.check_password(self.password.data): 
            raise ValidationError('Invalid email or password')

class BookingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])
    submit = SubmitField('Book Now')

    def validate_check_out(form, field):
        if field.data <= form.check_in.data:
            raise ValidationError("Check-out date must be after check-in date.")
        
    def validate_check_in(form, field):
        if field.data < date.today():
            raise ValidationError("Check-in date cannot be in the past.")
        
class ReviewForm(FlaskForm):
    rating = IntegerField('Rating', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message="Rating must be between 1 and 5.")
    ])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

    def save_review(self, room_id):
        review = Review(
            rating=self.rating.data,
            comment=self.comment.data,
            user_id=current_user.id,  
            room_id=room_id
        )
        db.session.add(review)
        db.session.commit()
        return review


# Admin forms
class RoomForm(FlaskForm):
    room_no = StringField('Room Number', validators=[DataRequired()])
    type = SelectField('Room Type', choices=[
        ('Standard', 'Standard'),
        ('Deluxe', 'Deluxe'),
        ('Suite', 'Suite'),
        ('Executive', 'Executive'),
        ('Family', 'Family')
    ], validators=[DataRequired()])
    price = FloatField('Price per Night', validators=[DataRequired(), NumberRange(min=0)])
    is_available = BooleanField('Available')
    submit = SubmitField('Save Room')

class UserRoleForm(FlaskForm):
    role = SelectField('Role', choices=[('customer', 'Customer'), ('admin', 'Admin')])
    submit = SubmitField('Update Role')