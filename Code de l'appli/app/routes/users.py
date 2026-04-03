import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from app.models import User, Seance, Calendrier, Cinema
#Pour récupérer le cinéma favori de l'utilisateur, et de garantir que les noms d'utilisateurs sont uniques
from sqlalchemy import func
from flask_login import login_user, logout_user, current_user, login_required
from app.utils import db, allowed_file
# Importe la base de donnée et les modèles User et Match
from app.models import Utilisateur
#Match -> à mettre dans app.models import plus tard
#Permet de créer des conditions dans les requêtes de bases de données dans SQLAlchemy
from sqlalchemy import or_

users = Blueprint('users', __name__)

#A été mis ici car ça ne marchait pas quand il était dans utils.py. Je ne sais pas si ça marche mais je le laisse au cas où
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nom = request.form.get('nom')
        date_n_str = request.form.get('date_naissance')
        
        #S'assure que le nom d'utilisateur n'est pas déjà utilisé, y compris avec une casse différente
        if Utilisateur.query.filter(func.lower(Utilisateur.nom_utilisateur) == func.lower(username)).first():
            flash("Ce nom d'utilisateur est déjà utilisé !", 'danger')
            return redirect(url_for('users.register'))

        #S'assure que le mail de l'utilisateur n'est pas déjà utilisé
        if Utilisateur.query.filter_by(email=email).first():
            flash('Email déjà enregistré !', 'danger')
            return redirect(url_for('users.register'))

        #Crée des nouvelles données avec SQLAlchemy pour un nouvel utilisateur
        new_user = Utilisateur(
            nom_utilisateur=username,
            email=email,
            nom=nom,
            date_naissance=datetime.strptime(date_n_str, '%Y-%m-%d').date() if date_n_str else None,
            motdepasse=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Compte créé ! Veuillez vous connecter.', 'success')
        return redirect(url_for('users.login'))
        
    return render_template('register.html')

@users.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        #Trie les utilisateurs par leur e-mail
        user = Utilisateur.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.motdepasse, password):
            login_user(user) 
            flash(f'Bienvenue {user.nom} !', 'success')
            return redirect(url_for('generales.index'))
        
        if user and check_password_hash(user.motdepasse, password):
            #Crée la session
            login_user(user, remember=True)
        
        flash('Email ou mot de passe invalide', 'error')
        return redirect(url_for('users.login'))

    #Pour régler un problème de déconnexion sur la page calendrier. Suggestion d'un LLM
    if request.method == 'POST':
        user = Utilisateur.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.motdepasse, request.form.get('password')):
            login_user(user, remember=True) 
            return redirect(url_for('generales.calendrier'))

    return render_template('login.html')

@users.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('users.login'))

@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Page de profil utilisateur"""
    #L'edit mode est ce que l'utilisateur voit lorsqu'il sélectionne "Modifier mon profil"
    edit_mode = request.args.get('edit') == 'true'
    
    #Enregistre les modifications que l'utilisateur fait à son profil
    if request.method == 'POST':
        nouveau_nom = request.form.get('nom')
        date_n_str = request.form.get('date_naissance')
        nouvelle_bio = request.form.get('bio')
        
        try:
            #Mise à jour du nom de l'utilisateur
            if nouveau_nom is not None:
                current_user.nom = nouveau_nom

            #Mise à jour de la date de naissance
            if date_n_str:
                #Suggestion d'un LLM. Conversion de la chaîne HTML 'YYYY-MM-DD' en objet date Python
                current_user.date_naissance = datetime.strptime(date_n_str, '%Y-%m-%d').date()

            if nouvelle_bio is not None:
                current_user.bio = nouvelle_bio
            
            #Suggestion d'un LLM. Gestion de l'upload de photo
            if 'photo' in request.files:
                file = request.files['photo']
                
                #Si l'utilisateur n'a pas sélectionné de fichier, le navigateur envoie un fichier vide sans nom
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        #Sécurise le nom (évite les injections de chemin type ../../etc/passwd)
                        filename = secure_filename(file.filename)
                        
                        #Crée un nom unique pour éviter les conflits (ex: user_5_photo.jpg)
                        unique_filename = f"user_{current_user.id_utilisateur}_{filename}"
                        
                        #Chemin complet pour l'enregistrement physique
                        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                        
                        #S'assure que le dossier existe où l'enregistrement physique est envoyé existe bien
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        
                        #Sauvegarde le fichier sur le serveur
                        file.save(upload_path)
                        
                        #Met à jour l'URL de la photo dans la base de données
                        current_user.photo_url = url_for('static', filename=f'uploads/{unique_filename}')
                        
                    else:
                        #Prévient l'utilisateur si le type de fichier choisi pour la photo de profil n'est pas pris en charge
                        flash("Ce type de fichier n'est pas autorisé pour la photo de profil. Utilisez une image au format PNG, JPG, JPEG, ou GIF.", "danger")
                        
            #Sauvegarde les mises à jours
            db.session.commit()
            flash('Profil mis à jour !', 'success')
            
            #Renvoi vers le profil hors edit mode s'il y a un succèe
            return redirect(url_for('users.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur : {str(e)}', 'danger')
            return redirect(url_for('users.profile', edit='true'))
            
    #Récupère le cinéma préféré de l'utilisateur avec sa commune
    favorite_cinema_query = (
        db.session.query(Seance.nom_cinema, func.count(Seance.nom_cinema).label('occurrence'))
        .join(Calendrier, Seance.id_seance == Calendrier.id_seance)
        .filter(Calendrier.id_utilisateur == current_user.id_utilisateur)
        .group_by(Seance.nom_cinema)
        .order_by(func.count(Seance.nom_cinema).desc())
        .first()
    )

    if favorite_cinema_query:
        fav_cinema = favorite_cinema_query[0]
    else:
        fav_cinema = "Aucun cinéma favori pour le moment"
    
    #Récupère les films du calendrier de l'utilisateur pour afficher dans les films récemment vus
    from app.models import FilmTitre
    from app.tmdb_utils import search_movie_on_tmdb
    
    calendar_films_query = (
        db.session.query(FilmTitre, Seance)
        .join(Seance, func.lower(FilmTitre.titre) == func.lower(Seance.titre))
        .join(Calendrier, Calendrier.id_seance == Seance.id_seance)
        .filter(
            Calendrier.id_utilisateur == current_user.id_utilisateur,
            Seance.debut > datetime.now()  # Films passés seulement
        )
        .distinct(FilmTitre.id_film)
        .limit(6)
        .all()
    )
    
    calendar_films = []
    for film, seance in calendar_films_query:
        tmdb_data = search_movie_on_tmdb(film.titre)
        calendar_films.append({
            'id_film': film.id_film,
            'titre': film.titre,
            'poster_url': f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}" if tmdb_data and tmdb_data.get('poster_path') else None
        })
    
    #Compte total des séances
    calendar_count = db.session.query(Calendrier).filter(
        Calendrier.id_utilisateur == current_user.id_utilisateur
    ).count()
    
    print(current_user.id_utilisateur)
    return render_template('profile.html', 
                         user=current_user, 
                         fav_cinema=fav_cinema, 
                         edit_mode=edit_mode,
                         calendar_films=calendar_films,
                         calendar_count=calendar_count)


@users.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    """Afficher le profil public d'un autre utilisateur"""
    user = Utilisateur.query.get_or_404(user_id)
    
    #Récupère le cinéma favori
    favorite_cinema_query = (
        db.session.query(Seance.nom_cinema, func.count(Seance.nom_cinema).label('occurrence'))
        .join(Calendrier, Seance.id_seance == Calendrier.id_seance)
        .filter(Calendrier.id_utilisateur == user_id)
        .group_by(Seance.nom_cinema)
        .order_by(func.count(Seance.nom_cinema).desc())
        .first()
    )
    
    if favorite_cinema_query:
        fav_cinema = favorite_cinema_query[0]
    else:
        fav_cinema = "Aucun cinéma favori pour le moment"
    
    #Films récemment vus
    from app.models import FilmTitre
    from app.tmdb_utils import search_movie_on_tmdb
    
    calendar_films_query = (
        db.session.query(FilmTitre, Seance)
        .join(Seance, func.lower(FilmTitre.titre) == func.lower(Seance.titre))
        .join(Calendrier, Calendrier.id_seance == Seance.id_seance)
        .filter(
            Calendrier.id_utilisateur == user_id,
            Seance.debut > datetime.now()
        )
        .distinct(FilmTitre.id_film)
        .limit(6)
        .all()
    )
    
    calendar_films = []
    for film, seance in calendar_films_query:
        tmdb_data = search_movie_on_tmdb(film.titre)
        calendar_films.append({
            'id_film': film.id_film,
            'titre': film.titre,
            'poster_url': f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}" if tmdb_data and tmdb_data.get('poster_path') else None
        })
    
    #Compte total des séances
    calendar_count = db.session.query(Calendrier).filter(
        Calendrier.id_utilisateur == user_id
    ).count()
    
    #Calcul de l'âge
    from datetime import date
    age = None
    if user.date_naissance:
        today = date.today()
        age = today.year - user.date_naissance.year - (
            (today.month, today.day) < (user.date_naissance.month, user.date_naissance.day)
        )
    
    return render_template('user_profile.html', 
                         user=user,
                         age=age,
                         fav_cinema=fav_cinema,
                         calendar_films=calendar_films,
                         calendar_count=calendar_count)


@users.route('/delete_account', methods=['POST', 'GET'])
@login_required
def delete_account():
    """Permet à l'utilisateur de supprimer son compte. Snif :("""
    try:
        user = current_user
        db.session.delete(user)
        db.session.commit()
        flash('Votre compte a été supprimé avec succès.', 'success')
        return redirect(url_for('generales.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
        return redirect(url_for('users.profile'))
