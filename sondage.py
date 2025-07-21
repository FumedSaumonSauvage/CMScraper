from composition_ecran import id_cooker
import data_helper

# Objet sondage pour l'export vers un JSON: est associé à un objet composant, mais n'est pas défini par lui.
# On définit ici des objets modèle (model) pour rendre la structure de données un peu plus robuste.



class StringVersion:
    # Classe représentant différentes versions d'une même chaine de caractères
    # Utilisée pour la correction OCR, pour stocker les différentes versions d'une chaîne de caractères et choisir la plus plausible
    def __init__(self):
        self.versions = []

    def add_version(self, string):
        self.versions.append(string)

    def get_all_versions(self):
        return self.versions

    def get_most_plausible(self):
        if len(self.versions) == 1:
            return self.versions[0]
        else:
            # Normalisation des versions
            normalized_versions = [version.strip().lower() for version in self.versions]
            # Calcul de la longueur moyenne des versions
            longueur_moyenne = round(sum(len(version.split()) for version in normalized_versions) / len(normalized_versions))
            mots = []
            for i_mot in range(longueur_moyenne):
                mots_at_i = []
                for version in normalized_versions:
                    mots_version = version.split()
                    if i_mot < len(mots_version):
                        mots_at_i.append(mots_version[i_mot])

                # Comptage des occurrences des mots
                word_bins = {}
                for mot in mots_at_i:
                    if mot in word_bins:
                        word_bins[mot] += 1
                    else:
                        word_bins[mot] = 1

                # Sélection du mot le plus fréquent
                if word_bins:
                    mots.append(max(word_bins, key=word_bins.get))

            # Reconstruction de la chaîne
            string_finale = " ".join(mots)
            return string_finale
        
    def to_dict(self):
        return {
            "versions": self.versions,
            "most_plausible": self.get_most_plausible()
        }

    


class sondage_m:
    def __init__(self):
        self.id = id_cooker.get_instance().get_new_id()
        self.description = StringVersion()  # Utilisation de StringVersion pour stocker les descriptions
        self.auteur = StringVersion()  # Utilisation de StringVersion pour stocker l'auteur
        self.date_creation = None
        self.ouvert= None
        self.choix_unique = None
        self.options = [] # Tableau d'options

    def ajouter_option(self, option):
        # Ajoute l'option en vérifiant si on l'a déjà. Si oui, pas la peine de l'ajouter.
        match_found = False
        for i, option_ex in enumerate(self.options):
            if data_helper.correlation_txt(option_ex.get_description(), option.get_description(), 0.2): # Si une option similaire est trouvée
                self.options[i].ajouter_description(option.get_description()) # Alors on màj
                match_found = True
                break
        if not match_found:
            self.options.append(option)

    def ajouter_description(self, description):
        self.description.add_version(description)

    def ajouter_auteur(self, auteur):
        self.auteur.add_version(auteur)
        
    def get_description(self):
        if not self.description.versions:
            return None
        return self.description.get_most_plausible()
    
    def get_auteur(self):
        return self.auteur.get_most_plausible()

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.get_description(),
            "auteur": self.get_auteur(),
            "date_creation": self.date_creation,
            "ouvert": self.ouvert,
            "choix_unique": self.choix_unique,
            "options": [option.to_dict() for option in self.options]
        }
    
    def to_dict_smpl(self):
        return {
            "description": self.get_description(),
            "auteur": self.get_auteur(),
            "options": [option.to_dict() for option in self.options]
        }

class option_m:
    def __init__(self):
        self.id = None
        self.description = StringVersion()
        self.taux = None
        self.sondage_id = None

    def get_description(self):
        return self.description.get_most_plausible()
    
    def ajouter_description(self, description):
        self.description.add_version(description)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.get_description(),
            "taux": self.taux,
            "sondage_id": self.sondage_id
        }
    
    def to_dict_smpl(self):
        return {
            "description": self.get_description(),
            "taux": self.taux
        }
    

