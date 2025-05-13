# Import necessary libraries
import json
import os
import io
import psycopg2
from datetime import date, timedelta, datetime
from flask import Flask,render_template, request, jsonify,flash,url_for,redirect,session,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import DecimalField, EmailField, IntegerField,  StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from flask_login import UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, ValidationError, NumberRange, Optional
from sqlalchemy.sql import func
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user,LoginManager
from flask_migrate import Migrate
from functools import wraps
from flask import redirect, url_for, flash
from flask import request, render_template, make_response


# from flask import Flask
# from flask_mail import Mail, Message

# Initialize Flask application
app=Flask(__name__)

# Set Flask application configurations
db=SQLAlchemy()
DB_NAME="database.db"
app.config['SECRET_KEY']='david'
app.config['UPLOAD_FOLDER']='static/files'
app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Email server configuration
# app.config['MAIL_SERVER'] = "smtp.googlemail.com"
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USERNAME'] = "planetgpinkissuites@gmail.com"
# app.config['MAIL_PASSWORD'] = 'qjfzmdutgklkikby'
db.init_app(app)
bcrypt= Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate=Migrate(app,db)

 


#----------------------------------------------------------------
#Database Creation
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)



class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Reserved') 


    def calculate_total_amount(self):
        # Assuming Room model has a price attribute
        room = Room.query.get(self.room_id)
        num_nights = (self.check_out_date - self.check_in_date).days
        return room.price * num_nights

    def __init__(self, first_name, last_name, phone_number, email, check_in_date, check_out_date, room_id, total_amount,status):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.email = email
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.room_id = room_id
        self.status = status
        self.total_amount = self.calculate_total_amount()
   



class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Numeric type for price

    # This defines a relationship to Booking and sets the backref as 'room' in Booking.
    bookings = db.relationship('Booking', backref='room', lazy=True)
     # This defines a relationship to Reservation and sets the backref as 'room' in Reservation.
    reservations = db.relationship('Reservation', backref='room', lazy=True)

    def __repr__(self):
        return f"<Room {self.room_number}, Type {self.room_type}>"
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    id_type = db.Column(db.String(50), nullable=True)
    id_number = db.Column(db.String(50), nullable=True)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    children_number = db.Column(db.Integer, nullable=False)
    adults_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)  # ForeignKey for Guest
    total_amount = db.Column(db.Float, nullable=False)

     

    def calculate_total_amount(self):
            # Fetch the room price
            room = Room.query.get(self.room_id)
            # Calculate the number of nights
            num_nights = (self.check_out_date - self.check_in_date).days
            # Ensure that the minimum number of nights is 1
            if num_nights < 1:
                num_nights = 1
            # Return the total amount
            return room.price * num_nights

    def __init__(self, first_name, last_name, phone_number, email, address, id_type, id_number, check_in_date, check_out_date, room_id,guest_id, total_amount,children_number,adults_number,status):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.email = email
        self.address = address
        self.id_type = id_type
        self.id_number = id_number
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.room_id = room_id
        self.guest_id = guest_id 
        self.children_number = children_number
        self.adults_number = adults_number
        self.status = status
        self.total_amount = self.calculate_total_amount()
   
    
class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)  # Ensure phone number is unique
    email = db.Column(db.String(120), nullable=False, unique=True)  # Email remains unique
    address = db.Column(db.String(200), nullable=False)
    id_type = db.Column(db.String(50), nullable=True)
    id_number = db.Column(db.String(50), nullable=True)

    # Relationship to Booking
    bookings = db.relationship('Booking', backref='guest', lazy=True)
#----------------------------------------------------------------
# FORM CREATION
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), DataRequired() , Length(min=4, max=20)], render_kw= {"placeholder":"Enter Username"})
    password = PasswordField('Password', validators=[InputRequired(), DataRequired(), Length(min=7, max=20)], render_kw= {"placeholder":"Enter Password"})
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), DataRequired(), EqualTo('password'), Length(min=7, max=20)], render_kw= {"placeholder":"Confirm Password"})
    role = SelectField('Role', choices=[('admin', 'Admin'),('manager', 'Manager'), ('receptionist', 'Receptionist')], validators=[DataRequired()])
    submit = SubmitField('Register')


    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()

        if existing_user_username:
            raise ValidationError('Username already exists. Please choose a different username.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), DataRequired() , Length(min=4, max=20)], render_kw= {"placeholder":"Enter Username"})
    password = PasswordField('Password', validators=[InputRequired(), DataRequired(), Length(min=7, max=20)], render_kw= {"placeholder":"Enter Password"})
    submit = SubmitField('Login')



class ReservationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    room_id = SelectField('Room', coerce=int, validators=[DataRequired()])
    phone_number = IntegerField('Phone Number', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Reserved', 'Reserved')], validators=[DataRequired()])
    total_amount = DecimalField('Total Amount (₦)', places=2, render_kw={'readonly': True})  # Remove validator
    submit = SubmitField('Save Reservation')

    
    def calculate_total_price(self):
        # Calculate number of nights
        nights = (self.check_out_date.data - self.check_in_date.data).days
        if nights <= 0:
            nights = 1  # Minimum of one night

        # Fetch room details
        room = Room.query.get(self.room_id.data)
        if room:
            # Calculate total price
            return room.price * nights
        return 0

class RoomForm(FlaskForm):
    room_number = IntegerField('Room Number', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[('Standard', 'Standard'), ('Executive', 'Executive'), ('Executive Wing B', 'Executive Wing B'), ('Exclusive', 'Exclusive'), ('Deluxe', 'Deluxe'), ('Suite', 'Suite')], validators=[DataRequired()])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Occupied', 'Occupied'), ('Maintenance', 'Maintenance'), ('Cleaning', 'Cleaning')], validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Save')

class BookingForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    room_id = SelectField('Room', coerce=int, validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=11)])
    email = EmailField('Email', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    id_type = SelectField('ID Type', choices=[('NIN', 'NIN'), ('DRIVERS LICENSE', 'Driver\'s License'), ('ID CARD', 'ID Card')], validators=[Optional()])
    id_number = IntegerField('ID Number', validators=[Optional()])
    adults_number=IntegerField('Adults Number', validators=[DataRequired()])
    children_number=StringField('Children Number', validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', format='%Y-%m-%d')
    status = SelectField('Status', choices=[('Pending', 'Pending')], validators=[DataRequired()])
    total_amount = DecimalField('Total Amount (₦)', places=2, render_kw={'readonly': True})  # Remove validator
    
    submit = SubmitField('Submit')

    
    def __init__(self, readonly_room=False, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        if readonly_room:
            # If room_id should be readonly, fetch the room and set its data
            room = Room.query.get(kwargs.get('room_id'))
            if room:
                self.room_id.choices = [(room.id, f'Room {room.room_number} ({room.room_type}) - ₦{room.price}')]
                self.room_id.render_kw = {'readonly': True}  # Make the room_id readonly
        else:
            # For regular bookings, populate available rooms as choices
            available_rooms = Room.query.filter_by(status='Available').all()
            self.room_id.choices = [(room.id, f'Room {room.room_number} ({room.room_type}) - ₦{room.price}') for room in available_rooms]

    def calculate_total_price(self):
        # Calculate number of nights
        nights = (self.check_out_date.data - self.check_in_date.data).days
        if nights <= 0:
            nights = 1  # Minimum of one night

        # Fetch room details
        room = Room.query.get(self.room_id.data)
        if room:
            # Calculate total price
            return room.price * nights
        return 0
# ----------------------------------------------------------------  

def role_required(allowed_roles):
    """Decorator to restrict access based on roles."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.role in allowed_roles:
                return func(*args, **kwargs)
            flash("You do not have access to this page.", "danger")
            return redirect(url_for('dashboard'))  # Redirect to a safe page
        return wrapper
    return decorator
  
# Define the homepage route
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])

def home():

   # Render the homepage template for GET requests
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])

def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
       
    return render_template('login.html', form=form)

from datetime import date
@app.route('/dashboard')
@login_required
def dashboard():

    # Get the current date
    today = date.today()

    # Fetch all reservations and dynamically update room statuses
    reservations = Reservation.query.all()
    

    # Fetch all bookings with status 'Checked In'
    total_bookings = Booking.query.filter_by(status='Checked In').all()

    # Calculate total number of adults and children in all checked-in bookings
    total_people = sum([booking.adults_number + booking.children_number for booking in total_bookings])

    # Fetch total reservations (not yet checked in)
    total_reservations = Reservation.query.filter_by(status='Reserved').count()

    # Fetch total occupied rooms
    total_rooms_occupied = Room.query.filter_by(status='Occupied').count()

    # Fetch total available rooms
    total_rooms_available = Room.query.filter_by(status='Available').count()

    # Fetch total available rooms and list them
    available_rooms = Room.query.filter_by(status='Available').all()

    # Fetch total dirty rooms
    total_rooms_dirty = Room.query.filter_by(status='Dirty').count()

    # Get current date
    today = date.today()

    # Fetch guests arriving today (check-in date is today and status is Reserved)
    guests_arriving_today = Reservation.query.filter_by(check_in_date=today, status='Reserved').all()

    # Fetch guests departing today (check-out date is today and status is Checked In)
    guests_departing_today = Booking.query.filter_by(check_out_date=today, status='Checked In').all()

    # Fetch total revenue for today
    active_bookings = Booking.query.filter(
        Booking.check_in_date <= today,
        Booking.check_out_date >= today
    ).all()

    total_revenue_today = 0
    for booking in active_bookings:
        # Calculate the number of nights
        number_of_nights = (booking.check_out_date - booking.check_in_date).days

        # If guest is checking out today, count the full amount
        if booking.check_out_date == today:
            total_revenue_today += booking.total_amount
        elif number_of_nights > 0:  # Avoid division by zero
            daily_rate = booking.total_amount / number_of_nights
            total_revenue_today += daily_rate
        else:
            # Handle the case where number_of_nights is 0
            daily_rate = booking.total_amount  # Maybe assign the full amount if it's a single day stay
            total_revenue_today += daily_rate

    # Fetch recent bookings (last 5)
    recent_bookings = Booking.query.order_by(Booking.check_in_date.desc()).limit(5).all()

    return render_template(
        'dashboard.html', total_people=total_people,
        total_bookings=len(total_bookings),  # Total count of checked-in bookings
        total_reservations=total_reservations,
        total_rooms_available=total_rooms_available,
        total_rooms_dirty=total_rooms_dirty,
        total_revenue=total_revenue_today,  # Today's revenue
        recent_bookings=recent_bookings,
        total_rooms_occupied=total_rooms_occupied,
        guests_arriving_today=guests_arriving_today,
        guests_departing_today=guests_departing_today,
        available_rooms=available_rooms  # Pass available rooms to template
    )


# Route to view all reservations
@app.route('/reservations', methods=['GET'])
@login_required
def manage_reservations():
    # Filter reservations by status or guest name
    status = request.args.get('status', 'Reserved')  # Default to Reserved
    last_name = request.args.get('last_name', '')

    # Start with the base query
    query = Reservation.query.filter(Reservation.status =='Reserved')  # Filter for 'Reserved' status


    if last_name:
        query = query.filter(Reservation.last_name.like(f'%{last_name}%'))

    # Order by reservation ID in descending order
    reservations = query.order_by(Reservation.id.desc()).all()

    return render_template('manage_reservations.html', reservations=reservations, status=status, last_name=last_name)



# Route to add a new reservation
@app.route('/reservations/add', methods=['GET', 'POST'])
@login_required
def add_reservation():
    form = ReservationForm()

    # Initially display all rooms except those under maintenance
    all_rooms = Room.query.filter(Room.status != 'Maintenance').all()
    form.room_id.choices = [
        (room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') 
        for room in all_rooms
    ]

    # Handle form submission
    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data

    

        # Check if dates are in the past
        today = date.today()
        if check_in < today or check_out < today:
            flash('Check-in and Check-out dates cannot be in the past.', 'danger')
            return render_template('add_reservation.html', form=form)

        # Check for room availability before submission
        room_id = form.room_id.data
        conflicting_reservation = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status != 'Checked Out',
            (Reservation.check_in_date < check_out) & 
            (Reservation.check_out_date > check_in)
        ).first()

        conflicting_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status == 'Checked In',
            (Booking.check_in_date < check_out) & 
            (Booking.check_out_date > check_in)
        ).first()

        if conflicting_reservation or conflicting_booking:
            flash('The selected room is unavailable for the chosen dates. Please choose a different room or date range.', 'danger')
            return render_template('add_reservation.html', form=form)

        # Proceed to create the reservation if no conflicts
        new_reservation = Reservation(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            check_in_date=check_in,
            check_out_date=check_out,
            room_id=room_id,
            total_amount=form.calculate_total_price(),
            status=form.status.data
        )

        db.session.add(new_reservation)
        db.session.commit()
        flash('Reservation successfully created!', 'success')
        return redirect(url_for('manage_reservations'))

    return render_template('add_reservation.html', form=form)



@app.route('/rooms/filter', methods=['GET'])
def filter_rooms():
    check_in_date = request.args.get('check_in_date', None)
    check_out_date = request.args.get('check_out_date', None)

    if check_in_date and check_out_date:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')

        # Exclude rooms with overlapping bookings or reservations
        unavailable_room_ids = db.session.query(Room.id).filter(
            Room.id.in_(
                db.session.query(Reservation.room_id).filter(
                    (Reservation.check_in_date < check_out) & 
                    (Reservation.check_out_date > check_in) & 
                    (Reservation.status != 'Checked Out')
                ).union(
                    db.session.query(Booking.room_id).filter(
                        (Booking.check_in_date < check_out) & 
                        (Booking.check_out_date > check_in) & 
                        (Booking.status == 'Checked In')
                    )
                )
            )
        ).all()

        # Flatten unavailable room IDs
        unavailable_room_ids = [room_id[0] for room_id in unavailable_room_ids]

        # Get available rooms
        available_rooms = Room.query.filter(
            Room.status != 'Maintenance',
            ~Room.id.in_(unavailable_room_ids)
        ).all()

        return jsonify({
            'rooms': [
                {'id': room.id, 'room_number': room.room_number, 
                 'room_type': room.room_type, 'price': room.price}
                for room in available_rooms
            ]
        })

    return jsonify({'rooms': []})





# Route to edit a reservation
@app.route('/reservations/edit/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationForm(obj=reservation)

    # Fetch the current room for the reservation
    current_room = Room.query.get(reservation.room_id)

    # Fetch available rooms excluding those with conflicts
    available_rooms = Room.query.filter(
        (Room.status != 'Maintenance') | (Room.id == current_room.id)  # Include current room
    ).all()

    room_choices = [
        (room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})')
        for room in available_rooms
    ]
    form.room_id.choices = room_choices

    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data
        room_id = form.room_id.data

        # Ensure no conflicts with reservations or bookings
        conflicting_reservation = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.id != reservation_id,  # Exclude current reservation
            Reservation.status != 'Checked Out',
            (Reservation.check_in_date < check_out) & (Reservation.check_out_date > check_in)
        ).first()

        conflicting_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status == 'Checked In',
            (Booking.check_in_date < check_out) & (Booking.check_out_date > check_in)
        ).first()

        if conflicting_reservation or conflicting_booking:
            conflict_source = conflicting_reservation if conflicting_reservation else conflicting_booking
            conflict_type = 'reservation' if conflicting_reservation else 'booking'
            conflict_msg = (
                f"The selected room is unavailable for the chosen dates due to an existing {conflict_type}. "
                f"Room {current_room.room_number} is already reserved from "
                f"{conflict_source.check_in_date.strftime('%Y-%m-%d')} to "
                f"{conflict_source.check_out_date.strftime('%Y-%m-%d')}."
            )
            flash(conflict_msg, 'danger')
            return render_template('edit_reservation.html', form=form, reservation=reservation)

        # Update reservation details
        reservation.first_name = form.first_name.data
        reservation.last_name = form.last_name.data
        reservation.email = form.email.data
        reservation.check_in_date = check_in
        reservation.check_out_date = check_out
        reservation.room_id = room_id
        reservation.total_amount = form.calculate_total_price()
        reservation.status = form.status.data

        db.session.commit()
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('manage_reservations'))

    return render_template('edit_reservation.html', form=form, reservation=reservation)


@app.route('/rooms/filters', methods=['GET'])
def filters_rooms():
    check_in_date = request.args.get('check_in_date')
    check_out_date = request.args.get('check_out_date')
    current_room_id = request.args.get('current_room_id')  # Pass the current room ID

    if check_in_date and check_out_date:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')

        # Fetch conflicting room IDs
        unavailable_room_ids = db.session.query(Room.id).filter(
            Room.id.in_(
                db.session.query(Reservation.room_id).filter(
                    (Reservation.check_in_date < check_out) &
                    (Reservation.check_out_date > check_in) &
                    (Reservation.status != 'Checked Out')
                ).union(
                    db.session.query(Booking.room_id).filter(
                        (Booking.check_in_date < check_out) &
                        (Booking.check_out_date > check_in) &
                        (Booking.status == 'Checked In')
                    )
                )
            )
        ).all()

        # Convert tuples to flat list
        unavailable_room_ids = [room_id[0] for room_id in unavailable_room_ids]

        # Exclude conflicts but always include the current room
        available_rooms = Room.query.filter(
            ~Room.id.in_(unavailable_room_ids) | (Room.id == int(current_room_id)),
            Room.status != 'Maintenance'
        ).all()

        return jsonify({
            'rooms': [
                {'id': room.id, 'room_number': room.room_number, 'room_type': room.room_type, 'price': room.price}
                for room in available_rooms
            ]
        })

    return jsonify({'rooms': []})


# Route to delete a reservation
@app.route('/reservations/delete/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # Update the room's status to "Available"
    room = Room.query.get(reservation.room_id)
    room.status = 'Available'

    # Delete reservation
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted successfully!', 'success')
    return redirect(url_for('manage_reservations'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/rooms', methods=['GET', 'POST'])
@login_required
def manage_rooms():

    # Handle filtering
    room_type = request.args.get('room_type', '')
    status = request.args.get('status', '')
    
    query = Room.query
    if room_type:
        query = query.filter_by(room_type=room_type)
    if status:
        query = query.filter_by(status=status)
    
    rooms = query.all()
    
    return render_template('manage_rooms.html', rooms=rooms, room_type=room_type, status=status)

@app.route('/rooms/add', methods=['GET', 'POST'])
@login_required
def add_room():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            room_number=form.room_number.data,
            room_type=form.room_type.data,
            status=form.status.data,
            price=form.price.data
        )
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('manage_rooms'))
    return render_template('add_room.html', form=form)

@app.route('/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    if form.validate_on_submit():
        room.room_number = form.room_number.data
        room.room_type = form.room_type.data
        room.status = form.status.data
        room.price = form.price.data
        db.session.commit()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('manage_rooms'))
    return render_template('edit_room.html', form=form, room=room)

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully!', 'success')
    return redirect(url_for('manage_rooms'))

@app.route('/rooms/clean/<int:room_id>', methods=['POST'])
@login_required
def mark_room_clean(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status == 'Dirty':
        room.status = 'Available'
        db.session.commit()
        flash(f'Room {room.room_number} is now available.', 'success')
        
    return redirect(url_for('housekeeping'))

@app.route('/housekeeping', methods=['GET'])
@login_required
def housekeeping():
    # Fetch rooms that are either "Occupied" or "Dirty" (to be cleaned)
  rooms = Room.query.filter(Room.status.in_(['Occupied', 'Dirty','Available'])).order_by(Room.room_number).all()
  return render_template('housekeeping.html', rooms=rooms)

@app.route('/rooms/edit_status/<int:room_id>', methods=['POST'])
@login_required
def edit_room_status(room_id):
    room = Room.query.get_or_404(room_id)

    # Logic to update the room status based on the current state
    if room.status == 'Occupied':
        room.status = 'Dirty'
    elif room.status == 'Dirty':
        room.status = 'Available'
    elif room.status == 'Available':
        room.status = 'Dirty'

    db.session.commit()
    flash(f"Room status updated to {room.status}!", 'success')
    return redirect(url_for('housekeeping'))

@app.route('/bookings', methods=['GET'])
def manage_bookings():
    
    phone_number = request.args.get('phone_number','')
    last_name = request.args.get('last_name','')

    bookings = Booking.query

    
    

    if phone_number:
        bookings = bookings.filter(Booking.phone_number.like(f'%{phone_number}%'))

    if last_name:
        bookings = bookings.filter(Booking.last_name.like(f'%{last_name}%'))

    bookings = bookings.order_by(Booking.id.desc()).all()

    return render_template('manage_bookings.html', bookings=bookings,phone_number=phone_number,last_name=last_name)

@app.route('/bookings/add', methods=['GET', 'POST'])
def add_booking():
    form = BookingForm()
    # Fetch rooms that are either "Available" 
    available_rooms = Room.query.filter(Room.status.in_(['Available'])).all()

 # Populate the room choices in the form
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]

    # Automatically set the check-in date to today and mark it as readonly
    form.check_in_date.data = date.today()

    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data
        room_id = form.room_id.data

        # Validate if the selected room is still available for the dates
        conflicting_reservation = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status != 'Checked Out',
            (Reservation.check_in_date < check_out) &
            (Reservation.check_out_date > check_in)
        ).first()

        # if conflicting_reservation:
        #     flash('The selected room is already reserved for the chosen dates. Please choose a different room or date range.', 'danger')
        #     return render_template('add_booking.html', form=form)

        # Proceed with the booking if no conflicts
        guest = Guest.query.filter_by(email=form.email.data).first()
        if guest is None:
            # Create a new guest if not already in the database
            guest = Guest(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone_number=form.phone_number.data,
                email=form.email.data,
                address=form.address.data,
                id_type=form.id_type.data,
                id_number=form.id_number.data
            )
            db.session.add(guest)
            db.session.commit()

        # Create the new booking
        new_booking = Booking(
            guest_id=guest.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data,
            id_type=form.id_type.data,
            id_number=form.id_number.data,
            room_id=room_id,
            children_number=form.children_number.data,
            adults_number=form.adults_number.data,
            status=form.status.data,
            check_in_date=check_in,
            check_out_date=check_out,
            total_amount=form.total_amount.data
        )

        # Update reservation status if linked
        reservation = Reservation.query.filter_by(room_id=room_id).first()
        if reservation:
            reservation.status = 'Checked In'

        db.session.add(new_booking)
        db.session.commit()
        flash('Booking added successfully!', 'success')
        return redirect(url_for('manage_bookings'))

    return render_template('add_booking.html', form=form)

@app.route('/rooms/filter_for_booking', methods=['GET'])
def filter_rooms_for_booking():
    check_in_date = request.args.get('check_in_date')
    check_out_date = request.args.get('check_out_date')
    current_booking_id = request.args.get('current_booking_id', type=int)  # New parameter

    if check_in_date and check_out_date:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')

        # Exclude rooms with conflicting reservations or bookings
        unavailable_room_ids = db.session.query(Room.id).filter(
            Room.id.in_(
                db.session.query(Reservation.room_id).filter(
                    (Reservation.check_in_date < check_out) &
                    (Reservation.check_out_date > check_in) &
                    (Reservation.status != 'Checked Out')
                ).union(
                    db.session.query(Booking.room_id).filter(
                        (Booking.check_in_date < check_out) &
                        (Booking.check_out_date > check_in) &
                        (Booking.id != current_booking_id) &  # Exclude the current booking
                        (Booking.status != 'Checked Out')
                    )
                )
            )
        ).all()

        unavailable_room_ids = [room_id[0] for room_id in unavailable_room_ids]

        # Fetch available rooms excluding those with conflicts
        available_rooms = Room.query.filter(
            Room.status == 'Available',
            ~Room.id.in_(unavailable_room_ids)
        ).all()

        return jsonify({
            'rooms': [
                {'id': room.id, 'room_number': room.room_number,
                 'room_type': room.room_type, 'price': room.price}
                for room in available_rooms
            ]
        })

    return jsonify({'rooms': []})


@app.route('/guests/get_by_phone', methods=['GET'])
def get_guest_by_phone():
    phone_number = request.args.get('phone_number', None)
    if phone_number:
        guest = Guest.query.filter_by(phone_number=phone_number).first()
        if guest:
            return jsonify({
                'exists': True,
                'first_name': guest.first_name,
                'last_name': guest.last_name,
                'email': guest.email,
                'address': guest.address,
                'id_type': guest.id_type,
                'id_number': guest.id_number
            })
    return jsonify({'exists': False})

@app.route('/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = BookingForm(obj=booking)

    # Pre-fill the room choice with the currently selected room
    current_room = Room.query.get(booking.room_id)
    form.room_id.choices = [(current_room.id, f'Room {current_room.room_number} - {current_room.room_type} (₦{current_room.price})')]

    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data

        # Ensure no overlapping reservations for the same room
        conflicting_reservation = Booking.query.filter(
            Booking.room_id == booking.room_id,
            Booking.id != booking_id,  # Exclude current booking
            Booking.status != 'Checked Out',
            (Booking.check_in_date < check_out) & (Booking.check_out_date > check_in)
        ).first()

        if conflicting_reservation:
            flash('The selected room is already reserved for the chosen dates. Please choose a different date range.', 'danger')
            return render_template('edit_booking.html', form=form, booking=booking)

        # Recalculate the total amount based on updated dates
        nights = (check_out - check_in).days
        if nights <= 0:
            nights = 1  # Minimum of one night
        total_amount = current_room.price * nights

        # Update booking details
        booking.check_in_date = check_in
        booking.check_out_date = check_out
        booking.first_name = form.first_name.data
        booking.last_name = form.last_name.data
        booking.phone_number = form.phone_number.data
        booking.email = form.email.data
        booking.address = form.address.data
        booking.children_number = form.children_number.data
        booking.adults_number = form.adults_number.data
        booking.status = form.status.data  # Corrected assignment
        booking.id_type = form.id_type.data
        booking.id_number = form.id_number.data
        booking.total_amount = total_amount

        db.session.commit()
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('manage_bookings'))
    
    
    return render_template('edit_booking.html', form=form, booking=booking)

@app.route('/bookings/check_conflict', methods=['GET'])
def check_booking_conflict():
    room_id = request.args.get('room_id', type=int)
    check_in_date = request.args.get('check_in_date')
    check_out_date = request.args.get('check_out_date')

    if not (room_id and check_in_date and check_out_date):
        return jsonify({'conflict': False, 'message': 'Invalid input data'}), 400

    # Parse the dates
    check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_date, '%Y-%m-%d')

    # Check for conflicts
    conflicting_reservation = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.status != 'Checked Out',
        (Reservation.check_in_date < check_out) & (Reservation.check_out_date > check_in)
    ).first()

    if conflicting_reservation:
        return jsonify({
            'conflict': True,
            'message': (
                f"The selected checkout date conflicts with an existing reservation "
                f"from {conflicting_reservation.check_in_date.strftime('%Y-%m-%d')} "
                f"to {conflicting_reservation.check_out_date.strftime('%Y-%m-%d')}."
            )
        })

    return jsonify({'conflict': False})


@app.route('/bookings/edit_room/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking_room(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = BookingForm(obj=booking)

    available_rooms = Room.query.filter_by(status='Available').all()
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]


    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data

        # Ensure no overlapping reservations for the same room
        conflicting_reservation = Booking.query.filter(
            Booking.room_id == booking.room_id,
            Booking.id != booking_id,  # Exclude current booking
            Booking.status != 'Checked Out',
            (Booking.check_in_date < check_out) & (Booking.check_out_date > check_in)
        ).first()

        if conflicting_reservation:
            flash('The selected room is already reserved for the chosen dates. Please choose a different date range.', 'danger')
            return render_template('edit_booking_room.html', form=form, booking=booking)

       

        # Update booking details
        booking.check_in_date = check_in
        booking.check_out_date = check_out
        booking.first_name = form.first_name.data
        booking.last_name = form.last_name.data
        booking.phone_number = form.phone_number.data
        booking.email = form.email.data
        booking.address = form.address.data
        booking.children_number = form.children_number.data
        booking.adults_number = form.adults_number.data
        booking.status = form.status.data  # Corrected assignment
        booking.id_type = form.id_type.data
        booking.id_number = form.id_number.data
        booking.total_amount = form.calculate_total_price()

        db.session.commit()
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('manage_bookings'))
    
    
    return render_template('edit_booking_room.html', form=form, booking=booking)




@app.route('/bookings/delete/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Cancelled'
    room = Room.query.get(booking.room_id)
    room.status = 'Available'
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted successfully!', 'danger')
    return redirect(url_for('manage_bookings'))

@app.route('/bookings/check_in/<int:booking_id>', methods=['POST'])
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Checked In'
    booking.check_in_date = date.today()  # Automatically set the check-in date
     # Fetch the room and mark it as "Occupied"
    room = Room.query.get(booking.room_id)
    if room: 
        room.status = 'Occupied'  # Update room status to Occupied
        db.session.commit()  # Ensure the change is committed

    db.session.commit()

   
    return redirect(url_for('manage_bookings'))

@app.route('/bookings/check_out/<int:booking_id>', methods=['POST'])
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Checked Out'
    room = Room.query.get(booking.room_id)
    room.status = 'Dirty' # Mark room as dirty after checkout
# Fetch the reservation linked to this booking (if it exists)
    reservation = Reservation.query.filter_by(room_id=booking.room_id).first()
    
    if reservation:
        # Update reservation status to 'Checked Out'
        reservation.status = 'Checked Out'
    booking.check_out_date = date.today()  # Automatically set the check-out date
    db.session.commit()
    return redirect(url_for('manage_bookings'))

@app.route('/bookinghistory')
def bookinghistory():
    last_name = request.args.get('last_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

     # Fetch all bookings
    query = Booking.query.order_by(Booking.check_in_date.desc())

    # Apply filters if provided
    if last_name:
        query = query.filter_by(last_name=last_name)
    if start_date and end_date:
        query = query.filter(Booking.check_in_date.between(start_date, end_date))

    bookings = query.all()  # Use the filtered query here
    return render_template('bookinghistory.html', bookings=bookings)

@app.route('/reservations/check_in/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def check_in_reservation(reservation_id):
    # Fetch the reservation by ID
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'Checked In'
    

     # Change the reserved room status to 'Available'
    reserved_room = Room.query.get(reservation.room_id)
    if reserved_room.status == 'Reserved':
        reserved_room.status = 'Available'
        db.session.commit()  # Commit the status change to make the room available for selection

    # Get today's date (without time)
    today = datetime.utcnow().date()

    # Check if the check-in date is today
    if reservation.check_in_date != today:
        flash(f'Check-in date for this reservation is {reservation.check_in_date}. You can only check in on the correct date.', 'danger')
        
        return redirect(url_for('manage_reservations'))  # Redirect back to reservations list

    # Pre-fill the BookingForm with the reservation details
    form = BookingForm(
        readonly_room=True,
        first_name=reservation.first_name,
        last_name=reservation.last_name,
        phone_number=reservation.phone_number,
        email=reservation.email,
        room_id=reservation.room_id,  # Prefill room_id
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        total_amount=reservation.total_amount
    )

    # Hide the room_id field by making it a hidden input field
    form.room_id.render_kw = {'readonly': True}

    # If the form is submitted, save the booking and mark the room as occupied
    if form.validate_on_submit():
        guest = Guest.query.filter_by(email=form.email.data).first()
        if guest is None:
            guest = Guest(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone_number=form.phone_number.data,
                email=form.email.data,
                address=form.address.data,
                id_type=form.id_type.data,
                id_number=form.id_number.data
            )
            db.session.add(guest)
            db.session.commit()

        

        # Create a new booking with 'Checked In' status
        new_booking = Booking(
            guest_id=guest.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            room_id=reservation.room_id,  # Use the prefixed room_id from the reservation
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            status='Checked In',
            total_amount=reservation.total_amount  # Use the same total amount from reservation
        )
       

        # Update the room status to 'Occupied'
        room = Room.query.get(reservation.room_id)
        room.status = 'Occupied'

        # Update the reservation status to 'Checked In'
        reservation.status = 'Checked In'

       
    
        db.session.add(new_booking)
        db.session.commit()
        flash('Guest successfully checked in!', 'success')
        return redirect(url_for('manage_bookings'))

    return render_template('add_booking.html', form=form)

@app.route('/guests', methods=['GET'])
def manage_guests():
    search_query = request.args.get('search', '').strip()
    if search_query:
        guests = Guest.query.filter(
            (Guest.first_name.ilike(f"%{search_query}%")) |
            (Guest.last_name.ilike(f"%{search_query}%")) |
            (Guest.email.ilike(f"%{search_query}%")) |
            (Guest.phone_number.ilike(f"%{search_query}%"))
        ).all()
    else:
        guests = Guest.query.all()
    return render_template('manage_guests.html', guests=guests, search_query=search_query)

@app.route('/guests/<int:guest_id>', methods=['GET'])
def view_guest_profile(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    bookings = Booking.query.filter_by(guest_id=guest.id).all()
    return render_template('view_guest_profile.html', guest=guest, bookings=bookings)


from datetime import datetime, timedelta
from sqlalchemy import func

from flask import render_template, request
from datetime import datetime
from sqlalchemy import func
from flask_login import login_required
from sqlalchemy.orm import joinedload

@app.route('/reports', methods=['GET'])
@login_required
def reports():
    try:
        # Get today's date
        today = datetime.today()

        # Get start_date and end_date from query parameters
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Validate and parse dates
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)

                if start_date > end_date:
                    flash("Start date cannot be after end date.", "danger")
                    return redirect(url_for('reports'))
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
                return redirect(url_for('reports'))
        else:
            # Default to the first day of the current month and today
            start_date = today.replace(day=1)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        # --- FILTERED INSIGHTS BASED ON DATE RANGE ---
        reservations = Reservation.query.filter(
            Reservation.check_in_date >= start_date,
            Reservation.check_in_date <= end_date
        ).options(joinedload(Reservation.room)).all()

        # Bookings (Checked-In) within the selected date range
        bookings = Booking.query.filter(
            Booking.check_in_date <= end_date,  # Check-in should be before or on the end date
            Booking.check_out_date >= start_date,  # Check-out should be after or on the start date
            Booking.status == 'Checked In'
        ).options(joinedload(Booking.room)).all()

        # Total revenue within the selected date range
        total_revenue = db.session.query(func.sum(Booking.total_amount)).filter(
            Booking.check_in_date <= end_date,
            Booking.check_out_date >= start_date,
            Booking.status == 'Checked In'
        ).scalar() or 0

        # Guests arriving within the selected date range
        guests_arriving = Reservation.query.filter(
            Reservation.check_in_date >= start_date,
            Reservation.check_in_date <= end_date,
            Reservation.status == 'Reserved'
        ).options(joinedload(Reservation.room)).all()

        # Guests departing within the selected date range
        guests_departing = Booking.query.filter(
            Booking.check_out_date >= start_date,
            Booking.check_out_date <= end_date,
            Booking.status == 'Checked In'
        ).options(joinedload(Booking.room)).all()

        # Room occupancy rate (current status of rooms)
        total_rooms = Room.query.count()
        occupied_rooms = Room.query.filter_by(status='Occupied').count()
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

        # Render the filtered report data to the reports.html page
        return render_template(
            'reports.html',
            reservations=reservations,
            bookings=bookings,
            total_revenue=total_revenue,
            guests_arriving=guests_arriving,
            guests_departing=guests_departing,
            occupancy_rate=occupancy_rate,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as e:
        app.logger.error(f"Error generating report: {e}")
        flash("An error occurred while generating the report. Please try again.", "danger")
        return redirect(url_for('reports'))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Created User Database!')
    app.run(debug=True)