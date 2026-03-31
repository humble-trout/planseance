# planseance
Code de l'application Plan Séance, réalisée dans le cadre du M2 TNAH de l'Ecole Nationale des Chartes en 2025-2026.

Important: entrer à la ligne 9 de app/_ _init _ _.py ses informations de connection Postgres, dans l'URI. Le faire aussi dans .env.

D'après le modèle Dating App de Shaktiranjan.

# Lancement de l'application 

Avant de lancer l'application, il est nécessaire de faire tourner le script SQL permettant de créer notre base de données "planseance", et contenu dans le dossier /Script BDD. 

IMPORTANT : Avant de faire tourner ce script, il est nécessaire de créer la base de données et le schéma par des requêtes "CREATE DATABASE" et "CREATE SCHEMA". Le nom donné à la BDD doit être "planseance" et celui du schéma doit être "psch". 

# Utilisation 

Pour utiliser l'application, il est nécessaire de créer un compte grâce à la fonction "register", et de se connecter avec la fonction "login". 

La fonction "matching", centrale dans l'application, permet d'organiser une rencontre entre deux utilisateurs sur la base d'une séance commune de cinéma. 

Deux options sont possibles pour tester cette fonction : 

- Il est possible de créer deux comptes différents et de s'inscrire à la même séance.

- Nous avons créé plusieurs utilisateurs qui se sont inscrits à des séances.

  => Pour matcher avec l'utilisateur Raphael, il suffit de s'inscrire pour aller voir "La Réparation", film diffusé au café des images le 28 avril 2026.
  => Pour matcher avec l'utilisateur Kev Adams, il faut s'inscrire à la séance de ..., au cinéma .... le .... .
  => L'utilisateur .... ira à la séance de ... le ... à ....
  => L'utilisateur .... ira à la séance de ... le ... à ....
  


