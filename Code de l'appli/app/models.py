from app.utils import db
from datetime import datetime, date
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text, DateTime
from flask_login import UserMixin

#S'assure de bien utiliser le bon schéma
SCHEMA_NAME = 'psch'

class AireGeographique(db.Model):
    __table__ = Table(
        'aire_geographique', db.metadata,
        Column('id_aire_geographique', Integer, primary_key=True),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

class FilmTitre(db.Model):
    __table__ = Table(
        'film_titre', db.metadata,
        Column('id_film', Integer, primary_key=True),
        Column('titre', db.String),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

class Utilisateur(db.Model, UserMixin):
    __table__ = Table(
        'utilisateur', db.metadata,
        Column('id_utilisateur', Integer, primary_key=True),
        Column('nom_utilisateur', db.String),
        Column('nom', db.String),
        Column('date_naissance', db.Date),
        Column('email', db.String),
        Column('motdepasse', db.String),
        Column('bio', db.Text),
        Column('photo_url', db.String),
        schema=SCHEMA_NAME,
        extend_existing=True
    )
    
    #Indique à Flask_login que id_utilisateur est bien l'id à utiliser
    def get_id(self):
        return str(self.id_utilisateur)

    #Assure que l'username correspond bien à nom_utilisateur et hache le mot de passe
    @property
    def username(self):
        return self.nom_utilisateur
    
    @username.setter
    def username(self, value):
        self.nom_utilisateur = value
    
    @property
    def password_hash(self):
        return self.motdepasse
    
    @password_hash.setter
    def password_hash(self, value):
        self.motdepasse = value

    #Calcule l'âge de l'utilisateur. Réalisé avec l'aide d'un LLM
    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            #On retire 1 si l'anniversaire n'est pas encore passé à la date d'ajourd'hui
            age = today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
            return age
        return None

class Cinema(db.Model):
    __table__ = Table(
        'cinema', db.metadata,
        Column('id_cinema', Integer, primary_key=True),
        Column('id_aire_geographique', Integer),
        Column('nom_cinema', db.String),
        Column('adresse', db.String),
        Column('commune', db.String),
        Column('longitude', db.Float),
        Column('latitude', db.Float),
        Column('numero_uu', db.String),
        Column('ecrans', Integer),
        Column('fauteuils', Integer),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

class Seance(db.Model):
    __table__ = Table(
        'seance', db.metadata,
        Column('id_seance', Integer, primary_key=True),
        Column('id_film', Integer, ForeignKey(f'{SCHEMA_NAME}.film.id_film'), nullable=False),
        Column('id_cinema', Integer, ForeignKey(f'{SCHEMA_NAME}.cinema.id_cinema'), nullable=False),
        Column('titre', db.String),
        Column('nom_cinema', db.String),
        Column('debut', DateTime),
        Column('fin', DateTime),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

    #Fait la relation entre film et seances et entre cinema et seances pour le matching
    film = db.relationship('Film', backref='seances')

    cinema = db.relationship('Cinema', backref='seances')

class Matches(db.Model):
    __table__ = Table(
    'matches', db.metadata,
    Column('id_matches', Integer, primary_key=True),
    Column('id_utilisateur1', Integer, ForeignKey(f'{SCHEMA_NAME}.utilisateur.id_utilisateur'), nullable=False),
    Column('id_utilisateur2', Integer, ForeignKey(f'{SCHEMA_NAME}.utilisateur.id_utilisateur'), nullable=False),
    Column('id_seance', Integer, ForeignKey(f'{SCHEMA_NAME}.seance.id_seance'), nullable=False),
    Column('statut', String(20), default='en_attente'),
    schema=SCHEMA_NAME,
    extend_existing=True
    )
    #Lien entre les deux utilisateurs matchés. Suggestion d'un LLM car je ne parvenais pas à faire fonctionner le matching. Je ne sais honnêtement pas si ça fait grand-chose mais je le laisse là au cas où
    user1 = db.relationship('Utilisateur', foreign_keys=[__table__.c.id_utilisateur1], backref='matches_as_user1')
    user2 = db.relationship('Utilisateur', foreign_keys=[__table__.c.id_utilisateur2], backref='matches_as_user2')
    

#Tables sans clés primaires. J'ai dû "forcer" SQLAlchemy à considérer des clés secondaires comme clés primaires sinon la BDD ne marchait pas

class Film(db.Model):
    __table__ = Table(
        'film', db.metadata,
        Column('id_film', Integer, ForeignKey(f'{SCHEMA_NAME}.film_titre.id_film'), primary_key=True),
        Column('titre', db.String),
        Column('date_sortie', db.String),
        schema=SCHEMA_NAME,
        extend_existing=True
    )
    
class Frequentation(db.Model):
    __table__ = Table(
        'frequentation', db.metadata,
        Column('id_cinema', Integer, ForeignKey(f'{SCHEMA_NAME}.cinema.id_cinema'), primary_key=True),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

class ProgrammationCinema(db.Model):
    __table__ = Table(
        'programmation_cinema', db.metadata,
        Column('id_cinema', Integer, ForeignKey(f'{SCHEMA_NAME}.cinema.id_cinema'), primary_key=True),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

class Calendrier(db.Model):
    __table__ = Table(
        'calendrier', db.metadata,
        Column('id_utilisateur', Integer, ForeignKey(f'{SCHEMA_NAME}.utilisateur.id_utilisateur'), primary_key=True),
        Column('id_seance', Integer, ForeignKey(f'{SCHEMA_NAME}.seance.id_seance'), primary_key=True),
        schema=SCHEMA_NAME,
        extend_existing=True
    )

    #Définit la relation entre l'id_utilisateur et les séances sauvegardées
    utilisateur = db.relationship('Utilisateur', backref='mes_seances')
    
    #Permet le matching en mettant en relation les id_seance et les utilisateurs participants
    seance = db.relationship('Seance', backref='participants')

class CinemaFavori(db.Model):
    __table__ = Table(
        'cinema_favori', db.metadata,
        Column('id_utilisateur', Integer, ForeignKey(f'{SCHEMA_NAME}.utilisateur.id_utilisateur'), primary_key=True),
        Column('id_cinema', Integer, ForeignKey(f'{SCHEMA_NAME}.cinema.id_cinema'), primary_key=True),
        schema=SCHEMA_NAME,
        extend_existing=True
    )
#Garantit qu'il n'y ait pas d'erreur parce que la table utilisateur a un nom français
#Doit être à la fin de models.py
User = Utilisateur