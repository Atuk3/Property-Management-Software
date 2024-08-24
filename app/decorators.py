from functools import wraps
from flask import request, redirect, url_for, flash
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))  # Redirect to a different page or home
            return f(*args, **kwargs)
        return decorated_function
    return decorator