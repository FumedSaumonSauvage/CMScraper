# Classe utilisée pour stocker les gens qui ont été rencontrés, et éviter les erreurs dues à l'OCR.

import sqlite3
import os
import dotenv

class database_helper:
    """On implémente le DP Singleton"""

    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(database_helper, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init_db(self):
        # On initialise la base de données
        dotenv.load_dotenv()
        self._db = sqlite3.connect(os.getenv("DATABASE_PATH"))
        cursor = self._db.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS personnes (id INTEGER PRIMARY KEY, nom TEXT)")
        self._db.commit()

    def ajouter_personne(self, nom):
        # On ajoute une personne à la base de données
        cursor = self._db.cursor()
        cursor.execute("INSERT INTO personnes (nom) VALUES (?)", (nom,))
        self._db.commit()

    def verifier_existence_personne(self, nom):
        # On vérifie si une personne est déjà dans la base de données
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM personnes WHERE nom = ?", (nom,))
        return cursor.fetchone() is not None
    
    def correlation(self, nom1, nom2):
        # Fournit une métrique de corrélation entre deux noms (entre 0 et 1)
        # Si les deux ont le même nombre de caractères, on compare
        if len(nom1) == len(nom2):
            nb_similaires = 0
            for i in range(len(nom1)):
                if nom1[i] == nom2[i]:
                    nb_similaires += 1
            return nb_similaires / len(nom1)
        
        # Si les deux n'ont pas le même nombre de caractères, on compare le plus court avec le plus long
        # On regarde comment est ce qu'on peut faire entrer le plus court dans le plus long, en coupant à chaque fois (on SQ on a que une lettre d'erreur)
        if len(nom1) < len(nom2):
            nom_court = nom1
            nom_long = nom2
        else:
            nom_court = nom2
            nom_long = nom1

        max_correlation = 0
        for i in range(len(nom_long) - len(nom_court) + 1):
            correlation = 0
            for j in range(len(nom_court)):
                if nom_court[j] == nom_long[i + j]:
                    correlation += 1
            correlation /= len(nom_court)
            if correlation > max_correlation:
                max_correlation = correlation
        return max_correlation
    

    def correction_nom_personne(self, nom, seuil = 0.8):
        # On essaie de voir si à une lettre près la personne existe, ca éviterait de mettre des personnes qui n'ont aucun sens dans la DB
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM personnes")
        personnes = cursor.fetchall()
        for personne in personnes:
            if self.correlation(nom, personne[1]) > seuil:
                return personne[1]
        return ""



    