# Classe qui permet de stocker les composition_ecran, puis d'identifier deux instances du même composant pour éviter de le compter deux fois

class univers:

    def __init__(self):
        self.compositions_ecran = []
        
    def ajouter_composition_ecran(self, compo):
        self.compositions_ecran.append(compo)

