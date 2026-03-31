from app.utils import db
from datetime import datetime, date
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text, DateTime
from flask_login import UserMixin

# Problèmes dans la déclaration de certaines clés secondaires : à vérifier

#S'assure de bien utiliser le bon schéma
SCHEMA_NAME = 'psch'

#Ici, la première fois que j'ai tenté de connecter la base de données Postgres avec Automap, il n'a pas importé les tables: calendrier, cinema_favori, film_titre. Selon le LLM auquel j'ai demandé la raison de ce problème, c'est parce qu'il manquait des clés primaires à ces tables
#Le LLM a suggéré la méthode "Manual reflection" à la place, afin de contourner ce problème en "forçant" SQLAlchemy à reconnaître certaines clés étrangères comme clés primaires

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
        #Nous avons supprimé "âge" car il est calculé à partir de la date de naissance
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

    # Propriétés pour compatibilité avec le code existant
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

    #Calcule l'âge de l'utilisateur
    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            # Calcul : Année actuelle - Année de naissance
            # On retire 1 si l'anniversaire n'est pas encore passé cette année
            age = today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
            return age
        return None # Retourne None si la date de naissance est inconnue

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
    user1 = db.relationship('Utilisateur', foreign_keys=[__table__.c.id_utilisateur1], backref='matches_as_user1')
    user2 = db.relationship('Utilisateur', foreign_keys=[__table__.c.id_utilisateur2], backref='matches_as_user2')
    

#Tables sans clés primaires. On "force" SQLAlchemy à considérer des clés secondaires comme clés primaires

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

#Ci-dessous: à ajouter dans Utilisateur:

# CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             email TEXT UNIQUE NOT NULL,
#             password_hash TEXT NOT NULL,
#             name TEXT, age INTEGER, bio TEXT, photo_url TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

#Ci-dessous: à utiliser pour le matching, le calendrier et les cinémas favoris

# class Like(db.Model):
#     __tablename__ = 'likes'
#     id = db.Column(db.Integer, primary_key=True)
#     liker_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     liked_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     # Ensure a user can't like the same person twice
#     __table_args__ = (db.UniqueConstraint('liker_id', 'liked_id', name='_liker_liked_uc'),)

# class Match(db.Model):
#     __tablename__ = 'matches'
#     id = db.Column(db.Integer, primary_key=True)
#     user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     # These allow you to do: match.user1.name or match.user2.photo_url
#     user1 = db.relationship('User', foreign_keys=[user1_id])
#     user2 = db.relationship('User', foreign_keys=[user2_id])
#     messages = db.relationship('Message', backref='match', cascade="all, delete-orphan")

# class Notification(db.Model):
#     __tablename__ = 'notifications'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
#     match_id = db.Column(db.Integer, db.ForeignKey('matches.id', ondelete='CASCADE'), nullable=True)
#     type = db.Column(db.String(20), nullable=False) # 'like', 'match', 'message'
#     message = db.Column(db.String(255))
#     is_read = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     # CRITICAL: This allows notification.sender.name in your templates
#     sender = db.relationship('User', foreign_keys=[sender_id])