# Import necessary libraries
import json
import os
import io
import psycopg2
import datetime

from flask import Flask,render_template, request, jsonify,flash,url_for,redirect,session,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import DecimalField,  StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from flask_login import UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, ValidationError
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

    def __repr__(self):
        return f'<Room {self.room_number}>'
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
    # reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    # rooms = Room.query.all()  # Example: get all rooms
    # revenue = calculate_revenue()  # Define a function to calculate revenue
    return render_template('dashboard.html', current_user=current_user)

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Created User Database!')
    app.run(debug=True)