# app/models/formulaires.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
class Recherche(FlaskForm):
    #ici apparemment il y a un html associé, Eva est-ce toi qui t'en occupes? 
    nom_aire_geographique = StringField("nom_aire_geographique", validators=[])
    genre_cinematographique = SelectField('genre', choices=[('',''),('COM','comedie')])
    langue = SelectField ('langue', choices=[('',''),('FR','français')])
    horaires = 

    