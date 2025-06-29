# Classe singleton qui gère l'écriture et la lecture des données vers un JSON.
# Étendu en classe d'outils pour traiter les données

import json

class data_helper:

    _instance = None
    _file = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(data_helper, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def init_file(self, file):
        file = open(file, "w")
    
    def write_data(self, data):
        self._file.write(json.dumps(data))

    def read_data(self):
        return json.loads(self._file.read())
    
    def close_file(self):
        self._file.close()

    def find_most_plausible_string(self, strings):
        # Trouve la chaîne de caractères la plus plausible parmi une liste de chaînes. Utilisé pour la correction de l'OCR.
        if not strings:
            return None
        elif len(strings) == 1:
            return strings[0]
        else:
            # Implémenter une médiane de condorcet pour une correction "par mot" en situant les mots dans une phrase.
            print("Pas encore implémenté de correction OCR")
            return strings[0]
        
    
