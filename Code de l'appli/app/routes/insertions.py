from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, flash
from app.utils import db
from app.models import Utilisateur, Calendrier, Matches, Seance, Film, FilmTitre, Cinema, CinemaFavori
from sqlalchemy import or_, and_, func
from flask_login import current_user, login_required
from datetime import date

insertions = Blueprint('insertions', __name__)


@insertions.route('/calendrier/supprimer/<int:id_seance>', methods=['DELETE'])
@login_required # Remplace avantageusement la vérification manuelle de session
def supprimer_seance(id_seance):
    """Supprime une séance du calendrier de l'utilisateur connecté"""
    try:
        user_id = current_user.id_utilisateur
        
        #Chercher l'entrée dans le calendrier liée spécifiquement à cet utilisateur
        calendrier_entry = Calendrier.query.filter_by(
            id_utilisateur=user_id,
            id_seance=id_seance
        ).first()
        
        if not calendrier_entry:
            return jsonify({
                'success': False, 
                'message': 'Séance non trouvée dans votre calendrier'
            }), 404
        
        #Suppression de la séance
        db.session.delete(calendrier_entry)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Séance supprimée avec succès'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la suppression: {e}")
        return jsonify({
            'success': False, 
            'message': 'Une erreur interne est survenue'
        }), 500
    

@insertions.route('/cinematch')
def api_cinematch():
    """Trouve des profils basés sur les séances communes sans système de likes."""
    
    #Si l'utilisateur n'est pas connecté, la page Cinématch affichée est différente
    if not current_user.is_authenticated:
        return render_template('cinematch.html', matches=None)
    
    user_id = current_user.id_utilisateur
        
    #Trouve les séances de l'utilisateur
    mes_seances_query = db.session.query(Calendrier.id_seance).filter(
        Calendrier.id_utilisateur == user_id
    ).all()
    liste_mes_seances = [s[0] for s in mes_seances_query]
    
    #S'arrête là si l'utilisateur n'a pas de séances à son calendrier
    if not liste_mes_seances:
        flash("Ajoutez d'abord des séances à votre calendrier !", "info")
        return redirect(url_for('generales.calendrier'))

    #Cherche les entrées dans le calendrier d'autres utilisateurs correspondant à la même séance
    #Ce bout de code est généré par un LLM et probablement plus complexe qu'il ne le faudrait car nous avions des problèmes d'importation de données des profils utilisateurs dans Cinématch qui ont été difficiles à régler, je ne me souviens pas de la version plus simple
    suggestions = db.session.query(Calendrier).filter(
        Calendrier.id_seance.in_(liste_mes_seances),
        Calendrier.id_utilisateur != user_id
    ).all()

    #récupère les données des profils
    results = []

    today = date.today() #Récupère la date du jour
    
    #Le code suivant a été amélioré avec un LLM car nous ne parvenions pas à rendre le matching réciproque et à faire en sorte que les matchings refusés restent disparus lorsque la page était rafraîchie
    for sugg in suggestions:
        p = sugg.utilisateur  #Relation Calendrier à Utilisateur
        seance_info = sugg.seance #Relation Calendrier à Seance
        s_id = seance_info.id_seance

        #Choix de l'utilisateur présent de matcher ou pas
        mon_choix = Matches.query.filter_by(id_utilisateur1=user_id, id_utilisateur2=p.id_utilisateur, id_seance=s_id).first()
        
        #Choix de l'autre utilisateur de matcher ou pas
        son_choix = Matches.query.filter_by(id_utilisateur1=p.id_utilisateur, id_utilisateur2=user_id, id_seance=s_id).first()

        #Disparition des profils où le matching a été refusé, que l'utilisateur présent ou l'autre utilisateur en soit à l'origine
        if (mon_choix and mon_choix.statut == 'refuse') or (son_choix and son_choix.statut == 'refuse'):
            continue 

        #Booléens repris dans la boucle Jinja if du template Cinématch
        i_accepted = mon_choix.statut == 'accepte' if mon_choix else False
        they_accepted = son_choix.statut == 'accepte' if son_choix else False
        
        #Affichage du profil de l'autre utilisateur

        #Récupère l'âge de l'autre utilisateur pour l'afficher sur le profil en soustrayant l'année de naissance à l'année actuelle
        age = None
        if p.date_naissance:
            #On retire 1 si l'anniversaire n'est pas encore passé à la date d'aujourd'hui
            age = today.year - p.date_naissance.year - (
                (today.month, today.day) < (p.date_naissance.month, p.date_naissance.day)
            )

        #Récupère le cinéma favori de l'autre utilisateur
        cinema_fav = db.session.query(Cinema.nom_cinema).join(
            CinemaFavori, Cinema.id_cinema == CinemaFavori.id_cinema
        ).filter(CinemaFavori.id_utilisateur == p.id_utilisateur).first()
        
        #Récupère les 3 films récemment vus dans le calendrier de l'autre utilisateur
        films_recents_query = db.session.query(Seance.titre).join(
            Calendrier, Calendrier.id_seance == Seance.id_seance
        ).filter(
            Calendrier.id_utilisateur == p.id_utilisateur,
            Seance.titre.isnot(None)
        ).distinct().limit(3).all()

        #Récupère le titre du film pour cette séance
        film_titre = db.session.query(FilmTitre).filter(
            func.lower(FilmTitre.titre) == func.lower(seance_info.titre)
        ).first()

        #On ajoute chaque match trouvé à la liste 'results'
        results.append({
            'match_user': {
                'id': p.id_utilisateur,
                'name': p.nom,
                'age': age,
                'username': p.nom_utilisateur,
                'bio': p.bio,
                'photo_url': p.photo_url,
                'cinema_favori': cinema_fav[0] if cinema_fav else None,
                'films_recents': [f[0] for f in films_recents_query] if films_recents_query else []
            },
            'seance': {
                'id': s_id,
                'horaire': seance_info.debut.strftime('%H:%M') if seance_info.debut else None,
                'date': seance_info.debut.strftime('%d/%m/%Y') if seance_info.debut else "Date inconnue",
                'cinema_nom': seance_info.nom_cinema if seance_info.nom_cinema else "Cinéma inconnu",
                'film_titre': film_titre.titre if film_titre else seance_info.titre,
                'film_id': film_titre.id_film if film_titre else None
            },

            #Pour les boucles du template cinematch
            'i_accepted': i_accepted,
            'they_accepted': they_accepted,
            'is_mutual': i_accepted and they_accepted
        })
    
    #Compte les matches potentiels (total) et confirmés (mutuels)
    total_matches = len(results)
    confirmed_matches = sum(1 for match in results if match['is_mutual'])
    
    #On retourne le template avec les résultats (limités aux 10 premiers, 10 matchs c'est déjà pas mal!)
    return render_template('cinematch.html', 
                         matches=results[:10],
                         total_matches=total_matches,
                         confirmed_matches=confirmed_matches)

@insertions.route('/valider_match/<int:id_matchee>/<int:id_seance>/<string:action>')
@login_required
def valider_match(id_matchee, id_seance, action):
    """Valide les matchs mutuels"""
    #Cherche s'il y a un match potentiel sur la même séance
    match = Matches.query.filter_by(
        id_utilisateur1=current_user.id_utilisateur,
        id_utilisateur2=id_matchee,
        id_seance=id_seance
    ).first()

    if action == 'accept':
        if not match:
            match = Matches(id_utilisateur1=current_user.id_utilisateur, 
                            id_utilisateur2=id_matchee, 
                            id_seance=id_seance)
            db.session.add(match)
        match.statut = 'accepte'
    
    elif action == 'decline':
        if not match:
            match = Matches(id_utilisateur1=current_user.id_utilisateur, 
                            id_utilisateur2=id_matchee, 
                            id_seance=id_seance)
            db.session.add(match)
        match.statut = 'refuse'

    db.session.commit()
    return redirect(url_for('insertions.api_cinematch'))
