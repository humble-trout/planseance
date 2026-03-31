import dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import sqlparse
import csv
import pandas as pd
import sys
import logging

def setup_logger(name : str, level=logging.DEBUG) -> logging.Logger:
    formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
        
class Logger:
    def __init__(self, name : str, level=logging.DEBUG):
        self.logger = setup_logger(name, level)

    def info(self, message : str):
        self.logger.info(message)
    
    def warn(self, message : str):
        self.logger.warning(message)

    def request(self, requete : str):
        self.info("Requête SQL à exécuter : " + requete)
    
    def error(self, message : str):
        self.logger.error(message)
   
def load_env(filename: str):
    logger = Logger("Chargement des variables")
    logger.info("Début")
    try:
        dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename))
    except Exception as e:
        logger.error(str(e))
    logger.info("Success")

class PostgresManager:
    def __init__(self, name: str, database: str):
        self.logger = Logger(f"Postgres-{name}")
        self.database = database
        self.engine = self._create_engine(database)

    def _create_engine(self, database : str):
        try:
            engine = create_engine("postgresql://{user}:{password}@{host}:{port}/{database}".format(
                    user = os.environ.get("pgUser"), 
                    password = os.environ.get("pgPassword"),
                    host = os.environ.get("pgHost"),
                    port = os.environ.get("pgPort"),
                    database = database
                )
            )
            self.logger.info("Engine créé")
            return engine
        except Exception as e:
            self.logger.error("La création de l'engine a échoué : " + str(e))

    def get_engine(self):
        if self.engine is not None:
            return self.engine
        else:
            self.logger.error("L'engine Postgres n'existe pas")
            return None

    def ensure_database_exists(self, newDatabase : str):
        engine = self.get_engine()
        if not engine:
            self.logger.warn("Aucun engine trouvé, abandon")
            exit()

        with engine.connect() as connection:
            connection = connection.execution_options(isolation_level="AUTOCOMMIT")
            self.logger.info(f"Vérification de l'existence de la base {newDatabase}")

            result = connection.execute(
                text("SELECT count(*) FROM pg_database WHERE datname = :database"),
                {"database": newDatabase}
            )

            if result.scalar() == 0:
                self.logger.info(f"La base {newDatabase} n'existe pas, création en cours")
                requete = f"CREATE DATABASE {newDatabase}"
                self.logger.request(requete)
                connection.execute(text(requete))
                self.logger.info(f"Base {newDatabase} créée avec succès.")
            else:
                self.logger.info(f"La base {newDatabase} existe déjà.")

    def forget_me(self):
        self.engine = None

class DataLoader:
    def __init__(self, engine : PostgresManager):
        self.engine = engine

    def load_sql_files(self, sql_dir: str):
        logger = Logger("SQLDataLoader")
        sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), sql_dir)
        sql_files = sorted(os.listdir(sql_path))

        with self.engine.connect() as connection:
            for sql_file in sql_files:
                logger.info("\n")
                file_path = os.path.join(sql_path, sql_file)
                logger.info(f"Exécution du fichier SQL : {sql_file}")
                with open(file_path, "r") as f:
                    contenu = f.read()
                    for instruction in sqlparse.split(contenu):
                        logger.request(instruction)
                        try:
                            connection.execute(text(instruction))
                            logger.info("Success : Requête exécutée correctement")
                        except Exception as e:
                            if(eval(os.environ.get("failOnFirstSqlError"))):
                               logger.error("Error : " + str(e))
                               exit()
                            else:
                                logger.warn("Error : " + str(e))

    def load_csv_files(self, csv_dir: str):
        logger = Logger("CSVDataLoader")
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_dir)
        csv_files = sorted(os.listdir(csv_path)) # Ajout de sorted pour l'ordre constant

        with self.engine.connect() as connection:
            for csv_file in csv_files:
                if not csv_file.endswith(".csv"): continue # Sécurité
                
                logger.info("\n")
                file_path = os.path.join(csv_path, csv_file)
                logger.info(f"Import du fichier CSV : {csv_file}")

                try:
                    # --- CHANGEMENT MAJEUR ICI ---
                    # On utilise sep=None et engine='python' pour l'auto-détection
                    # On passe file_path directement au lieu de 'f' pour laisser Pandas gérer l'ouverture
                    df = pd.read_csv(
                        file_path,
                        sep=None,            # Pandas va tester , ; \t tout seul
                        engine='python',     # Obligatoire pour utiliser sep=None
                        on_bad_lines='warn', # Va afficher l'erreur de la ligne 87 sans crasher tout le script
                        encoding='utf-8'     # Change en 'latin-1' si tu as des problèmes d'accents
                    )
                    
                    logger.info(f"Structure détectée : {len(df.columns)} colonnes, {len(df)} lignes.")

                    # Nettoyage des noms de colonnes (enlève les espaces et met en minuscule pour SQL)
                    #df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

                    table_name = csv_file.replace(".csv", "")
                    schema_name = os.environ.get("pgSchemaImportsCsv", "public") # Valeur par défaut 'public' si env vide

                    logger.info(f"Transfert vers {schema_name}.{table_name}...")
                    
                    df.to_sql(
                        table_name,
                        schema=schema_name,
                        con=connection,
                        if_exists="replace",
                        index=False
                    )
                    connection.commit() # Important si l'isolation level n'est pas autocommit
                    logger.info(f"Success : {csv_file} importé.")

                except Exception as e:
                    # connection.rollback() # Pas toujours nécessaire avec Pandas mais prudent
                    if os.environ.get("failOnFirstCsvError") == "True":
                        logger.error(f"FATAL Error sur {csv_file} : {e}")
                        exit()
                    else:
                        logger.warn(f"SKIP Error sur {csv_file} : {e}")
if __name__ == "__main__":
    load_env(".env")

    global_postgres = PostgresManager("global", "postgres")
    global_postgres.ensure_database_exists(os.environ.get("pgDatabase"))
    global_postgres.forget_me()

    processingPostgres = PostgresManager("workingInstance", os.environ.get("pgDatabase"))

    if os.environ.get("pgDatabase"):
        processingPostgres.ensure_database_exists(os.environ.get("pgDatabase"))
        engine = processingPostgres.get_engine()

        if engine:
            loader = DataLoader(engine)
            loader.load_csv_files("csv")
            loader.load_sql_files("sql")
    else:
        Logger("Main").error("Variable pgDatabase manquante dans .env")
        exit()
