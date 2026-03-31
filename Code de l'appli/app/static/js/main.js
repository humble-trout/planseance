// header avec scroll
document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('.header-container');
    const isHomePage = document.body.classList.contains('home-page');
    const homeLayout = document.querySelector('.home-layout');
    const otherLayout = document.querySelector('.other-pages-layout');
    const centerLogo = document.querySelector('.header-logo-center');
    
    if (isHomePage && homeLayout && otherLayout) {
        // Sur la page d'accueil : on commence avec le logo centré
        homeLayout.style.display = 'flex';
        otherLayout.style.display = 'none';
        header.classList.add('header-large');
        
        // Au scroll, on passe au layout compact
        window.addEventListener('scroll', function() {
            if (window.scrollY > 100) {
                // Mode condensé : layout à gauche
                homeLayout.style.display = 'none';
                otherLayout.style.display = 'flex';
                header.classList.remove('header-large');
                header.classList.add('header-condensed');
            } else {
                // Mode large : logo centré
                homeLayout.style.display = 'flex';
                otherLayout.style.display = 'none';
                header.classList.remove('header-condensed');
                header.classList.add('header-large');
            }
        });
    } else if (otherLayout && homeLayout) {
        // Sur les autres pages : layout compact d'emblée
        homeLayout.style.display = 'none';
        otherLayout.style.display = 'flex';
        header.classList.add('header-condensed');
    }
});


// recherche en temps reel ?

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-bar');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const movieCards = document.querySelectorAll('.movie-card');
        
        movieCards.forEach(card => {
            const title = card.querySelector('.movie-title').textContent.toLowerCase();
            if (title.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// api affiche

const TMDB_API_KEY = '0d88ecf84847b9983d64130b5894bade'; // À remplacer par votre clé API
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';

async function fetchMoviePoster(movieTitle, imgElement) {
    try {
        // Recherche du film par titre
        const searchUrl = `${TMDB_BASE_URL}/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(movieTitle)}&language=fr-FR`;
        const response = await fetch(searchUrl);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            const movie = data.results[0];
            if (movie.poster_path) {
                imgElement.src = TMDB_IMAGE_BASE + movie.poster_path;
                imgElement.alt = movie.title;
            } else {
                // Image par défaut si pas d'affiche
                imgElement.src = '/static/img/no-poster.jpg';
            }
        } else {
            imgElement.src = '/static/img/no-poster.jpg';
        }
    } catch (error) {
        console.error('Erreur lors de la récupération de l\'affiche:', error);
        imgElement.src = '/static/img/no-poster.jpg';
    }
}

// Charge toutes les affiches au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const moviePosters = document.querySelectorAll('.movie-poster[data-movie-title]');
    
    moviePosters.forEach(poster => {
        const movieTitle = poster.getAttribute('data-movie-title');
        fetchMoviePoster(movieTitle, poster);
    });
});

//info film
async function fetchMovieDetails(movieTitle) {
    try {
        const searchUrl = `${TMDB_BASE_URL}/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(movieTitle)}&language=fr-FR`;
        const response = await fetch(searchUrl);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            const movieId = data.results[0].id;
            
            // Récupère les détails complets avec les crédits
            const detailsUrl = `${TMDB_BASE_URL}/movie/${movieId}?api_key=${TMDB_API_KEY}&append_to_response=credits&language=fr-FR`;
            const detailsResponse = await fetch(detailsUrl);
            const details = await detailsResponse.json();
            
            return details;
        }
        return null;
    } catch (error) {
        console.error('Erreur lors de la récupération des détails:', error);
        return null;
    }
}

// Charge les détails sur la page film
document.addEventListener('DOMContentLoaded', async function() {
    const movieDetailsContainer = document.querySelector('.movie-details-container');
    if (!movieDetailsContainer) return;
    
    const movieTitle = movieDetailsContainer.getAttribute('data-movie-title');
    if (!movieTitle) return;
    
    const details = await fetchMovieDetails(movieTitle);
    
    const synopsisLoading = document.getElementById('synopsis-loading');
    const synopsisContent = document.getElementById('synopsis-content');
    const tmdbExtraInfo = document.getElementById('tmdb-extra-info');
    
    if (!details) {
        if (synopsisLoading) {
            synopsisLoading.textContent = 'Informations TMDB non disponibles pour ce film.';
        }
        return;
    }
    
    // Cache le message de chargement
    if (synopsisLoading) synopsisLoading.style.display = 'none';
    
    // Affiche le synopsis
    if (synopsisContent && details.overview) {
        synopsisContent.innerHTML = details.overview;
        synopsisContent.style.display = 'block';
    } else if (synopsisContent) {
        synopsisContent.innerHTML = '<em>Synopsis non disponible.</em>';
        synopsisContent.style.display = 'block';
    }
    
    // Met à jour l'affiche
    const posterImg = document.querySelector('.movie-detail-poster');
    if (posterImg && details.poster_path) {
        posterImg.src = TMDB_IMAGE_BASE + details.poster_path;
    }
    
    // Ajoute les informations supplémentaires
    if (tmdbExtraInfo) {
        let extraHTML = '<div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid var(--rose-clair);">';
        
        // Budget et revenus
        if (details.budget && details.budget > 0) {
            extraHTML += `<p class="movie-meta"><strong>Budget :</strong> ${(details.budget / 1000000).toFixed(1)}M $</p>`;
        }
        if (details.revenue && details.revenue > 0) {
            extraHTML += `<p class="movie-meta"><strong>Box-office :</strong> ${(details.revenue / 1000000).toFixed(1)}M $</p>`;
        }
        
        // Note TMDB
        if (details.vote_average) {
            const stars = '⭐'.repeat(Math.round(details.vote_average / 2));
            extraHTML += `<p class="movie-meta"><strong>Note TMDB :</strong> ${details.vote_average.toFixed(1)}/10 ${stars} (${details.vote_count} votes)</p>`;
        }
        
        // Langues
        if (details.spoken_languages && details.spoken_languages.length > 0) {
            const langues = details.spoken_languages.map(l => l.name).join(', ');
            extraHTML += `<p class="movie-meta"><strong>Langues :</strong> ${langues}</p>`;
        }
        
        // Pays de production
        if (details.production_countries && details.production_countries.length > 0) {
            const pays = details.production_countries.map(p => p.name).join(', ');
            extraHTML += `<p class="movie-meta"><strong>Pays :</strong> ${pays}</p>`;
        }
        
        extraHTML += '</div>';
        tmdbExtraInfo.innerHTML = extraHTML;
    }
    
    console.log('✅ Données TMDB chargées pour:', movieTitle);
});
