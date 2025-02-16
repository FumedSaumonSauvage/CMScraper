from composition_ecran import id_cooker

# Objet sondage pour l'export vers un JSON: est associé à un objet composant, mais n'est pas défini par lui.
# On définit ici des objets modèle (model) pour rendre la structure de données un peu plus robuste.

class sondage_m:
    def __init__(self):
        self.id = id_cooker.get_instance().get_new_id()
        self.description = None
        self.auteur = None
        self.date_creation = None
        self.ouvert= None
        self.choix_unique = None
        self.options = []

    def ajouter_option(self, option):
        self.options.append(option)

class option_m:
    def __init__(self):
        self.id = None
        self.description = None
        self.nb_votes = None
        self.sondage_id = None
    

