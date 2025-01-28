# Classe singleton qui gère l'écriture et la lecture des données vers un JSON

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
