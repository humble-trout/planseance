import os
from flask import Flask
from app.utils import db
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    #IMPORTANT: mettez vos identifiants Postgres ci-dessous
    POSTGRES_URI = 'postgresql://USERNAME:PSSWD@localhost:5432/planseance'
    
    app.config.update(
        SQLALCHEMY_DATABASE_URI=POSTGRES_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY='your-secret-key',
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static/uploads'),
        FILMS_PER_PAGE=10,
        CINE_PER_PAGE=10
    )

    from app.config import Config
    app.config.from_object(Config)

    db.init_app(app)

    #connecte le login manager à cette application et redirige l'utilisateur vers la page de login s'il n'est pas connecté
    login_manager.init_app(app)
    login_manager.login_view = 'users.login'
    login_manager.login_message = None  # Pas de message flash, redirection silencieuse

    with app.app_context():
        #il y avait des erreurs dans le terminal car Flask cherchait à utiliser sqlite. Le code suivant est la suggestion d'un LLM
        from sqlalchemy import create_engine
        engine = create_engine(POSTGRES_URI)

        #Reflète le schéma pour copier la base de données Postgres
        db.metadata.reflect(bind=engine, schema='psch', extend_existing=True)

        #Importe les modèles et blueprints
        from app.models import User 

        from .routes.users import users
        from .routes.insertions import insertions
        from .routes.generales import generales

        app.register_blueprint(users)
        app.register_blueprint(insertions, url_prefix='/api')
        app.register_blueprint(generales)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Utilisateur
        try:
            return Utilisateur.query.get(int(user_id))
        except:
            return None
        
    return app

# def create_app():
#     app = Flask(__name__)
#     # Définit des limites de taille pour les images utilisées par les utilisateurs
#     app.config['UPLOAD_FOLDER'] = 'static/uploads'
#     app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024     
    
#     from .routes.generales import generales
#     from .routes.users import users
#     from .routes.insertions import insertions

#     app.register_blueprint(generales)
#     app.register_blueprint(users)
  
#     #Suggestion d'un LLM: ajouter un préfixe aux routes API
#     app.register_blueprint(insertions, url_prefix='/api') 

#     #Suggestion d'un LLM permettant d'appeler le nom de l'application dans notre HTML avec {{ config['APP_NAME'] }}
#     app.config['APP_NAME'] = "Plan Séance"

#     return app