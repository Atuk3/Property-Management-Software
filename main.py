# Import necessary libraries
import json
import os
import io
import psycopg2
from datetime import datetime
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
    guest_name = db.Column(db.String(150), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('reservations', lazy=True))

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Numeric type for price

    # This defines a relationship to Booking and sets the backref as 'room' in Booking.
    bookings = db.relationship('Booking', backref='room', lazy=True)

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
    guest_name = StringField('Guest Name', validators=[DataRequired()])
    check_in = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    room_number = StringField('Room Number', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Reservation')

class RoomForm(FlaskForm):
    room_number = StringField('Room Number', validators=[DataRequired(), Length(min=1, max=10)])
    room_type = SelectField('Room Type', choices=[('Standard 1', 'Standard 1'), ('Standard 2', 'Standard 2'), ('Executive', 'Executive'), ('Executive Wing B', 'Executive Wing B'), ('Exclusive', 'Exclusive')], validators=[DataRequired()])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Occupied', 'Occupied'), ('Maintenance', 'Maintenance')], validators=[DataRequired()])
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
    check_out_date = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')], validators=[DataRequired()])
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
     # Fetch data for the dashboard
    # booking = Booking.query.all()
    rooms = Room.query.all()  # Example: get all rooms
    # revenue = calculate_revenue()  # Define a function to calculate revenue
    return render_template('dashboard.html', current_user=current_user, rooms=rooms)

@app.route('/reservations', methods=['GET', 'POST'])
@login_required
def reservations():
    
    form = ReservationForm()
    if form.validate_on_submit():
        new_reservation = Reservation(
            guest_name=form.guest_name.data,
            check_in=form.check_in.data,
            check_out=form.check_out.data,
            room_number=form.room_number.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(new_reservation)
        db.session.commit()
        print('Reservation created successfully!')
        return redirect(url_for('reservations'))

    reservations = Reservation.query.all()
    return render_template('reservations.html', form=form, reservations=reservations)

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
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            total_amount=form.total_amount.data
        )

        room = Room.query.get(form.room_id.data)
        if room:
            room.status = 'Occupied'  # Update room status to 'occupied'

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
    db.session.commit()
   
    return redirect(url_for('manage_bookings'))

@app.route('/bookings/check_out/<int:booking_id>', methods=['POST'])
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Checked Out'
    room = Room.query.get(booking.room_id)
    room.status = 'Available'
    db.session.commit()
    return redirect(url_for('manage_bookings'))

@app.route('/bookings/history')
def booking_history():
    bookings = Booking.query.order_by(Booking.check_in_date.desc()).all()
    return render_template('booking_history.html', bookings=bookings)

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