# Bienvenue dans Plan Séance !
Ce dépôt GitHub contient le code complet de l'application Plan Séance, réalisée dans le cadre du M2 TNAH de l'Ecole Nationale des Chartes en 2025-2026. Il est composé de deux dossiers : Script BDD, qui permet de créer la base de données nécessaire au fonctionnement de l'application, et Code de l'appli, qui contient l'application elle-même.

L'application Plan Séance a été réalisée en utilisant Dating App de Shaktiranjan (https://github.com/Shakti077/DatingApp) comme un modèle. Nous avons restructuré ce modèle selon ce que nous avions vu en cours de Flask, et avons utilisé certaines des routes de Shaktiranjan comme base pour la création des nôtres (notamment en ce qui concerne la gestion de compte et le matching).

Nous avons eu recours à des LLM pour aider à expliquer certaines des erreurs que nous rencontrions et à régler certains problèmes de notre code que nous ne parvenions pas à résoudre par nous-mêmes. L'utilisation de LLMs est signalée dans les commentaires du code.

**Important :** afin de connecter la base de données à l'application, il faut entrer ses informations de connection Postgres dans les fichiers .env contenus dans les dossiers Script BDD et Code de l'appli. Pour ce dernier, il faut aussi les renseigner à la ligne 9 du fichier app/_ _init _ _.py.

## Présentation et objectifs de l'application

Plan Séance est une application de type « rencontre » centrée sur la fréquentation des cinémas indépendants. Elle permet de découvrir des films et des cinémas, d'obtenir un calendrier personnalisé avec les séances auquel l'on prévoit d'assister, et de « matcher » avec d'autres utilisateurices inscrit-es aux mêmes séances. L'utilisateurice peut personnaliser son profil en y ajoutant une biographie et une photo de profil, et il peut également y visionner son cinéma « favori », celui qu'il fréquente le plus. L'application intègre des outils de datavizualisation : le calendrier, une carte interactive des cinémas indépendants de France, et la page « Cinématch » qui affiche les matchs confirmés, possibles et en attente.

A travers ce projet, notre objectif était d'apprendre à maîtriser Flask, afin d'utiliser cet outil pour construire notamment le moteur de recherche, la gestion de compte et le système de « matching ». La création du front-end et notamment la réalisation de la carte interactive nous ont permis de mobiliser et d'affiner nos compétences en HTML, CSS et Javascript. Nous avons aussi amélioré nos compétences en SQL à travers les nombreuses modifications qui ont dû être faites au script de traitement de données pour permettre le bon fonctionnement de la gestion de compte et du matching.

## Lancement de l'application 

Avant de lancer l'application, il est nécessaire de créer la base de données en local, à l'aide du script contenu dans le dossier Script BDD de ce dépôt.

**IMPORTANT :** Pour que le script fonctionne, il est nécessaire de créer manuellement le schéma "psch". Pour ce faire, il faut accéder au Shell de Postgres depuis le terminal, créer la base de données "planseance", se connecter à cette dernière, et créer le schéma "psch" -alternativement, si vous avez déjà lancé le script une première fois, la base a déjà été créée et il vous suffira de vous y connecter et de créer le schéma. Cette contrainte est dûe à une erreur fatale que nous avons rencontrée à répétition lorsque nous incluions la création du schéma directement dans le script, qui nous a forcé-es à retirer cette requête.

## Fonctionnalités 

Plan Séance propose plusieurs fonctionnalités à ses utilisateurices. Sans être connecté-es, iels ont accès à :

- Découverte de films : La page d'accueil de l'application montre les films à l'affiche. Sélectionner le film de son choix permet de voir des informations supplémentaires sur lui sur une page « Film », dont les cinémas où il est diffusé.

- Recherche : Moteur de recherche plein texte permettant de trouver un film ou un cinéma indépendant avec son nom.

- Filtres avancés : Options de filtrage permettant une recherche affinée des films, par genre et année de sortie.

- Cartographie, ou Cinémap : Carte interactive de la France affichant la position des cinémas indépendants. Si l'on clique sur une épingle, un pop-up s'affiche avec des informations sur le cinéma, et il est possible d'obtenir plus de renseignements dont la programmation en navigant de ce pop-up à la page « Cinéma »


Les fonctions suivantes sont proposées aux utilisateur-ices connecté-es :

- Gestion de compte : Inscription et création d'un profil avec mot de passe sécurisé. L'utilisateurice peut choisir une photo de profil et écrire une courte biographie. Sur son profil, il peut découvrir son cinéma « favori », c'est-à-dire celui qu'il fréquente le plus.

- Calendrier personnalisé : L'utilisateurice peut ajouter des séances de cinéma à son calendrier depuis les pages « Film » ou « Cinéma », et les visionner dans un calendrier mensuel.

- Matching de séance, ou Cinématch : Proposition de mise en relation entre utilisateurices ayant sélectionné la même séance. Si un-e autre utilisateurice est déjà inscrit pour la séance sélectionnée, un pop-up s'affiche invitant à consulter la page Cinématch. Depuis cette dernière, l'utilisateur peut envoyer des likes, confirmer des matchs, refuser des matchs, et voir la liste de ses matchs en attente et confirmés. 

## Note d'utilisation 

Afin de tester la fonctionnalité de matching, il sera nécessaire de créer deux comptes et de les inscrire à la même séance de cinéma.
