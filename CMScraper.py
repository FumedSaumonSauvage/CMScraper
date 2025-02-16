import cv2
import numpy as np
import dotenv
from composition_ecran import composition_ecran, composant, auteur_sondage, bouton_fermer_reponse, bouton_voir_tout, option_reponse, personne_sondee, reponse_dev, sondage, voir_reponses_option
from database import database_helper_names
from ultralytics import YOLO
import os
import pytesseract
from sondage import sondage_m, option_m
import json
import re


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



def write_to_json_file(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur ecriture Json: {e}")

def OCR(composant_graph, frame, confiance = 40):
    # On fait de l'OCR sur le composant précisément: selon le type, différentes stratégies

    c_frame = frame.copy() #évite les embrouilles par la suite

    #Réduction de la zone de la frame au composant
    if composant_graph.is_sondage():
        # Masquer l'auteur, et tout ce qui est plus bas que l'auteur
        x, y, w, h = composant_graph.position
        x1, y1, x2, y2 = int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2)
        
        auteur = [element for element in composant_graph.fils if element.is_auteur_sondage() == True]

        if auteur:
            auteur = auteur[0]
            x_a, y_a, w_a, h_a = auteur.position
            x1_a, y1_a, x2_a, y2_a = int(x_a - w_a / 2), int(y_a - h_a / 2), int(x_a + w_a / 2), int(y_a + h_a / 2)
            c_frame[y1_a:y2_a, x1_a:x2_a] = 0  # Masquer l'auteur

        reponses = [element for element in composant_graph.fils if element.is_option_reponse() == True]
        for reponse in reponses: # TODO: potentiellement redondant, amélioratioj possible en n'itérant que pour la réponse située le + haut
            x_r, y_r, w_r, h_r = reponse.position
            x1_r, y1_r, x2_r, y2_r = int(x_r - w_r / 2), int(y_r - h_r / 2), int(x_r + w_r / 2), int(y_r + h_r / 2)
            c_frame[y1_r:, :] = 0  # Masquer tout ce qui est à partir du début de la première réponse (et au dessous)

        cropped_frame = c_frame[y1:y2, x1:x2]

        data = pytesseract.image_to_data(cropped_frame, output_type=pytesseract.Output.DICT)
        text = " ".join(data['text'][i] for i in range(len(data['text'])) if int(data['conf'][i]) > confiance)
        text = text.replace("\n", " ")
        return text

    elif composant_graph.is_auteur_sondage():
        x, y, w, h = composant_graph.position
        x1, y1, x2, y2 = int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2)
        cropped_frame = frame[y1:y2, x1:x2]

        text = pytesseract.image_to_string(cropped_frame)
        # Lire seulement la première ligne
        first_line = text.split('\n')[0]
        return first_line
    
    elif composant_graph.is_option_reponse():
        x, y, w, h = composant_graph.position
        x1, y1, x2, y2 = int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2)
        
        # On vire un peu de bordure en plu pour éviter des problèmes d'OCR
        x1 += int(0.08 * w)
        
        cropped_frame = frame[y1:y2, x1:x2]
        
        data = pytesseract.image_to_data(cropped_frame, output_type=pytesseract.Output.DICT)
        niveau_bas = max(data['top']) # On prend le 50% des caractères en bas
        text = " ".join(data['text'][i] for i in range(len(data['text'])) if int(data['top'][i]) >= niveau_bas* 0.6)

        return text


    


if __name__ == "__main__":

    dotenv.load_dotenv()

    sondages_global = [] # Ensemble des sondages qui ont été vus

    # Lire la frame en question
    frame = read_screen(debug = True)

    # Analyse de la frame
    composition = analyse_frames(frame)

    # Exporter la composition en frame
    enregistrer_frame(debug_exporter_composition_as_frame(composition, 1440, 2560), "test1.png")
    #composition.debug_imprimer_arbre_composants()

    sondages_graph = composition.get_racines_sondage()
    for sg in sondages_graph:
        print(f"Analyse du sondage {sg.id}")
        sm = sondage_m()
        sm.description = OCR(sg, frame)
        auteur = [fils for fils in sg.fils if fils.is_auteur_sondage()]
        if auteur:
            sm.auteur = OCR(auteur[0], frame)
        else:
            sm.auteur = "Auteur inconnu"
        
        options = [fils for fils in sg.fils if fils.is_option_reponse()]
        for option in options:
            om = option_m()
            om.description = OCR(option, frame)
            taux_match = re.search(r'(\d+)%', om.description)
            om.taux = int(taux_match.group(1)) if taux_match else 0
            om.description = re.sub(r'\d+%', '', om.description).strip()
            sm.ajouter_option(om)
        
        sondages_global.append(sm)
    
    # Exporter les sondages en JSON
    data = {
        "sondages": [sondage.to_dict_smpl() for sondage in sondages_global]
    }

    write_to_json_file(data, "sondages.json")





