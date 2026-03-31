# planseance
Code de l'application Plan Séance, réalisée dans le cadre du M2 TNAH de l'Ecole Nationale des Chartes en 2025-2026.

Important: entrer à la ligne 9 de app/_ _init _ _.py ses informations de connection Postgres, dans l'URI. Le faire aussi dans .env.

D'après le modèle Dating App de Shaktiranjan.

# Objectif : 

planseance est une application de type "rencontre" centrée sur les pratiques cinématographiques. 

# Lancement de l'application 

Avant de lancer l'application, il est nécessaire de faire tourner le script SQL permettant de créer notre base de données "planseance", et contenu dans le dossier /Script BDD. 

IMPORTANT : Avant de faire tourner ce script, il est nécessaire de créer la base de données et le schéma par des requêtes "CREATE DATABASE" et "CREATE SCHEMA". Le nom donné à la BDD doit être "planseance" et celui du schéma doit être "psch". 

# Utilisation 

Pour utiliser l'application, il est nécessaire de créer un compte grâce à la fonction "register", et de se connecter avec la fonction "login". 

L'utilisateur a accès à des informations sur la programmation des cinémas. Il dispose d'un profil personnalisé, notamment composé d'un calendrier des 
séances auxquelles il a prévu d'assister, ou d'une liste des films vus récemment. 

La fonction "matching", centrale dans l'application, permet d'organiser une rencontre entre deux utilisateurs sur la base d'une séance commune de cinéma. 

Pour tester cette fonctionnalité, vous aurez besoin de créer deux comptes différents et d'inscrire les deux comptes à la même séance. Un match vous sera alors proposé et vous aurez la possibilité de l'accepter ou non. 




