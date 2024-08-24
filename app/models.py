from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, Manager, Receptionist
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)  # Track last login time

    def __repr__(self):
        return f'<User {self.username}>'
    

    

    class Room(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        room_number = db.Column(db.String(10), unique=True, nullable=False)
        room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
        status = db.Column(db.String(50), nullable=False, default='Available')  # Available, Occupied, Maintenance
        description = db.Column(db.Text)

        # Relationship
        room_type = db.relationship('RoomType', backref=db.backref('rooms', lazy=True))

        def __repr__(self):
            return f'<Room {self.room_number} - {self.status}>'
        


    class RoomType(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50), nullable=False)  # Single, Double, Suite
        rate = db.Column(db.Float, nullable=False)
        description = db.Column(db.Text)

        def __repr__(self):
            return f'<RoomType {self.name}>'
        

        
    class Guest(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(100), nullable=False)
        last_name = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(150), unique=True, nullable=False)
        phone_number = db.Column(db.String(20), nullable=False)
        address = db.Column(db.String(200))
        created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

        def __repr__(self):
            return f'<Guest {self.first_name} {self.last_name}>'
        


    class Booking(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
        guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
        check_in_date = db.Column(db.Date, nullable=False)
        check_out_date = db.Column(db.Date, nullable=False)
        status = db.Column(db.String(50), nullable=False, default='Reserved')  # Reserved, Checked-in, Checked-out, Cancelled
        total_amount = db.Column(db.Float, nullable=False)
        created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

        # Relationships
        room = db.relationship('Room', backref=db.backref('bookings', lazy=True))
        guest = db.relationship('Guest', backref=db.backref('bookings', lazy=True))

        def __repr__(self):
            return f'<Booking Room {self.room_id} - Guest {self.guest_id}>'
        



    class Payment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
        amount_paid = db.Column(db.Float, nullable=False)
        payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
        payment_method = db.Column(db.String(50), nullable=False)  # Cash, Credit Card, Bank Transfer

        # Relationship
        booking = db.relationship('Booking', backref=db.backref('payments', lazy=True))

        def __repr__(self):
            return f'<Payment Booking {self.booking_id} - Amount {self.amount_paid}>'