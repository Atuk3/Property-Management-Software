from flask import render_template
from app import app

@app.route('/')
def home():
    return "Welcome to the Hotel Management System!"