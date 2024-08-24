from flask import render_template
from flask_login import login_required
from app.decorators import role_required
from app import app

@app.route('/')
def home():
    return "Welcome to the Hotel Management System!"


@app.route('/admin_dashboard')
@login_required
@role_required('Admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/manager_dashboard')
@login_required
@role_required('Manager')
def manager_dashboard():
    return render_template('manager_dashboard.html')