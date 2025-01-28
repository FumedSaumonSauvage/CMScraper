class composition_ecran:
    """ Classe permettant de gérer et d'organiser les éléments graphiques détectés sur l'écran.
    Chaque composition d'écran correspond à une frame et comporte plusieurs composants (voir définition des composants au dessous)
    Cette classe permet de vérifier l'intégrité de la composition d'écran détectée, aisi que de construire un score global de confiance.
    """

    def __init__(self, frame):
        self.frame = frame
        self.composants = []
        self.score = 0
        self.id = id_cooker.get_instance().get_new_id()

    def ajouter_composant(self, composant):
        self.composants.append(composant)

    def verifier_integrite(self):
        # Vérifie l'intégrité de la composition d'écran
        for composant in self.composants:
            composant.verifier_integrite()

    def get_all_composants(self):
        return self.composants
    
    def ordonner(self):
        # Pour tous les composants dans la composition, on regarde ceux qui sont imbriqués les uns dans les autres pour définir des fils et des pères.
        for composant in self.composants:
            for autre_composant in self.composants:
                if composant.est_contenu_dans(autre_composant.position):
                    composant.donner_parent(autre_composant)
                    autre_composant.ajouter_fils(composant)

    def debug_imprimer_arbre_composants(self):
        # Debug exclusivement, imprime l'arborescence des composants
        # On part de chaque composant qui n'a pas de parent, et on déroule ensuite de fils en fils
        orphelins = []
        for cpst in self.get_all_composants():
            if not cpst.a_un_parent():
                orphelins.append(cpst)
        for cpst in orphelins:
            cpst.debug_print_composant()
            



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
        self.parent = None
        self.is_init = False # dit si un composant a été initialisé ou non

    
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

    def donner_parent(self, composant):
        # initialise le parent du composant en question
        self.parent = composant

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
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Si la fonction est appellée ici, on a un problème
        AssertionError("Impossible de vérifier l'intégrité d'un composant générique")
    
    def get_init_status(self):
        # Vérifie si le composant a été initialisé
        return self.is_init
    
    def set_init_status(self, status):
        # Met à jour le statut d'initialisation du composant
        self.is_init = status

    def a_un_parent(self):
        return not self.parent is None
    
    def debug_print_composant(self, indent = 0):
        # Imprime le composant et ses fils
        print(f"{' '*indent}{self.__class__.__name__} (id {self.id})")
        if len(self.fils) > 0:
            new_indent = indent + 2
            for child in self.fils:
                child.debug_print_composant(new_indent)

    



class bouton_voir_tout(composant):

    def __init__(self, position):
        super().__init__(position)

    def is_bouton_voir_tout(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Pas de fils, et un sondage comme parent
        return (len(self.fils) == 0) and self.parent.is_sondage()
    

class bouton_fermer_reponse(composant):

    def __init__(self, position):
        super().__init__(position)

    def is_bouton_fermer_reponse(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Pas de fils, et un père reponse_dev
        return (len(self.fils) == 0) and self.parent.is_reponse_dev()


class option_reponse(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_option_reponse(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Un fils bouton pour voir les réponses, et un parent sondage
        return (len(self.fils) == 1) and self.parent.is_sondage() and self.fils[0].is_is_voir_reponses_option()
        
class personne_sondee(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_personne_sondee(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Pas de fils, et un parent reponse dev
        return (len(self.fils) == 0) and self.parent.is_reponse_dev()
        
class reponse_dev(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_reponse_dev(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Au moins un fils (bouton_fermer_reponse), et pas de parent (package différent, voir doc)
        bfr = False
        for fils in self.fils:
            if fils.is_bouton_fermer_reponse():
                bfr = True
        return (len(self.fils) >= 1) and bfr
        
class sondage(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_sondage(self):
        return True
    
    def donner_parent(self, composant):
        # Pas de parent pour un sondage
        AssertionError("Un sondage ne peut contenir de parent.")

    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Au moins un auteur et une option en tant que fils, mais pas de parent
        auteur = False
        option = False
        for fils in self.fils:
            if fils.is_auteur_sondage():
                auteur = True
            if fils.is_option_reponse():
                option = True
        
        return (len(self.fils) >= 2) and auteur and option
        
        
class voir_reponses_option(composant):
        
    def __init__(self, position):
        super().__init__(position)
    
    def is_voir_reponses_option(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Un parent option_reponse et pas de fils (voir doc, reponse_dev dans un autre package)
        return (len(self.fils) == 0) and self.parent.is_option_reponse()
    

class auteur_sondage(composant):
    
    def __init__(self, position):
        super().__init__(position)

    def is_auteur_sondage(self):
        return True
    
    def verifier_integrite(self):
        # Vérifie si le composant est intègre et a bien été initialisé
        # Pas de fils, et un parent sondage
        return (len(self.fils) == 0) and self.parent.is_sondage()
            


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
