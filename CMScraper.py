import cv2
import numpy as np
import dotenv
from composition_ecran import composition_ecran, composant, auteur_sondage, bouton_fermer_reponse, bouton_voir_tout, option_reponse, personne_sondee, reponse_dev, sondage, voir_reponses_option
from database import database_helper_names
from ultralytics import YOLO
import os


"""
Lire l'écran
Si on voit un sondage au complet (longueur minimale):

    cliquer sur "voir tout" 

    Lire l'auteur, son texte total et ses options de réponse
    Vérifier que le sondage est cohérent:
        Il existe un auteur
        Il existe des options de réponse
        Pour chaque option de réponse:
            Il y a un bouton pour afficher les réponses
            S'il n'y en a pas, on considère la réponse invalide

    Ajouter le sondage au Json

    Pour chaque option de réponses:
        Cliquer pour voir les participants (interpoler la zone théorique et la détection)
        Tant que il y a des changements à l'écran:
            Détecter les réponses
            Mettre la souris au milieu de la boite à réponse
            Scroller
        
        Fermer la boite
    
    Scroller plus bas pour ne plus voir le sondage

Si on ne le voit pas au complet:
    Scroller vers le bas

TODO: gérer les exceptions si le sondage est long (plus d'en tête, que des réponses)
    
"""


def read_screen(debug = False):
    # Lit l"écran et renvoie une frame
    # En débug, on utilise juste une frame qui traine
    if debug:
        return cv2.imread("test_frame.png")
    
def class_id_to_name(id):
    # convertit l'id de classe en une str compréhensible.
    class_names = {
        0: "auteur_sondage",
        1: "bouton_fermer_reponse",
        2: "bouton_voir_tout",
        3: "option_reponse",
        4: "personne_sondee",
        5: "reponse_dev",
        6: "sondage",
        7: "voir_reponses_option",
    }

    return class_names[id]

    
def analyse_frames(frame):
    # Analyse la frame et renvoie un objet composition_ecran
    compo = composition_ecran(frame)
    bboxes = detecter_bboxes(frame)

    #tri des bboxes: on vire celles à <0.7 de confiance
    conf = bboxes.conf
    cls = bboxes.cls
    xywh = bboxes.xywh

    # Filter by confidence
    high_conf_indices = conf > float(os.getenv("INDICE_CONF"))
    filtered_boxes = xywh[high_conf_indices]
    filtered_conf = conf[high_conf_indices]
    filtered_cls = cls[high_conf_indices]

    for box, confidence, class_id in zip(filtered_boxes, filtered_conf, filtered_cls):
        x1, y1, x2, y2 = box
        #print(f"Box: ({x1}, {y1}, {x2}, {y2}), Confidence: {confidence:.2f}, Class: {class_id_to_name(int(class_id))}")

    zip_boxes = zip(filtered_boxes, filtered_conf, filtered_cls)
    # Construction d'un objet composition_ecran
    for box in zip_boxes:
        compo.ajouter_composant(make_component(box))
    
    compo.ordonner(threshold_incl=0.8, verbose=False) # On range les composants les uns dans les autres

    return compo

def debug_exporter_composition_as_frame(composition, taillex, tailley):
    # Pour du debug, prend tout ce qui est visible sur la composition et renvoie une frame illustrative (taille en param)
    frame = np.zeros((taillex, tailley, 3), np.uint8)
    for composant in composition.get_all_composants():
        x, y, w, h = composant.position
        x1, y1, w1, h1 = int(x-w/2), int(y-h/2), int(x+w/2), int(y+h/2)
        cv2.rectangle(frame, (x1, y1), (w1, h1), (255, 255, 255), 2)
        text_size = cv2.getTextSize(composant.__class__.__name__, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_x = x1 + 5
        text_y = y1 + text_size[1] + 5
        cv2.putText(frame, f"{composant.__class__.__name__}, id: {composant.id}", (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return frame

def afficher_frame(frame):
    # Affiche la frame
    cv2.imshow("Frame", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def enregistrer_frame(frame, path):
    # Enregistre la frame
    cv2.imwrite(path, frame)
    print(f"Frame enregistrée à {path}")

def make_component(box_detail):
    # Box: (tensor([1112.8577,  704.6846,  207.5119,   53.7666]), tensor(0.9690), tensor(4.))
    # On convertit les tensors en tuples
    box = tuple(box_detail[0].tolist())
    confidence = box_detail[1]
    classe = int(box_detail[2])

    if classe == 0: # auteur_sondage
        component = auteur_sondage(box)
    elif classe == 1: # bouton_fermer_reponse
        component = bouton_fermer_reponse(box)
    elif classe == 2: # bouton_voir_tout
        component = bouton_voir_tout(box)
    elif classe == 3: # option_reponse
        component = option_reponse(box)
    elif classe == 4: # personne_sondee
        component = personne_sondee(box)
    elif classe == 5: # reponse_dev
        component = reponse_dev(box)
    elif classe == 6: # sondage
        component = sondage(box)
    elif classe == 7: # voir_reponses_option
        component = voir_reponses_option(box)

    return component


def detecter_bboxes(frame):
    model_path = os.getenv("MODEL")
    model = YOLO(model_path)
    results = model(frame)
    return results[0].boxes


if __name__ == "__main__":

    dotenv.load_dotenv()

    # Lire la frame en question
    frame = read_screen(debug = True)

    # Analyse de la frame
    composition = analyse_frames(frame)

    # Exporter la composition en frame
    enregistrer_frame(debug_exporter_composition_as_frame(composition, 1440, 2560), "test1.png")
    composition.debug_imprimer_arbre_composants()

    # Chargement de la DB
    #db_helper = database_helper_names()
    #db_helper.init_db()

