from flask_sqlalchemy import SQLAlchemy
from flask import session, redirect, url_for, flash
from functools import wraps

db = SQLAlchemy()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('users.login'))
        return f(*args, **kwargs)
    return decorated_function

#Pour que l'utilisateur puisse choisir une photo de profil. A été gardé au cas où mais est aussi défini dans users.py
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'} in ALLOWED_EXTENSIONS