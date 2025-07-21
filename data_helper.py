# Classe singleton qui gère l'écriture et la lecture des données vers un JSON.
# Étendu en classe d'outils pour traiter les données

import json
from Levenshtein import distance as levenshtein_distance

def correlation_txt(texteA, texteB, seuil = 0.15):
        # Utilisation de la distance de Levenshtein pour déterminer si texteA = TexteB
        # Si distance < seuil * max(len(texteA), len(texteB)), on considère que les textes sont égaux
        if texteA is None or texteB is None:
            return False
        
        distance = levenshtein_distance(texteA, texteB)
        max_length = max(len(texteA), len(texteB))
        
        if max_length == 0:  # Eviter la division par zéro
            return True
        
        #print(f"correlation_txt(): correlation de {texteA} avec {texteB}: Same = {distance} < {seuil * max_length}")
        
        return distance < seuil * max_length

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
        
    
