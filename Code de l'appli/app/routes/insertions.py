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
        # On utilise directement l'ID de l'objet current_user
        # Note : adaptez .id_utilisateur si votre clé primaire se nomme autrement
        user_id = current_user.id_utilisateur
        
        # Chercher l'entrée appartenant spécifiquement à cet utilisateur
        calendrier_entry = Calendrier.query.filter_by(
            id_utilisateur=user_id,
            id_seance=id_seance
        ).first()
        
        if not calendrier_entry:
            return jsonify({
                'success': False, 
                'message': 'Séance non trouvée dans votre calendrier'
            }), 404
        
        # Suppression
        db.session.delete(calendrier_entry)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Séance supprimée avec succès'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        # Log de l'erreur pour le debug, mais message générique pour le client
        print(f"Erreur lors de la suppression: {e}")
        return jsonify({
            'success': False, 
            'message': 'Une erreur interne est survenue'
        }), 500
    
# Il y a deux supprimer_seance?? on en supprime un? eva c'est toi qui as fait ça
    
# @insertions.route('/calendrier/supprimer/<int:id_seance>', methods=['DELETE'])
# def supprimer_seance(id_seance):
#     """Supprime une séance du calendrier de l'utilisateur"""
#     user_id = current_user.id_utilisateur
#     # Vérifier si l'utilisateur est connecté
#     if 'user_id' not in session:
#         return jsonify({'success': False, 'message': 'Non connecté'}), 401
    
#     try:
#         user_id = session['user_id']
        
#         # Chercher l'entrée dans le calendrier
#         calendrier_entry = Calendrier.query.filter_by(
#             id_utilisateur=user_id,
#             id_seance=id_seance
#         ).first()
        
#         if not calendrier_entry:
#             return jsonify({'success': False, 'message': 'Séance non trouvée dans votre calendrier'}), 404
        
#         # Supprimer l'entrée
#         db.session.delete(calendrier_entry)
#         db.session.commit()
        
#         return jsonify({'success': True, 'message': 'Séance supprimée avec succès'}), 200
        
    # except Exception as e:
    #     db.session.rollback()
    #     print(f"Erreur lors de la suppression: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500


@insertions.route('/cinematch')
def api_cinematch():
    """Trouve des profils basés sur les séances communes sans système de likes."""
    
    # Vérifier si l'utilisateur est connecté
    if not current_user.is_authenticated:
        return render_template('cinematch.html', matches=None)
    
    user_id = current_user.id_utilisateur
        
    # Trouver les propres séances (id_seance) de l'utilisateur
    mes_seances_query = db.session.query(Calendrier.id_seance).filter(
        Calendrier.id_utilisateur == user_id
    ).all()
    liste_mes_seances = [s[0] for s in mes_seances_query]
    
    # Si l'utilisateur n'a rien mis dans son calendrier, on ne peut rien lui proposer
    if not liste_mes_seances:
        flash("Ajoutez d'abord des séances à votre calendrier !", "info")
        return redirect(url_for('generales.calendrier'))

    # 4. Trouver les autres entrées de calendrier pour les mêmes séances
    #Ce code est généré par un LLM et plus complexe qu'il ne le faudrait car nous avions des problèmes d'importation de données qui ont été difficiles à régler
    suggestions = db.session.query(Calendrier).filter(
        Calendrier.id_seance.in_(liste_mes_seances),
        Calendrier.id_utilisateur != user_id
    ).all()

    # 5. Récupérer les données des profils et construire la réponse
    results = []

    today = date.today() # On récupère la date du jour
    
    # La boucle commence ici
    for sugg in suggestions:
        p = sugg.utilisateur  # Relation Calendrier -> Utilisateur
        seance_info = sugg.seance # Relation Calendrier -> Seance
        s_id = seance_info.id_seance # On définit s_id pour les requêtes suivantes

        # 1. Mon statut vis-à-vis de lui
        mon_choix = Matches.query.filter_by(id_utilisateur1=user_id, id_utilisateur2=p.id_utilisateur, id_seance=s_id).first()
        
        # 2. Son statut vis-à-vis de moi
        son_choix = Matches.query.filter_by(id_utilisateur1=p.id_utilisateur, id_utilisateur2=user_id, id_seance=s_id).first()

        # --- LOGIQUE DE DISPARITION ---
        # On passe à la suggestion suivante (continue) si :
        # - J'ai dit 'refuse'
        # - OU il a dit 'refuse'
        if (mon_choix and mon_choix.statut == 'refuse') or (son_choix and son_choix.statut == 'refuse'):
            continue 

        # On prépare les booléens pour le template
        i_accepted = mon_choix.statut == 'accepte' if mon_choix else False
        they_accepted = son_choix.statut == 'accepte' if son_choix else False

        # Calcul de l'âge
        age = None
        if p.date_naissance:
            # Calcul : année actuelle - année de naissance
            # On retire 1 si l'anniversaire n'est pas encore passé cette année
            age = today.year - p.date_naissance.year - (
                (today.month, today.day) < (p.date_naissance.month, p.date_naissance.day)
            )

        # Récupérer le cinéma favori
        cinema_fav = db.session.query(Cinema.nom_cinema).join(
            CinemaFavori, Cinema.id_cinema == CinemaFavori.id_cinema
        ).filter(CinemaFavori.id_utilisateur == p.id_utilisateur).first()
        
        # Récupérer les films récemment vus (via calendrier - les 3 derniers)
        films_recents_query = db.session.query(Seance.titre).join(
            Calendrier, Calendrier.id_seance == Seance.id_seance
        ).filter(
            Calendrier.id_utilisateur == p.id_utilisateur,
            Seance.titre.isnot(None)
        ).distinct().limit(3).all()

        # Récupérer le titre du film pour cette séance
        film_titre = db.session.query(FilmTitre).filter(
            func.lower(FilmTitre.titre) == func.lower(seance_info.titre)
        ).first()

        # On ajoute chaque match trouvé à la liste 'results'
        results.append({
            'match_user': {
                'id': p.id_utilisateur,
                'name': p.nom,
                'age': age,           # On envoie l'âge calculé ici
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

            # On envoie les deux infos au template
            'i_accepted': i_accepted,
            'they_accepted': they_accepted,
            'is_mutual': i_accepted and they_accepted
        })
    
    # Compter les matches potentiels (total) et confirmés (mutuels)
    total_matches = len(results)
    confirmed_matches = sum(1 for match in results if match['is_mutual'])
    
    # On retourne le template avec les résultats (limités aux 20 premiers. il ne faudrait pas trop être un tombeur)
    return render_template('cinematch.html', 
                         matches=results[:20],
                         total_matches=total_matches,
                         confirmed_matches=confirmed_matches)

@insertions.route('/valider_match/<int:id_matchee>/<int:id_seance>/<string:action>')
@login_required
def valider_match(id_matchee, id_seance, action):
    # On cherche si une interaction existe déjà
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
        match.statut = 'accepte' # On marque comme accepté
    
    elif action == 'decline':
        if not match:
            match = Matches(id_utilisateur1=current_user.id_utilisateur, 
                            id_utilisateur2=id_matchee, 
                            id_seance=id_seance)
            db.session.add(match)
        match.statut = 'refuse' # On marque comme refusé (la carte disparaîtra)

    db.session.commit()
    return redirect(url_for('insertions.api_cinematch'))