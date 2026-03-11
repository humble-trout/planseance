#importations dans l'appli de rencontre Flask qui nous sert de modèle + celles de Maxime Challon
#à voir si on supprime certaines des importations Flask jsp à quoi elles servent toutes
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(
    __name__, 
    template_folder='templates',
    static_folder='statics')
app.config.from_object(Config)

db = SQLAlchemy(app)

from .routes import generales, insertions