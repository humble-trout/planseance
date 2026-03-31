BEGIN;

-- nom de schéma définitif
SET search_path TO psch;

-- initialisation des tables temporaire



--jeux de données du CNC sur les cinéma

	-- correction de la qualité, majoritairement des attributs non reconnus comme int et maj/espace/
-- on ne corrige pas en profondeur les champs qu'on n'utilisera pas

CREATE TABLE if not exists tmp_cnc AS (
SELECT 
    CAST(rc."régionCNC" AS INTEGER) AS region_cnc,
    CAST(rc."N° auto" AS INTEGER) AS n_auto,
    TRIM(INITCAP(rc.nom)) AS nom_cinema,
    TRIM(INITCAP(rc."région administrative")) AS region_administrative,
    TRIM(INITCAP(rc.adresse)) AS adresse,
    rc."code INSEE" AS code_insee,
    rc.commune AS commune,
    rc."population de la commune" AS population_commune,
    CAST(CASE 
        	WHEN Trim(rc."DEP") IN ('2A', '2B') THEN '20'
        	ELSE rc."DEP"
    	END AS INTEGER) AS departement, 
    rc."N°UU" AS n_uu,
    rc."unité urbaine" AS unite_urbaine, 
    rc."population unité urbaine" AS population_unite_urbaine, 
    rc."situation géographique" AS situation_geographique, 
    CAST(rc."écrans" AS INTEGER) AS ecrans, 
    CAST(rc.fauteuils AS INTEGER) AS fauteuils, 
    CAST(rc."semaines d'activité" AS INTEGER) AS semaines_activite, 
    CAST(REGEXP_REPLACE(rc."séances", '[^0-9]', '', 'g') AS INTEGER) AS seances_annuelles, 
    CAST(REGEXP_REPLACE(rc."entrées 2024", '[^0-9]', '', 'g') AS INTEGER) AS entree_24, 
    --corriger pb de vide
    CAST(REGEXP_REPLACE(NULLIF(rc."entrées 2023", ''), '[^0-9]', '', 'g') AS INTEGER) AS entree_23,
    rc."évolution entrées" AS evolution_entrees, 
    rc."tranche d'entrées" AS tranche_entrees, 
    rc."propriétaire" AS proprietaire, 
    --tranformer en vrai booleen
    CAST(CASE
            WHEN rc."AE" = 'OUI' THEN TRUE
            ELSE FALSE
        END AS BOOLEAN) AS art_et_essai, 
    rc."catégorie Art et Essai" AS categorie_ae, 
    rc."label Art et Essai" AS label_ae, 
    rc.genre AS genre, 
    CAST(CASE
            WHEN rc.multiplexe = 'OUI' THEN TRUE
            ELSE FALSE
        END AS BOOLEAN) AS multiplexe,
    rc."zone de la commune" AS zone_commune, 
    CAST(rc."nombre de films programmés" AS INTEGER) AS nb_films_programmes, 
    CAST(rc."nombre de films inédits" AS INTEGER) AS nb_films_inedits, 
    CAST(rc."nombre de films en semaine 1" AS INTEGER) AS nb_films_semaine_1, 
    -- rendre les pourcentages exploitables
    CAST(REGEXP_REPLACE(REPLACE(rc."PdM en entrées des films français", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS pdm_films_francais, 
    CAST(REGEXP_REPLACE(REPLACE(rc."PdM en entrées des films américains", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS pdm_films_americains, 
    CAST(REGEXP_REPLACE(REPLACE(rc."PdM en entrées des films européens", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS pdm_films_europeens, 
    CAST(REGEXP_REPLACE(REPLACE(rc."PdM en entrées des autres films", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS pdm_autres_films, 
    CAST(rc."films Art et Essai" AS INTEGER) AS nb_films_ae, 
    CAST(REGEXP_REPLACE(REPLACE(rc."part des séances de films Art et Essai", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS part_seances_ae, 
    CAST(REGEXP_REPLACE(REPLACE(rc."PdM en entrées des films Art et Essai", ',', '.'), '[^0-9.]', '', 'g') AS REAL) AS pdm_films_ae,
    CAST(rc.latitude AS REAL) AS latitude, 
    CAST(rc.longitude AS REAL) AS longitude
FROM raw_cnc rc );

-- jeux de données sur les cinémas de data.gouv

	-- jeux extremement similaire au précédent donc traitement similaire, mais la reconnaissance du type etaot plus simple


CREATE TABLE if not exists tmp_etab_cine AS (
SELECT 
    CAST(re."﻿régionCNC" AS INTEGER) AS region_cnc, -- caractere invisible je n'ai pas réussi a le résoudre autrement qu'en le rendant "visible"
    CAST(re."N° auto" AS INTEGER) AS n_auto,
    TRIM(INITCAP(re.nom)) AS nom_cinema,
    TRIM(INITCAP(re."région administrative")) AS region_administrative,
    TRIM(INITCAP(re.adresse)) AS adresse,
    re."code INSEE" AS code_insee,
    re.commune AS commune,
    re."population de la commune" AS population_commune,
    CAST(CASE 
        	WHEN Trim(re."DEP") IN ('2A', '2B') THEN '20'
        	ELSE re."DEP"
    	END AS INTEGER) AS departement,
    re."N°UU" AS n_uu,
    re."unité urbaine" AS unite_urbaine, 
    FLOOR(CAST(re."population unité urbaine" AS FLOAT)) AS population_unite_urbaine,
    re."situation géographique" AS situation_geographique, 
    FLOOR(CAST(re."écrans" AS FLOAT)) AS ecrans, 
    FLOOR(CAST(re.fauteuils AS FLOAT)) AS fauteuils, 
    FLOOR(CAST(re."semaines d'activité" AS FLOAT)) AS semaines_activite, 
    FLOOR(CAST(re."séances" AS FLOAT)) AS seances,
    FLOOR(CAST(re."entrées 2022" AS FLOAT)) AS entree_22,
    FLOOR(CAST(re."entrées 2021" AS FLOAT)) AS entree_21,
    re."évolution entrées" AS evolution_entrees, 
    re."tranche d'entrées" AS tranche_entrees, 
    re."programmateur" AS programmateur, 
    CAST(CASE
            WHEN re."AE" = 'OUI' THEN TRUE
            ELSE FALSE
        END AS BOOLEAN) AS art_et_essai, 
    re."catégorie Art et Essai" AS categorie_ae, 
    re."label Art et Essai" AS label_ae, 
    re.genre AS genre, 
    CAST(CASE
            WHEN re.multiplexe = 'OUI' THEN TRUE
            ELSE FALSE
        END AS BOOLEAN) AS multiplexe,
    re."zone de la commune" AS zone_commune, 
    FLOOR(CAST(NULLIF(REGEXP_REPLACE(CAST(re."nombre de films programmés" AS TEXT), '[^0-9.]', '', 'g'), '') AS FLOAT)) AS nb_films_programmes, --pcq il y a du contenu 'C' 
    FLOOR(CAST(re."nombre de films inédits" AS FLOAT)) AS nb_films_inedits, 
    FLOOR(CAST(re."nombre de films en semaine 1" AS FLOAT)) AS nb_films_semaine_1, 
    CAST(re."PdM en entrées des films français" AS REAL) AS pdm_films_francais, 
    CAST(re."PdM en entrées des films américains" AS REAL) AS pdm_films_americains, 
    CAST(re."PdM en entrées des films européens" AS REAL) AS pdm_films_europeens, 
    CAST(re."PdM en entrées des autres films" AS REAL) AS pdm_autres_films, 
    FLOOR(CAST(re."films Art et Essai" AS FLOAT)) AS nb_films_ae, 
    CAST(re."PdM en entrées des films Art et Essai" AS REAL) AS pdm_films_ae,
    CAST(re.latitude AS REAL) AS latitude, 
    CAST(re.longitude AS REAL) AS longitude
FROM raw_etab_cine re );


-- jeux de données sur la programmation des cinémas indépendants
	-- le traitement est plus léger car les données concernant les films eux meme proviendront a terme d'un csv different

CREATE TABLE if not exists tmp_programation AS 
	select TRIM(INITCAP(filmtitle)) AS titre,
	INITCAP(TRIM(rp.filmdirector)) as realisateur,
	INITCAP(TRIM(rp.filmcast)) as distribution,
    CAST(rp.filmstoryline as text) as resume,
    rp.filmgenre as genre,
    rp.filmcountry as pays_film,
    CAST(NULLIF(rp.showstart, '') AS timestamp with time zone) AS debut_seance,
    CAST(NULLIF(rp.showend, '') AS timestamp with time zone) AS fin_seance,
    rp.evenement,
    rp.auditoriumnumber as salle,
    CASE 
    	WHEN TRIM(rp.filmversion) IN ('VERSION_ORIGINAL', 'VERSION_ORIGINAL_LOCAL') THEN 'VO'
        WHEN TRIM(rp.filmversion) = 'VERSION_LOCAL' THEN 'VF'
        ELSE TRIM(rp.filmversion)
    END AS version_audio,
    CAST(CASE
            WHEN rp.filmaudio = 'ST' THEN TRUE
            ELSE FALSE
        END AS BOOLEAN) AS sous_titres,
   	rp.filmtrailer as bande_annonce,
   	rp.filmposter as affiche,
   	rp.showid,
   	rp.filmid,
   	rp.showurl as reservation,
   	rp.cineid,
   	TRIM(INITCAP(rp.cinenom )) AS nom_cinema,
   	TRIM(INITCAP(rp.cineadresse)) as adresse,
   	(rp.cinecp / 1000) AS departement,
   	TRIM(INITCAP(rp.cineville)) as ville,
   	rp.description,
   	rp.auditoriumcapacity as nbr_place
from raw_prog rp
WHERE filmtitle IS NOT NULL AND filmtitle != ''; --sert à éliminer tous les titres des films dont la valeur est NULL

	
	
-- jeux de données sur le RSA	

CREATE TABLE if not exists tmp_rsa AS (
select
	-- les données ont ete interpretées comme text mais ce sont des dates au format aaaa-mm, j'ai rajouté un jour unique pour qu'elles soient interpretées correctement, cela n'aura pas d'insidance 
	CAST(rsa."﻿Date référence" || '-01' AS DATE) AS date_ref, -- comme dans etab on a des problemes de cractere invisible
	TRIM(rsa."Numéro commune") AS num_commune,
	TRIM(rsa."Type RSA")  AS type_rsa,
	TRIM(INITCAP(rsa."Nom commune")) as commune,
	rsa."Nombre foyers RSA" as nbr_foyer_rsa,
	rsa."Nombre personnes RSA" as nbr_pers_rsa
from raw_rsa rsa);





-- jeux de données wikidata, informations sur les films

CREATE TABLE if not exists tmp_wiki1 AS (
SELECT 
    rw.film AS film_entity,
    TRIM(INITCAP("filmLabel")) AS titre,
	INITCAP(TRIM(NULLIF(REGEXP_REPLACE(rw."realisateurLabel", '^Q[0-9]+$', ''), ''))) AS realisateur,
    CASE 
    WHEN LENGTH(REGEXP_REPLACE(CAST(rw.duree AS TEXT), '[^0-9]', '', 'g')) <= 9
    THEN CAST(NULLIF(REGEXP_REPLACE(CAST(rw.duree AS TEXT), '[^0-9]', '', 'g'), '') AS INTEGER)
    ELSE NULL -- Permet de résoudre un problème de donnée trop longue en integer
	END AS duree,
    INITCAP(TRIM(NULLIF(REGEXP_REPLACE(rw."genreLabel", '^Q[0-9]+$', ''), ''))) AS genre,
    EXTRACT(YEAR FROM (NULLIF(rw."dateLabel", '')::TIMESTAMP))::INTEGER AS annee_sortie,
    -- j'ai eu beauuuucoup de mal à faire fonctionner ca, uniformiser les formats de notation
    -- emploi du raccourcis :: car je n'arrivais pas a faire compiler tout cela avec la fonction cast
    (case
	        -- pour les notes en %, enlever le %
            WHEN rw."note" ~ '^[0-9]+(\.[0-9]+)?%$' THEN
                REPLACE(rw."note", '%', '')::numeric
            -- pour les notes /100, split avant le /
            WHEN rw."note" ~ '^[0-9]+(\.[0-9]+)?/100$' THEN
                SPLIT_PART(rw."note", '/', 1)::numeric
            -- pour les notes /10, split puis mettre sur 100
            WHEN rw."note" ~ '^[0-9]+(\.[0-9]+)?/10$' THEN
                SPLIT_PART(rw."note", '/', 1)::NUMERIC * 10
            -- pour les notes sans / 
            WHEN rw."note" ~ '^[0-9]+(\.[0-9]+)?$'
                 AND rw."note"::NUMERIC <= 10 THEN
                rw."note"::NUMERIC * 10
            -- et les autres, convertir en num
            WHEN rw."note" ~ '^[0-9]+(\.[0-9]+)?$' THEN
                rw."note"::NUMERIC

            ELSE null
END
    )::INTEGER AS note_sur_100
FROM raw_wikidata1 rw
WHERE "filmLabel" !~ 'Q[^a-z]' 
  	AND "filmLabel" IS NOT NULL --Ce "WHERE" sert à n'inclure que les titres des films dont la valeur n'est pas "NULL"
  	AND "filmLabel" != '');




-- le script est doublé par ce que le csv a du etre scindé en deux car trop lourd
CREATE TABLE if not exists tmp_wiki2 AS (
SELECT 
    rd.film AS film_entity,
    TRIM(INITCAP("filmLabel")) AS titre,
    INITCAP(TRIM(NULLIF(REGEXP_REPLACE(rd."realisateurLabel", '^Q[0-9]+$', ''), ''))) AS realisateur,
    CAST(NULLIF(REGEXP_REPLACE(CAST(rd.duree AS TEXT), '[^0-9]', '', 'g'), '') AS BIGINT) AS duree,
    INITCAP(TRIM(NULLIF(REGEXP_REPLACE(rd."genreLabel", '^Q[0-9]+$', ''), ''))) AS genre,
    EXTRACT(YEAR FROM (NULLIF(rd."dateLabel", '')::TIMESTAMP))::INTEGER AS annee_sortie,
    (case
	        -- pour les notes en %, enlever le %
            WHEN rd."note" ~ '^[0-9]+(\.[0-9]+)?%$' THEN
                REPLACE(rd."note", '%', '')::numeric
            -- pour les notes /100, split avant le /
            WHEN rd."note" ~ '^[0-9]+(\.[0-9]+)?/100$' THEN
                SPLIT_PART(rd."note", '/', 1)::numeric
            -- pour les notes /10, split puis mettre sur 100
            WHEN rd."note" ~ '^[0-9]+(\.[0-9]+)?/10$' THEN
                SPLIT_PART(rd."note", '/', 1)::NUMERIC * 10
            -- pour les notes sans / 
            WHEN rd."note" ~ '^[0-9]+(\.[0-9]+)?$'
                 AND rd."note"::NUMERIC <= 10 THEN
                rd."note"::NUMERIC * 10
            -- et les autres, convertir en num
            WHEN rd."note" ~ '^[0-9]+(\.[0-9]+)?$' THEN
                rd."note"::NUMERIC

            ELSE null
END
    )::INTEGER AS note_sur_100
FROM raw_wikidata2 rd
WHERE "filmLabel" !~ 'Q[^a-z]' 
  	AND "filmLabel" IS NOT NULL --Ce "WHERE" sert à n'inclure que les titres des films dont la valeur n'est pas "NULL"
  	AND "filmLabel" != ''); 

DROP TABLE IF EXISTS tmp_titre; -- DROP TABLE permet de détruire la table pour être sûr de ne pas recréer ensuite des colonnes qui existent déjà 
--crée une table temporaire pour les titres de film. permet d'éviter des doublons pour des films qui ont plusieurs réalisateurs, genres, etc.
CREATE TABLE if not exists tmp_titre AS (
    -- Premier bloc : Wikidata 1
    SELECT TRIM(INITCAP("filmLabel")) AS titre
    FROM raw_wikidata1
    WHERE "filmLabel" !~ 'Q[^a-z]'

    UNION -- Fusionne et supprime les doublons automatiquement

    -- Deuxième bloc : Wikidata 2
    SELECT TRIM(INITCAP("filmLabel"))
    FROM raw_wikidata2
    WHERE "filmLabel" !~ 'Q[^a-z]'

    UNION

    -- Troisième bloc : Programmation
    SELECT TRIM(INITCAP(filmtitle))
    FROM raw_prog
    WHERE filmtitle IS NOT NULL AND filmtitle != ''
);

--crée une colonne id_film dans films_realisateurs qui génère automatiquement une ID
ALTER TABLE tmp_titre 
ADD COLUMN id_film INTEGER GENERATED ALWAYS AS IDENTITY;

--transforme cette colonne en clé primaire
ALTER TABLE tmp_titre 
ADD PRIMARY KEY (id_film); 

COMMIT ;