BEGIN;

SET search_path TO psch;

--UPDATE dans la table cinema pour y inclure un id_aire_geographique

UPDATE cinema c
SET id_aire_geographique = ag.id_aire_geographique
FROM aire_geographique ag
WHERE c.commune = ag.commune ;


--UPDATE pour la table séance, permettant de rajouter les clés secondaires id_film et id_cinéma

UPDATE seance a
SET id_film = ft.id_film 
FROM film_titre ft 
WHERE a.titre ilike ft.titre  ;

--update pour la clé id_cinema

UPDATE seance a
SET id_cinema = g.id_cinema 
FROM cinema g
WHERE a.nom_cinema = g.nom_cinema  ;

--UPDATE pour la table fréquentation, permettant de rajouter une clé secondaire id_cinéma. nous utilisons l'adresse du cinéma plutôt que son nom car les adresses sont plus distinctes 

--update pour les ids
UPDATE frequentation L
SET id_cinema = g.id_cinema 
FROM cinema g
WHERE L.adresse_cinema = g.adresse  ;


--UPDATE équivalent pour la table programmation_cinema, permettant de rajouter une clé secondaire id_cinéma
UPDATE programmation_cinema pc
SET id_cinema = g.id_cinema 
FROM cinema g
WHERE pc.adresse_cinema = g.adresse  ;

COMMIT ;
