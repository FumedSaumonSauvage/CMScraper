class composition_ecran:
    """ Classe permettant de gérer et d'organiser les éléments graphiques détectés sur l'écran.
    Chaque composition d'écran correspond à une frame et comporte plusieurs composants (voir définition des composants au dessous)
    Cette classe permet de vérifier l'intégrité de la composition d'écran détectée, aisi que de construire un score global de confiance.
    """

    def __init__(self, frame):
        self.frame = frame
        self.composants = []
        self.score = 0

    def ajouter_composant(self, composant):
        self.composants.append(composant)


class composant:
    """ Classe générique sur la base de laquelle on construira les composants de la composition d'écran."""

    def __init__(self, position):
        """ Arguments:
        id: int - Component identifier, built by component factory.
        classe: str - Component class TODO voir si ca sert
        position: (xcenter, ycenter, width, height) - Component position in the frame."""
        self.id = id_cooker.get_instance().get_new_id()
        self.position = position
        self.fils = []

    def is_bouton_voir_tout(self):
        return False
    
    def is_bouton_fermer_reponse(self):
        return False
    
    def is_option_reponse(self):
        return False
    
    def is_personne_sondee(self):    
        return False
    
    def is_reponse_dev(self):
        return False
    
    def is_sondage(self):
        return False
    
    def is_voir_reponses_option(self):
        return False
    
    def is_auteur_sondage(self):
        return False
    
    def ajouter_fils(self, fils):
        self.fils.append(fils)

    def est_contenu_dans(self, x, y, w, h):
        # Renvoie La proportion du composant qui est contenue si le composant en question est contenu dans la bbox passéen en arguments
        # En gros c'est une iou

        x1, y1, w1, h1 = self.position
        x2, y2, w2, h2 = x,y,w,h

        # Calcul des coordonnées des bords des boîtes
        x1_max = x1 + w1
        y1_max = y1 + h1
        x2_max = x2 + w2
        y2_max = y2 + h2

        # Vérification de la contenance complète
        if x1 >= x2 and y1 >= y2 and x1_max <= x2_max and y1_max <= y2_max:
            return 1.0

        # Calcul de l'intersection
        x_intersection = max(0, min(x1_max, x2_max) - max(x1, x2))
        y_intersection = max(0, min(y1_max, y2_max) - max(y1, y2))

        aire_intersection = x_intersection * y_intersection
        aire_boite1 = w1 * h1

        # Calcul de la proportion
        if aire_boite1 == 0:
            return 0.0

        return aire_intersection / aire_boite1


class bouton_voir_tout(composant):

    def __init__(self, position):
        super().__init__(position)

    def is_bouton_voir_tout(self):
        return True
    

class bouton_fermer_reponse(composant):

    def __init__(self, position):
        super().__init__(position)

    def is_bouton_fermer_reponse(self):
        return True
    

class option_reponse(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_option_reponse(self):
        return True
        
class personne_sondee(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_personne_sondee(self):
        return True
        
class reponse_dev(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_reponse_dev(self):
        return True
        
class sondage(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_sondage(self):
        return True
        
class voir_reponses_option(composant):
        
    def __init__(self, position):
        super().__init__(position)
    
    def is_voir_reponses_option(self):
        return True
    

class auteur_sondage(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_auteur_sondage(self):
        return True
            


class id_cooker:
    """ Singleton to build unique ids"""

    _instance = None
    _counter = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(id_cooker, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_new_id(self):
        self._counter += 1
        return self._counter
