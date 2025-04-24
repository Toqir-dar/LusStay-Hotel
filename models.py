from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')

    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


    def __repr__(self):
        return f'<User {self.name}>'


class Room(db.Model):
    __tablename__ = 'rooms'

    r_id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(10), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0.0)

    bookings = db.relationship('Booking', backref='room', lazy=True)
    reviews = db.relationship('Review', backref='room', lazy=True)

    @property
    def average_rating(self):
        reviews = Review.query.filter_by(room_id=self.id).all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)

    def __repr__(self):
        return f'<Room {self.room_no}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    b_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.r_id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='confirmed')



    def __repr__(self):
        return f'<Booking {self.b_id} - Room {self.room_id}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.r_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review by User {self.user_id} for Room {self.room_id}>'
