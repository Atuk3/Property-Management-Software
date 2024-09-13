# Import necessary libraries
import json
import os
import io
import psycopg2
from datetime import date
from flask import Flask,render_template, request, jsonify,flash,url_for,redirect,session,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import DecimalField,  StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from flask_login import UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, ValidationError, NumberRange
from sqlalchemy.sql import func
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user,LoginManager
from flask_migrate import Migrate

# Initialize Flask application
app=Flask(__name__)

# Set Flask application configurations
db=SQLAlchemy()
DB_NAME="database.db"
app.config['SECRET_KEY']='david'
app.config['UPLOAD_FOLDER']='static/files'
app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    status = db.Column(db.String(20), nullable=False, default='Reserved') #Reserved, Cancelled.


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
    id_type = db.Column(db.String(50), nullable=False)
    id_number = db.Column(db.String(50), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    children_number = db.Column(db.Integer, nullable=False)
    adults_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)  # ForeignKey for Guest
    total_amount = db.Column(db.Float, nullable=False)

     

    def calculate_total_amount(self):
        # Assuming Room model has a price attribute
        room = Room.query.get(self.room_id)
        num_nights = (self.check_out_date - self.check_in_date).days
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
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=False)
    id_type = db.Column(db.String(50), nullable=False)
    id_number = db.Column(db.String(50), nullable=False)

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
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Reserved', 'Reserved'),('Cancelled', 'Cancelled')], validators=[DataRequired()])
    total_amount = DecimalField('Total Amount (₦)', places=2, validators=[DataRequired(), NumberRange(min=0)], render_kw={'readonly': True})
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
    room_number = StringField('Room Number', validators=[DataRequired(), Length(min=1, max=10)])
    room_type = SelectField('Room Type', choices=[('Standard 1', 'Standard 1'), ('Standard 2', 'Standard 2'), ('Executive', 'Executive'), ('Executive Wing B', 'Executive Wing B'), ('Exclusive', 'Exclusive')], validators=[DataRequired()])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Occupied', 'Occupied'), ('Maintenance', 'Maintenance'), ('Cleaning', 'Cleaning')], validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Save')

class BookingForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    room_id = SelectField('Room', coerce=int, validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    id_type = SelectField('ID Type', choices=[('nin', 'NIN'), ('drivers_license', 'Driver\'s License'), ('id_card', 'ID Card')], validators=[DataRequired()])
    id_number = StringField('ID Number', validators=[DataRequired()])
    adults_number=StringField('Adults Number', validators=[DataRequired()])
    children_number=StringField('Children Number', validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', format='%Y-%m-%d')
    status = SelectField('Status', choices=[('Pending', 'Pending')], validators=[DataRequired()])
    total_amount = DecimalField('Total Amount (₦)', places=2, validators=[DataRequired(), NumberRange(min=0)], render_kw={'readonly': True})
    
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
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

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch total bookings
    total_bookings = Booking.query.filter_by(status='Checked In').count()
    # Fetch total reservations
    total_reservations = Reservation.query.filter_by(status='Reserved').count()

    # Fetch total occupied rooms
    total_rooms_occupied = Room.query.filter_by(status='Occupied').count()
    # Fetch total available rooms
    total_rooms_available = Room.query.filter_by(status='Available').count()
     # Fetch total dirty rooms
    total_rooms_dirty = Room.query.filter_by(status='Dirty').count()

    # Fetch total revenue
    total_revenue = db.session.query(func.sum(Booking.total_amount)).scalar() or 0

    # Fetch recent bookings (last 5)
    recent_bookings = Booking.query.order_by(Booking.check_in_date.desc()).limit(5).all()

    return render_template(
        'dashboard.html', 
        total_bookings=total_bookings,
        total_reservations=total_reservations,
        total_rooms_available=total_rooms_available,
        total_rooms_dirty=total_rooms_dirty,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        total_rooms_occupied=total_rooms_occupied 
        
    )

# Route to view all reservations
@app.route('/reservations', methods=['GET'])
@login_required
def manage_reservations():
    # Filter reservations by status or guest name
    status = request.args.get('status', '')
    last_name = request.args.get('last_name', '')

    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    if last_name:
        query = query.filter(Reservation.last_name.like(f'%{last_name}%'))

    reservations = query.order_by(Reservation.check_in_date.desc()).all()

    return render_template('manage_reservations.html', reservations=reservations, status=status, last_name=last_name)


# Route to add a new reservation
@app.route('/reservations/add', methods=['GET', 'POST'])
@login_required
def add_reservation():
    form = ReservationForm()

    # Dynamically populate available room choices
    available_rooms = Room.query.filter_by(status='Available').all()
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]

    if form.validate_on_submit():
        # Create a new reservation
        new_reservation = Reservation(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            room_id=form.room_id.data,
            total_amount=form.calculate_total_price(),
            status=form.status.data
        )
        
        # Mark the room as "Occupied"
        room = Room.query.get(form.room_id.data)
        room.status = 'Reserved'

        # Commit changes
        db.session.add(new_reservation)
        db.session.commit()
        flash('Reservation successfully created!', 'success')
        return redirect(url_for('manage_reservations'))

    return render_template('add_reservation.html', form=form)


# Route to edit a reservation
@app.route('/reservations/edit/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationForm(obj=reservation)

    available_rooms = Room.query.filter_by(status='Available').all()
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]

    if form.validate_on_submit():
        # Update reservation details
        reservation.first_name = form.first_name.data
        reservation.last_name = form.last_name.data
        reservation.email = form.email.data
        reservation.check_in_date = form.check_in_date.data
        reservation.check_out_date = form.check_out_date.data
        reservation.room_id = form.room_id.data
        reservation.total_amount = form.calculate_total_price()
        reservation.status = form.status.data

        db.session.commit()
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('manage_reservations'))

    return render_template('edit_reservation.html', form=form, reservation=reservation)


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
        flash('Room is now available.', 'success')
    return redirect(url_for('housekeeping'))

@app.route('/housekeeping', methods=['GET'])
@login_required
def housekeeping():
    # Fetch rooms that are either "Occupied" or "Dirty" (to be cleaned)
  rooms = Room.query.filter(Room.status.in_(['Occupied', 'Dirty'])).order_by(Room.room_number).all()
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

    db.session.commit()
    flash(f"Room status updated to {room.status}!", 'success')
    return redirect(url_for('housekeeping'))

@app.route('/bookings', methods=['GET'])
def manage_bookings():
    
    phone_number = request.args.get('phone_number')
    last_name = request.args.get('last_name')

    bookings = Booking.query

    
    

    if phone_number:
        bookings = bookings.filter(Booking.phone_number.like(f'%{phone_number}%'))

    if last_name:
        bookings = bookings.filter(Booking.last_name.like(f'%{last_name}%'))

    bookings = Booking.query.order_by(Booking.check_in_date.desc()).all()


    return render_template('manage_bookings.html', bookings=bookings,phone_number=phone_number,last_name=last_name)

@app.route('/bookings/add', methods=['GET', 'POST'])
def add_booking():
    form = BookingForm()
    # Fetch rooms that are either "Available" or "Reserved"
    available_rooms = Room.query.filter(Room.status.in_(['Available', 'Reserved'])).all()

 # Populate the room choices in the form
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]

    # Automatically set the check-in date to today and mark it as readonly
    form.check_in_date.data = date.today()

    if form.validate_on_submit():
         # Check if the guest already exists based on email or other identifier
        guest = Guest.query.filter_by(email=form.email.data).first()
        
        if guest is None:
            # Create a new guest
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
        else:
            # Update existing guest details
            guest.first_name = form.first_name.data
            guest.last_name = form.last_name.data
            guest.phone_number = form.phone_number.data
            guest.address = form.address.data
            guest.id_type = form.id_type.data
            guest.id_number = form.id_number.data
            db.session.commit()


        # Create the booking
        new_booking = Booking(
            guest_id=guest.id,  # Link the guest to the booking
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data,
            id_type=form.id_type.data,
            id_number=form.id_number.data,
            room_id=form.room_id.data,
            children_number=form.children_number.data,
            adults_number=form.adults_number.data,
            status=form.status.data,
            check_in_date=date.today(),  # Set check-in date to today
            check_out_date=form.check_out_date.data,
            total_amount=form.total_amount.data
        )

        room = Room.query.get(form.room_id.data)
        if room:
            room.status = 'Occupied'  # Update room status to 'occupied'

  # Fetch the reservation linked to this booking (if exists) and update its status
        reservation = Reservation.query.filter_by(room_id=form.room_id.data).first()
        if reservation:
            reservation.status = 'Checked In'  # Update reservation status to 'Checked In'

            
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking added successfully!', 'success')
        return redirect(url_for('manage_bookings'))
    return render_template('add_booking.html', form=form)

@app.route('/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = BookingForm(obj=booking)
    if form.validate_on_submit():
         # Recalculate the total amount based on updated check-in and check-out dates
        nights = (form.check_out_date.data - form.check_in_date.data).days
        if nights <= 0:
            nights = 1  # Minimum of one night
        
        room = Room.query.get(form.room_id.data)
        total_amount = room.price * nights if room else 0

        # Update the booking instance
        booking.first_name = form.first_name.data
        booking.last_name = form.last_name.data
        booking.phone_number = form.phone_number.data
        booking.email = form.email.data
        booking.address = form.address.data
        booking.room_id = form.room_id.data
        booking.check_in_date = form.check_in_date.data
        booking.check_out_date = form.check_out_date.data
        booking.children_number = form.children_number.data
        booking.adults_number = form.adults_number.data
        booking.status = form.status.data
        booking.id_type = form.id_type.data
        booking.id_number = form.id_number.data
        booking.total_amount = total_amount
        db.session.commit()
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('manage_bookings'))
        
    return render_template('edit_booking.html', form=form, booking=booking)

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
    db.session.commit()
   
    return redirect(url_for('manage_bookings'))

@app.route('/bookings/check_out/<int:booking_id>', methods=['POST'])
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Checked Out'
    room = Room.query.get(booking.room_id)
    room.status = 'Dirty' # Mark room as dirty after checkout
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

     # Dynamically populate available room choices (including the reserved room)
    available_rooms = Room.query.filter(Room.status.in_(['Available', 'Reserved'])).all()


    # Pre-fill the BookingForm with the reservation details
    form = BookingForm(
        first_name=reservation.first_name,
        last_name=reservation.last_name,
        phone_number=reservation.phone_number,
        email=reservation.email,
        room_id=reservation.room_id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        total_amount=reservation.total_amount
    )

      # Set the room choices in the form, making sure the reserved room is included
    form.room_id.choices = [(room.id, f'Room {room.room_number} - {room.room_type} (₦{room.price})') for room in available_rooms]


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
        new_booking = Booking(
            guest_id=guest.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            room_id=form.room_id.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            status='Checked In',
            total_amount=reservation.total_amount  # Use the same total amount from reservation
        )

        room = Room.query.get(form.room_id.data)
        room.status = 'Occupied'

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



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Created User Database!')
    app.run(debug=True)