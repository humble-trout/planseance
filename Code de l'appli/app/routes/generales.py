from flask import Blueprint, render_template, redirect, url_for, session, jsonify, current_app, request, flash
from sqlalchemy import extract, func, or_, String, cast
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils import db
from app.models import FilmTitre, Seance, Cinema, Film, Calendrier, Matches
from ..forms import FiltreFilmForm, SimplePagination
from app.tmdb_utils import search_movie_on_tmdb, get_cache_stats
from flask_login import current_user, login_required

generales = Blueprint('generales', __name__)


def verify_film_on_tmdb(film_data):
    """Vérifie si un film existe sur TMDB (pour threading)"""
    film_id, titre = film_data
    tmdb_result = search_movie_on_tmdb(titre)
    return (film_id, titre, tmdb_result is not None)


@generales.route('/')
def index():
    """Page d'accueil avec films disponibles validés TMDB"""
    try:
        # Requête avec SQLAlchemy - TOUS les films avec séances
        # JOIN sur le titre car seance.id_film est NULL
        subquery = (
            db.session.query(
                FilmTitre.id_film,
                FilmTitre.titre,
                func.lower(
                    func.regexp_replace(FilmTitre.titre, '[^a-zA-Z0-9]+', '', 'g')
                ).label('titre_normalise')
            )
            .join(Seance, func.lower(FilmTitre.titre) == func.lower(Seance.titre))
            .filter(Seance.debut.isnot(None))
            # .filter(Seance.debut >= datetime.now())  # Pas nécessaire pour l'eval mais serait nécessaire en conditions réelles
            .distinct()
            .subquery()
        )
        
        # Requête principale avec DISTINCT ON
        films_query = (
            db.session.query(
                subquery.c.id_film,
                subquery.c.titre
            )
            .distinct(subquery.c.titre_normalise)
            .order_by(subquery.c.titre_normalise, subquery.c.titre)
            .limit(100)  # Augmenté pour compenser le filtrage TMDB
        )
        
        films_db = films_query.all()
        print(f"{len(films_db)} films trouvés")
        
        # Vérification TMDB en parallèle
        films_to_verify = [(f.id_film, f.titre) for f in films_db]
        verified_films = []
        
        print(f"🔍 Validation TMDB en cours...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(verify_film_on_tmdb, film): film for film in films_to_verify}
            
            for future in as_completed(futures):
                film_id, titre, is_valid = future.result()
                if is_valid:
                    verified_films.append({'id_film': film_id, 'titre': titre})
        
        # Limiter à x films après validation
        #verified_films = verified_films[:100]
        
        print(f"{len(verified_films)} films validés sur TMDB")
        print(f"Cache stats: {get_cache_stats()}")
        
        return render_template('index.html', films=verified_films)
        
    except Exception as e:
        print(f"Erreur lors du chargement des films: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', films=[])

@generales.route('/film/<int:id_film>')
def film(id_film):
    """Page de détails d'un film avec ses séances"""
    try:
        # Récupérer les informations du film avec SQLAlchemy
        film_query = (
            db.session.query(
                FilmTitre.id_film,
                FilmTitre.titre,
                Film.realisateur,
                Film.duree,
                Film.genre.label('genres'),
                Film.date_sortie.label('annee'),
                Film.note
            )
            .outerjoin(Film, FilmTitre.id_film == Film.id_film)
            .filter(FilmTitre.id_film == id_film)
            .first()
        )
        
        if not film_query:
            print(f"Film {id_film} non trouvé")
            return "Film non trouvé", 404
        
        # Convertir en dico pour pouvoir ajouter les infos TMDB
        film_data = {
            'id_film': film_query.id_film,
            'titre': film_query.titre,
            'realisateur': film_query.realisateur,
            'duree': film_query.duree,
            'genres': film_query.genres,
            'annee': film_query.annee,
            'note': film_query.note,
            'synopsis': None,  # À compléter avec TMDB
            'poster_url': None,
            'tmdb_note': None,
            'tmdb_votes': None,
            'budget': None,
            'revenue': None,
            'langues': None,
            'pays': None
        }
        
        # Compléter avec TMDB si disponible
        tmdb_data = search_movie_on_tmdb(film_query.titre)
        if tmdb_data:
            film_data['synopsis'] = tmdb_data.get('overview')
            film_data['poster_url'] = f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}" if tmdb_data.get('poster_path') else None
            film_data['tmdb_note'] = tmdb_data.get('vote_average')
            film_data['tmdb_votes'] = tmdb_data.get('vote_count')
            film_data['budget'] = tmdb_data.get('budget')
            film_data['revenue'] = tmdb_data.get('revenue')
            
            if tmdb_data.get('spoken_languages'):
                film_data['langues'] = ', '.join([l['name'] for l in tmdb_data['spoken_languages']])
            if tmdb_data.get('production_countries'):
                film_data['pays'] = ', '.join([p['name'] for p in tmdb_data['production_countries']])
        
        # 3. Récupérer les séances avec tentative d'identification des cinémas
        seances_query = (
            db.session.query(
                Seance.id_seance,
                Seance.debut.label('date_seance'),
                Seance.version,
                Seance.id_cinema,  # AJOUT ID CINEMA
                Cinema.nom_cinema.label('cinema_nom'),
                Cinema.commune.label('ville'),
                Cinema.adresse,
                Seance.nom_cinema.label('seance_cinema_nom')  # Nom dans la table seance
            )
            .outerjoin(Cinema, Seance.id_cinema == Cinema.id_cinema)
            .join(FilmTitre, func.lower(Seance.titre) == func.lower(FilmTitre.titre))
            .filter(
                FilmTitre.id_film == id_film,
                Seance.debut.isnot(None),
                # Seance.debut >= datetime.now()  # Pas nécessaire pour l'eval mais serait nécessaire en conditions réelles
            )
            .order_by(Cinema.nom_cinema, Seance.debut)
            .all()
        )
        
        # Identifier les cinémas + inclure ID pour liens
        seances = []
        for s in seances_query:
            seance_dict = {
                'id_seance': s.id_seance,
                'date_seance': s.date_seance,
                'heure_debut': s.date_seance,  # Contient date + heure
                'version': s.version or 'VO',
                'id_cinema': s.id_cinema,  # AJOUT ID CINEMA
                'cinema_nom': s.cinema_nom or s.seance_cinema_nom or 'Cinéma non spécifié',
                'ville': s.ville
            }
            seances.append(seance_dict)
        
        print(f"✅ Film '{film_data['titre']}' avec {len(seances)} séances")
        print(f"   TMDB: {'✓' if tmdb_data else '✗'}, Synopsis: {'✓' if film_data['synopsis'] else '✗'}")
        
        return render_template('movie.html', film=film_data, seances=seances)
        
    except Exception as e:
        print(f"Erreur lors du chargement du film: {e}")
        import traceback
        traceback.print_exc()
        return "Erreur lors du chargement du film", 500

@generales.route('/discover')
@login_required
def discover():
    return redirect(url_for('generales.index'))

@generales.route('/cinemap')
def cinemap():
    """Page de la carte des cinémas"""
    return render_template('cinemap.html')

@generales.route('/api/cinemas')
def api_cinemas():
    """API pour récupérer les cinémas avec leurs films programmés - VERSION OPTIMISÉE"""
    try:
        # Mode: 'light' (sans affiches, rapide) ou 'full' (avec affiches, plus lent)
        mode = request.args.get('mode', 'light')
        
        # Récupérer les cinémas avec au moins un film programmé
        # JOIN sur nom_cinema car seance.id_cinema est NULL
        cinemas_query = (
            db.session.query(
                Cinema.id_cinema,
                Cinema.nom_cinema,
                Cinema.adresse,
                Cinema.commune,
                Cinema.latitude,
                Cinema.longitude,
                func.count(func.distinct(Seance.titre)).label('film_count')
            )
            .join(Seance, func.lower(Cinema.nom_cinema) == func.lower(Seance.nom_cinema))
            .filter(
                Cinema.latitude.isnot(None),
                Cinema.longitude.isnot(None),
                Seance.debut.isnot(None),
                # Seance.debut >= datetime.now(),  # Pas nécessaire pour l'eval mais serait nécessaire en conditions réelles
                Seance.titre.isnot(None)
            )
            .group_by(
                Cinema.id_cinema,
                Cinema.nom_cinema,
                Cinema.adresse,
                Cinema.commune,
                Cinema.latitude,
                Cinema.longitude
            )
            .having(func.count(func.distinct(Seance.titre)) > 0)
            .all()
        )
        
        # Pour chaque cinéma, récupérer les films
        cinemas_data = []
        for cinema in cinemas_query:
            # Récupérer les films de ce cinéma via le nom
            films_query = (
                db.session.query(
                    FilmTitre.id_film,
                    FilmTitre.titre
                )
                .join(Seance, func.lower(FilmTitre.titre) == func.lower(Seance.titre))
                .filter(
                    func.lower(Seance.nom_cinema) == func.lower(cinema.nom_cinema)
                )
                .distinct()
                .limit(5)  # Réduit de 10 à 5 pour popups
                .all()
            )
            
            films_list = []
            for film in films_query:
                film_data = {
                    'id_film': film.id_film,
                    'titre': film.titre,
                    'poster_url': None  # Initialiser pour éviter undefined
                }
                
                # Récupérer l'affiche TMDB seulement en mode 'full'
                if mode == 'full':
                    tmdb_data = search_movie_on_tmdb(film.titre)
                    if tmdb_data and tmdb_data.get('poster_path'):
                        film_data['poster_url'] = f"https://image.tmdb.org/t/p/w92{tmdb_data['poster_path']}"
                
                films_list.append(film_data)
            
            cinemas_data.append({
                'id_cinema': cinema.id_cinema,
                'nom_cinema': cinema.nom_cinema,
                'adresse': cinema.adresse,
                'commune': cinema.commune,
                'latitude': float(cinema.latitude) if cinema.latitude else None,
                'longitude': float(cinema.longitude) if cinema.longitude else None,
                'film_count': cinema.film_count,
                'films': films_list
            })
        
        print(f"API Cinémas ({mode}): {len(cinemas_data)} cinémas avec films programmés")
        
        return jsonify({
            'success': True,
            'cinemas': cinemas_data,
            'count': len(cinemas_data)
        })
        
    except Exception as e:
        print(f"Erreur API cinémas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'cinemas': []
        }), 500

@generales.route('/cinema/<int:id_cinema>')
def cinema(id_cinema):
    """Page de détails d'un cinéma avec ses films"""
    try:
        # Récupérer les informations du cinéma
        cinema_query = (
            db.session.query(Cinema)
            .filter(Cinema.id_cinema == id_cinema)
            .first()
        )
        
        if not cinema_query:
            print(f"Cinéma {id_cinema} non trouvé")
            return "Cinéma non trouvé", 404
        
        cinema_data = {
            'id_cinema': cinema_query.id_cinema,
            'nom_cinema': cinema_query.nom_cinema or 'Cinéma',
            'adresse': cinema_query.adresse,
            'commune': cinema_query.commune,
            'latitude': cinema_query.latitude,
            'longitude': cinema_query.longitude,
            'ecrans': cinema_query.ecrans,
            'fauteuils': cinema_query.fauteuils
        }
        
        # Récupérer tous les films programmés dans ce cinéma (via nom)
        films_query = (
            db.session.query(
                FilmTitre.id_film,
                FilmTitre.titre,
                func.count(Seance.id_seance).label('nb_seances')
            )
            .join(Seance, func.lower(FilmTitre.titre) == func.lower(Seance.titre))
            .filter(
                func.lower(Seance.nom_cinema) == func.lower(cinema_data['nom_cinema']),
                Seance.debut.isnot(None),
                Seance.debut >= datetime.now()  # Pas nécessaire pour l'eval mais serait nécessaire en conditions réelles
            )
            .group_by(FilmTitre.id_film, FilmTitre.titre)
            .order_by(FilmTitre.titre)
            .all()
        )
        
        # Enrichir avec données TMDB (parallélisé pour rapidité)
        from concurrent.futures import ThreadPoolExecutor
        
        def get_film_with_poster(film):
            """Récupère les données TMDB pour un film"""
            tmdb_data = search_movie_on_tmdb(film.titre)
            poster_url = None
            if tmdb_data and tmdb_data.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}"
            
            return {
                'id_film': film.id_film,
                'titre': film.titre,
                'nb_seances': film.nb_seances,
                'poster_url': poster_url
            }
        
        # Paralléliser les appels TMDB avec 10 workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            films_list = list(executor.map(get_film_with_poster, films_query))
        
        print(f"✅ Cinéma '{cinema_data['nom_cinema']}' avec {len(films_list)} films (optimisé)")
        
        return render_template('cinema.html', cinema=cinema_data, films=films_list)
        
    except Exception as e:
        print(f"Erreur lors du chargement du cinéma: {e}")
        import traceback
        traceback.print_exc()
        return "Erreur lors du chargement du cinéma", 500

@generales.route('/calendrier')
def calendrier():
    """Page du calendrier des séances"""
    # Vérifier si l'utilisateur est connecté via Flask-Login
    if current_user.is_authenticated: 

        try:
            # On utilise l'ID de l'utilisateur connecté via Flask-Login
            user_id = current_user.id_utilisateur
            
            # Sous-requête pour compter les autres inscrits
            counts = db.session.query(
                Calendrier.id_seance, 
                func.count(Calendrier.id_utilisateur).label('total')
            ).filter(Calendrier.id_utilisateur != user_id).group_by(Calendrier.id_seance).subquery()
            #Récupérer les séances sélectionnées avec les détails
            selections = (
                db.session.query(Calendrier, Seance, FilmTitre, counts.c.total)
                .join(Seance, Calendrier.id_seance == Seance.id_seance)
                .join(FilmTitre, func.lower(Seance.titre) == func.lower(FilmTitre.titre))
                .outerjoin(counts, Seance.id_seance == counts.c.id_seance) # Jointure pour récupérer le compte
                .filter(Calendrier.id_utilisateur == user_id)
                .all()
            )
            
            # Enrichir avec TMDB
            seances_enrichies = []
            for calendrier, seance, film, total_matches in selections:
                nb = total_matches if total_matches else 0

                # Vérifier s'il y a un match mutuel pour cette séance
                matched_user = None
                my_accepts = db.session.query(Matches.id_utilisateur2).filter(
                    Matches.id_seance == seance.id_seance,
                    Matches.id_utilisateur1 == user_id,
                    Matches.statut == 'accepte'
                ).all()
                
                for (other_user_id,) in my_accepts:
                    # Vérifier si l'autre personne m'a aussi accepté
                    reverse_match = db.session.query(Matches).filter(
                        Matches.id_seance == seance.id_seance,
                        Matches.id_utilisateur1 == other_user_id,
                        Matches.id_utilisateur2 == user_id,
                        Matches.statut == 'accepte'
                    ).first()
                    if reverse_match:
                        matched_user = other_user_id
                        break

                tmdb_data = search_movie_on_tmdb(film.titre)
                seances_enrichies.append({
                    'id_seance': seance.id_seance,
                    'id_film': film.id_film,
                    'id_cinema': seance.id_cinema,
                    'titre': film.titre,
                    'cinema': seance.nom_cinema,
                    'debut': seance.debut,
                    'nb_potentiels': nb,
                    'poster_url': f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}" if tmdb_data and tmdb_data.get('poster_path') else None,
                    'matched_user_id': matched_user
                })
            
            return render_template('calendrier.html', selections=seances_enrichies)
        except Exception as e:
            print(f"Erreur calendrier: {e}")
            import traceback
            traceback.print_exc()
            return render_template('calendrier.html', selections=[])
    else:
        return render_template('calendrier.html', selections=None)
    
@generales.route('/calendrier/liste')
@login_required
def calendrier_liste():
    """Page du calendrier en format liste"""
    # Vérifier si l'utilisateur est connecté via Flask-Login
    if current_user.is_authenticated:
        try:
            # On utilise l'ID de l'utilisateur connecté via Flask-Login
            user_id = current_user.id_utilisateur
            
            # Récupérer les séances sélectionnées avec les détails
            selections = (
                db.session.query(Calendrier, Seance, FilmTitre)
                .join(Seance, Calendrier.id_seance == Seance.id_seance)
                .join(FilmTitre, func.lower(Seance.titre) == func.lower(FilmTitre.titre))
                .filter(Calendrier.id_utilisateur == user_id)
                .order_by(Seance.debut)
                .all()
            )
            
            # Enrichir avec TMDB
            seances_enrichies = []
            for calendrier, seance, film in selections:
                # Vérifier s'il y a un match mutuel pour cette séance
                matched_user = None
                my_accepts = db.session.query(Matches.id_utilisateur2).filter(
                    Matches.id_seance == seance.id_seance,
                    Matches.id_utilisateur1 == user_id,
                    Matches.statut == 'accepte'
                ).all()
                
                for (other_user_id,) in my_accepts:
                    # Vérifier si l'autre personne m'a aussi accepté
                    reverse_match = db.session.query(Matches).filter(
                        Matches.id_seance == seance.id_seance,
                        Matches.id_utilisateur1 == other_user_id,
                        Matches.id_utilisateur2 == user_id,
                        Matches.statut == 'accepte'
                    ).first()
                    if reverse_match:
                        matched_user = other_user_id
                        break
                
                tmdb_data = search_movie_on_tmdb(film.titre)
                seances_enrichies.append({
                    'id_seance': seance.id_seance,
                    'id_film': film.id_film,
                    'id_cinema': seance.id_cinema,
                    'titre': film.titre,
                    'cinema': seance.nom_cinema,
                    'debut': seance.debut,
                    'poster_url': f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}" if tmdb_data and tmdb_data.get('poster_path') else None,
                    'matched_user_id': matched_user
                })
            
            return render_template('calendrier_liste.html', selections=seances_enrichies)
        except Exception as e:
            print(f"Erreur calendrier: {e}")
            import traceback
            traceback.print_exc()
            return render_template('calendrier_liste.html', selections=[])
    else:
        return render_template('calendrier_liste.html', selections=None)

#Utiliser le code ci-dessous si on veut faire des notifs (ATTENTION: j'ai supprimé notifications.html, il faudra le récupérer le rendre utilisable par SQLAlchemy)

# generales.route('/notifications')
# @login_required
# def notifications():
#     """
#     View all notifications for the logged-in user.
#     """
#     db = get_db()
#     cursor = db.cursor()
#     user_id = session['user_id']
    
#     cursor.execute('''
#         SELECT n.id, n.type, n.message, n.is_read, n.created_at, n.match_id,
#                u.username, u.name, u.photo_url
#         FROM notifications n
#         LEFT JOIN users u ON n.sender_id = u.id
#         WHERE n.user_id = ?
#         ORDER BY n.created_at DESC
#     ''', (user_id,))
    
#     user_notifications = cursor.fetchall()
#     db.close()
    
#     return render_template('notifications.html', notifications=user_notifications)

@generales.route('/selection_seance/<int:id_seance>', methods=['POST'])
@login_required
def selection_seance(id_seance):
    """Ajoute une séance au calendrier de l'utilisateur"""
    try:
        user_id = current_user.id_utilisateur

        # Vérification optionnelle : est-ce que la séance est déjà ajoutée ?
        deja_present = Calendrier.query.filter_by(
            id_utilisateur=user_id, 
            id_seance=id_seance
        ).first()
        
        if deja_present:
            return jsonify({'error': 'Cette séance est déjà dans votre calendrier'}), 400

        nouvelle_selection = Calendrier(
            id_utilisateur=user_id,
            id_seance=id_seance
        )
        
        db.session.add(nouvelle_selection)
        db.session.commit()
        
        # Vérifier s'il y a des matches potentiels pour cette séance
        # Chercher d'autres utilisateurs qui ont aussi cette séance dans leur calendrier
        autres_utilisateurs = db.session.query(Calendrier).filter(
            Calendrier.id_seance == id_seance,
            Calendrier.id_utilisateur != user_id
        ).count()
        
        # Vérifier s'il y a des matches que l'utilisateur n'a pas encore refusés
        matches_disponibles = db.session.query(Calendrier).filter(
            Calendrier.id_seance == id_seance,
            Calendrier.id_utilisateur != user_id
        ).join(
            Matches,
            ((Matches.id_utilisateur1 == user_id) & (Matches.id_utilisateur2 == Calendrier.id_utilisateur) & (Matches.id_seance == id_seance)),
            isouter=True
        ).filter(
            or_(Matches.statut.is_(None), Matches.statut != 'refuse')
        ).count()
        
        response_data = {
            'message': 'Séance ajoutée au calendrier !',
            'has_matches': autres_utilisateurs > 0,
            'match_count': autres_utilisateurs
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur ajout séance : {e}")
        return jsonify({'error': 'Erreur lors de l\'ajout'}), 500


@generales.route('/ma_selection')
@login_required
def ma_selection():
    """Redirige vers la page calendrier"""
    return redirect(url_for('generales.calendrier'))

@generales.route("/recherche_rapide_cine")
@generales.route("/recherche_rapide_cine/<int:page>")
def recherche_rapide_cine(page=1):
    """Recherche plein texte dans les cinémas"""
    chaine = request.args.get("chaine", None)

    if chaine: 
        resultats = Cinema.query.\
            filter(
                or_(
                    Cinema.nom_cinema.ilike("%"+chaine+"%"),
                    Cinema.adresse.ilike("%"+chaine+"%"),
                    Cinema.commune.ilike("%"+chaine+"%"),
                    Cinema.numero_uu.cast(String).ilike("%"+chaine+"%"), 
                    Cinema.ecrans.cast(String).ilike("%"+chaine+"%"), 
                    Cinema.fauteuils.cast(String).ilike("%"+chaine+"%")
                )
            ).\
            order_by(Cinema.nom_cinema).\
            paginate(page=page, per_page=current_app.config.get("CINE_PER_PAGE", 10))
    else:
        resultats = None
        
    return render_template("resultats_recherche_cinemas.html", 
            sous_titre="Recherche | " + chaine if chaine else "Recherche", 
            donnees=resultats,
            requete=chaine)


#filtres avancés sur la recherche de films
#Il a fallu utiliser un LLM pour séparer les genres car ils étaient présentés comme "Drame, Comedie, Action" au lieu d'être séparés dans le menu de sélection
@generales.route("/recherche_rapide_film")
@generales.route("/recherche_rapide_film/<int:page>")
def recherche_rapide_film(page=1):
    form = FiltreFilmForm(request.args)
    
    # 1. Remplissage dynamique des genres (Nettoyage des doublons combinés)
    # On récupère toutes les chaînes de genres
    raw_genres = db.session.query(Film.genre).distinct().all()
    
    set_genres = set()
    for row in raw_genres:
        if row.genre:
            # On sépare par la virgule, on nettoie les espaces et on ajoute au set
            parts = [g.strip() for g in row.genre.split(',')]
            set_genres.update(parts)
    
    # On trie par ordre alphabétique pour le confort de l'utilisateur
    form.genre.choices = [('', 'Tous les genres')] + [(g, g) for g in sorted(list(set_genres))]

    # 2. Construction de la requête
    query = db.session.query(FilmTitre)

    # 3. Ajout des filtres (Correction du DuplicateAlias et du filtre Genre)
    chaine = form.chaine.data
    if chaine:
        query = query.filter(FilmTitre.titre.ilike(f"%{chaine}%"))
    
    # On fait le JOIN une seule fois si besoin
    if form.genre.data or form.annee.data:
        query = query.join(Film)

        if form.genre.data:
            # Utilisation de ILIKE pour trouver le genre même s'il y en a plusieurs
            # Exemple : trouver "Drama" dans "Drama, Comedy"
            query = query.filter(Film.genre.ilike(f"%{form.genre.data}%"))
            
        if form.annee.data:
            valeur_annee = str(form.annee.data).strip()
            if valeur_annee:
                query = query.filter(
                    cast(Film.date_sortie, String).contains(valeur_annee)
                )

    # 4. Tri et Pagination
    # Attention : .distinct(FilmTitre.titre) nécessite que le ORDER BY commence par FilmTitre.titre
    query = query.distinct(FilmTitre.titre).order_by(FilmTitre.titre)
    
    per_page = 30
    total = query.count()
    films = query.limit(per_page).offset((page - 1) * per_page).all()
    
    resultats = SimplePagination(films, page, per_page, total)
        
    return render_template("resultats_recherche_films.html", 
            form=form, 
            donnees=resultats,
            requete=chaine)