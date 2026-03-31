# planseance
Code de l'application Plan Séance, réalisée dans le cadre du M2 TNAH de l'Ecole Nationale des Chartes en 2025-2026.

Important: entrer à la ligne 9 de app/_ _init _ _.py ses informations de connection Postgres, dans l'URI. Le faire aussi dans .env.

D'après le modèle Dating App de Shaktiranjan.

# Objectif : 

planseance est une application de type "rencontre" centrée sur les pratiques cinématographiques. 

# Lancement de l'application 

Avant de lancer l'application, il est nécessaire de faire tourner le script SQL permettant de créer notre base de données "planseance", et contenu dans le dossier /Script BDD. 

IMPORTANT : Avant de faire tourner ce script, il est nécessaire de créer la base de données et le schéma par des requêtes "CREATE DATABASE" et "CREATE SCHEMA". Le nom donné à la BDD doit être "planseance" et celui du schéma doit être "psch". 

# Fonctionnalités 

L'application compte plusieurs fonctionnalités : 

- Gestion de compte : Inscription et création d'un profil incluant nom, préférences
cinématographiques et mot de passe sécurisé.

- Recherche : Moteur de recherche plein texte pour identifier rapidement un film ou un cinéma
indépendant.

- Filtres avancés : permettent une recherche affinée des films, par genre ou par date de sortie.

- Cartographie : Carte interactive pour localiser les cinémas et consulter la programmation par
emplacement. L’utilisateurice a accès à une carte de la France, depuis laquelle iel peut sélectionner
sa ville et voir les cinémas indépendants. La carte affiche également la position que l’utilisateurice a
déclarée.

- Matching de séance : Proposition de mise en relation entre utilisateurices ayant sélectionné la
même séance. Une page « Match » s’affiche après que l’utilisateurice ait sélectionné une séance.

- Calendrier personnel : Agenda regroupant l'ensemble des séances auxquelles l'utilisateurice a
prévu d'assister.


# Notes d'utilisation 

La fonction "matching", centrale dans l'application, permet d'organiser une rencontre entre deux utilisateurs. Pour tester cette fonctionnalité, vous aurez donc besoin de créer deux comptes différents et d'inscrire les deux comptes à la même séance. Un match vous sera alors proposé et vous aurez la possibilité de l'accepter ou non. 




