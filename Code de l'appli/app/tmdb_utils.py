
#Utilitaires pour l'API TMDB avec cache mémoire

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration TMDB
TMDB_API_KEY = '0d88ecf84847b9983d64130b5894bade'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

# Cache mémoire
_tmdb_cache: Dict[str, Any] = {}
_cache_timestamp: Dict[str, datetime] = {}
CACHE_DURATION = timedelta(hours=24)  # Cache valide 24h


def _is_cache_valid(cache_key: str) -> bool:
    """Vérifie si le cache est encore valide"""
    if cache_key not in _cache_timestamp:
        return False
    return datetime.now() - _cache_timestamp[cache_key] < CACHE_DURATION


def search_movie_on_tmdb(titre: str) -> Optional[Dict[str, Any]]:
    """
    Recherche un film sur TMDB et retourne les détails
    Utilise le cache mémoire pour éviter les requêtes répétées
    
    Returns:
        Dico avec les infos du film si trouvé, None sinon
    """
    cache_key = f"search_{titre.lower()}"
    
    # Vérifier le cache
    if _is_cache_valid(cache_key):
        return _tmdb_cache.get(cache_key)
    
    try:
        # Recherche du film
        search_url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': TMDB_API_KEY,
            'query': titre,
            'language': 'fr-FR'
        }
        
        response = requests.get(search_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            movie = data['results'][0]
            
            # Récupérer les détails complets
            movie_id = movie['id']
            details = get_movie_details(movie_id)
            
            # Mettre en cache
            _tmdb_cache[cache_key] = details
            _cache_timestamp[cache_key] = datetime.now()
            
            return details
        else:
            # Film non trouvé - mettre en cache aussi pour éviter de réessayer
            _tmdb_cache[cache_key] = None
            _cache_timestamp[cache_key] = datetime.now()
            return None
            
    except Exception as e:
        print(f"Erreur TMDB pour '{titre}': {e}")
        return None


def get_movie_details(movie_id: int) -> Optional[Dict[str, Any]]:
    """
    récup les détails complets d'un film depuis TMDB
    """
    cache_key = f"details_{movie_id}"
    
    # vérifier le cache
    if _is_cache_valid(cache_key):
        return _tmdb_cache.get(cache_key)
    
    try:
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'append_to_response': 'credits',
            'language': 'fr-FR'
        }
        
        response = requests.get(details_url, params=params, timeout=5)
        response.raise_for_status()
        details = response.json()
        
        # Mettre en cache
        _tmdb_cache[cache_key] = details
        _cache_timestamp[cache_key] = datetime.now()
        
        return details
        
    except Exception as e:
        print(f"Erreur détails TMDB pour ID {movie_id}: {e}")
        return None


def get_poster_url(poster_path: Optional[str]) -> str:
    """
    retourne l'URL complète du poster TMDB
    """
    if poster_path:
        return f"{TMDB_IMAGE_BASE}{poster_path}"
    return "/static/img/placeholder-poster.jpg"


def clear_cache():
    """vide le cache mémoire"""
    global _tmdb_cache, _cache_timestamp
    _tmdb_cache.clear()
    _cache_timestamp.clear()
    print("Cache vidé")


def get_cache_stats() -> Dict[str, int]:
    """retourne des statistiques sur le cache"""
    valid_entries = sum(1 for key in _tmdb_cache.keys() if _is_cache_valid(key))
    return {
        'total_entries': len(_tmdb_cache),
        'valid_entries': valid_entries,
        'expired_entries': len(_tmdb_cache) - valid_entries
    }
