import cv2
#import pymouse
import dotenv
from composition_ecran import composition_ecran
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
        return cv2.imread("frames_test/frame1.jpg")
    
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
        print(f"Box: ({x1}, {y1}, {x2}, {y2}), Confidence: {confidence:.2f}, Class: {class_id_to_name(int(class_id))}")




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
