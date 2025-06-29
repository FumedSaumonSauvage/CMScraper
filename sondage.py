from composition_ecran import id_cooker

# Objet sondage pour l'export vers un JSON: est associé à un objet composant, mais n'est pas défini par lui.
# On définit ici des objets modèle (model) pour rendre la structure de données un peu plus robuste.

class sondage_m:
    def __init__(self):
        self.id = id_cooker.get_instance().get_new_id()
        self.description = [] # Plusieurs possibilités de descriptions pour trouver la plus probable avec pytesseract
        self.auteur = None
        self.date_creation = None
        self.ouvert= None
        self.choix_unique = None
        self.options = []

    def ajouter_option(self, option):
        self.options.append(option)

    def ajouter_description(self, description):
        self.description.append(description)

    def find_most_plausible_description(self):
        if not self.description:
            return None
        elif len(self.description) == 1:
            return self.description[0]
        else:
            print("Pas encore implémenté de correction OCR")
            return self.description[0]

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "auteur": self.auteur,
            "date_creation": self.date_creation,
            "ouvert": self.ouvert,
            "choix_unique": self.choix_unique,
            "options": [option.to_dict() for option in self.options]
        }
    
    def to_dict_smpl(self):
        return {
            "description": self.description,
            "auteur": self.auteur,
            "options": [option.to_dict() for option in self.options]
        }

class option_m:
    def __init__(self):
        self.id = None
        self.description = None
        self.taux = None
        self.sondage_id = None

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "taux": self.taux,
            "sondage_id": self.sondage_id
        }
    
    def to_dict_smpl(self):
        return {
            "description": self.description,
            "taux": self.taux
        }
    

