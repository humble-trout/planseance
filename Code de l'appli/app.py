from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

app = Flask(
    __name__, 
    template_folder='templates',
    static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy(app)

from app.routes import generales, insertions, suppressions, erreurs, users