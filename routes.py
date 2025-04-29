from flask import Flask, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 
from models import db, User, Room, Booking, Review
from forms import RegisterForm, LoginForm, BookingForm, ReviewForm, RoomForm, UserRoleForm
from sqlalchemy.orm import joinedload
from functools import wraps


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'


db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
@login_required
def home():
    booking = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.check_in_date.desc()).first()
    return render_template('home.html', booking=booking)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_pw, phone=phone)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)  
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/rooms')
@login_required
def rooms():
    # Get filter parameters
    room_type = request.args.get('type')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    available_only = request.args.get('available')
    
    # Start with base query
    query = Room.query
    
    # Apply filters
    if room_type:
        query = query.filter(Room.type == room_type)
    
    if min_price:
        query = query.filter(Room.price >= float(min_price))
    
    if max_price:
        query = query.filter(Room.price <= float(max_price))
    
    if available_only == '1':
        query = query.filter(Room.is_available == True)
    
    # Get filtered rooms
    all_rooms = query.all()

    return render_template('rooms.html', rooms=all_rooms)

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = BookingForm()
    
    # Fetch reviews for this room
    reviews = Review.query.filter_by(room_id=room_id).order_by(Review.review_date.desc()).all()
    
    # Get average rating
    total_rating = sum(review.rating for review in reviews) if reviews else 0
    avg_rating = total_rating / len(reviews) if reviews else 0
    
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        check_in = form.check_in.data
        check_out = form.check_out.data

        if check_in >= check_out:
            flash('Check-out date must be after check-in date.', 'danger')
            return redirect(url_for('book_room', room_id=room_id))

        if not room.is_available:
            flash('Sorry, this room is already booked.', 'danger')
            return redirect(url_for('rooms'))

        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in_date=check_in,
            check_out_date=check_out
        )

        room.is_available = False
        db.session.add(booking)
        db.session.commit()

        flash('Booking successful!', 'success')
        return redirect(url_for('my_bookings'))

    return render_template('book.html', room=room, form=form, reviews=reviews, avg_rating=avg_rating)

@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.options(
        joinedload(Booking.user),
        joinedload(Booking.room)
    ).filter_by(user_id=current_user.id).all()

    return render_template('my_bookings.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    room = Room.query.get(booking.room_id)

    if booking.user_id != current_user.id:
        flash('You can only cancel your own bookings.', 'danger')
        return redirect(url_for('my_bookings'))

    room.is_available = True
    db.session.delete(booking)
    db.session.commit()

    flash('Booking cancelled successfully!', 'info')
    return redirect(url_for('my_bookings'))


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Admin dashboard
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    rooms_count = Room.query.count()
    bookings_count = Booking.query.count()
    bookings = Booking.query.all()
    users_count = User.query.count()
    
    recent_bookings = Booking.query.options(
        joinedload(Booking.user),
        joinedload(Booking.room)
    ).order_by(Booking.check_in_date.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html', 
        bookings=bookings,
        rooms_count=rooms_count,
        bookings_count=bookings_count,
        users_count=users_count,
        recent_bookings=recent_bookings
    )

# Admin Room Management
@app.route('/admin/rooms')
@login_required
@admin_required
def admin_rooms():
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/rooms/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_room():
    if request.method == 'POST':
        room_no = request.form['room_no']
        room_type = request.form['type']
        price = float(request.form['price'])
        
        # Check if room number already exists
        if Room.query.filter_by(room_no=room_no).first():
            flash('Room number already exists.', 'danger')
            return redirect(url_for('admin_add_room'))
        
        room = Room(room_no=room_no, type=room_type, price=price, is_available=True)
        db.session.add(room)
        db.session.commit()
        
        flash('Room added successfully!', 'success')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/add_room.html')

@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        room.room_no = request.form['room_no']
        room.type = request.form['type']
        room.price = float(request.form['price'])
        room.is_available = 'is_available' in request.form
        
        db.session.commit()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/edit_room.html', room=room)

@app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    

    active_bookings = Booking.query.filter_by(room_id=room_id, status='confirmed').count()
    if active_bookings > 0:
        flash('Cannot delete room with active bookings.', 'danger')
        return redirect(url_for('admin_rooms'))
    
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully!', 'info')
    return redirect(url_for('admin_rooms'))

# Admin Booking Management
@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    bookings = Booking.query.options(
        joinedload(Booking.user),
        joinedload(Booking.room)
    ).all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/<int:booking_id>')
@login_required
@admin_required
def admin_booking_detail(booking_id):
    booking = Booking.query.options(
        joinedload(Booking.user),
        joinedload(Booking.room)
    ).get_or_404(booking_id)
    return render_template('admin/booking_detail.html', booking=booking)

@app.route('/admin/bookings/cancel/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def admin_cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    room = Room.query.get(booking.room_id)
    
    booking.status = 'cancelled'
    room.is_available = True
    db.session.commit()
    
    flash('Booking cancelled successfully!', 'info')
    return redirect(url_for('admin_bookings'))

# Admin User Management
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.options(
        joinedload(Booking.room)
    ).filter_by(user_id=user_id).all()
    
    return render_template('admin/user_detail.html', user=user, bookings=bookings)

@app.route('/admin/users/role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_change_role(user_id):
    user = User.query.get_or_404(user_id)
    

    if user.id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin_users'))
    
    new_role = request.form['role']
    if new_role in ['admin', 'customer']:
        user.role = new_role
        db.session.commit()
        flash(f'User role updated to {new_role} successfully!', 'success')
    
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/edit_user.html', user=user)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)


    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))


    bookings = Booking.query.filter_by(user_id=user_id).all()
    for booking in bookings:
        room = Room.query.get(booking.room_id)
        if room:
            room.is_available = True
        db.session.delete(booking)

    db.session.delete(user)
    db.session.commit()

    flash('User and their bookings deleted successfully!', 'info')
    return redirect(url_for('admin_users'))




@app.route('/room/<int:room_id>/review', methods=['GET', 'POST'])
@login_required  # Make sure users are logged in to leave reviews
def add_review(room_id):
    # Get the room to make sure it exists
    room = Room.query.get_or_404(room_id)
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        review = form.save_review(room_id)
        flash('Your review has been submitted successfully!', 'success')
        return redirect(url_for('room_reviews', room_id=room_id))
    
    return render_template('review_form.html', form=form, room=room)

@app.route('/room/<int:room_id>/reviews')
def room_reviews(room_id):
    room = Room.query.get_or_404(room_id)
    reviews = Review.query.filter_by(room_id=room_id).order_by(Review.review_date.desc()).all()
    return render_template('room_reviews.html', room=room, reviews=reviews)

@app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    # Store room_id before deleting for redirect
    room_id = review.room_id
    
    # Delete the review
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted successfully!', 'info')
    
    # Redirect back to the room's reviews page
    return redirect(url_for('room_reviews', room_id=room_id))

@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    reviews = Review.query.options(
        joinedload(Review.user),
        joinedload(Review.room)
    ).order_by(Review.review_date.desc()).all()
    
    return render_template('admin/reviews.html', reviews=reviews)