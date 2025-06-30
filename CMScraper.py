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
from Levenshtein import distance as levenshtein_distance
import time
import sys


def verbose(level):
    # Factory de décorateurs spécifiques à la verbose.
    # Niveau de verbose contenu entre 0 (minimal) et 3 (maximal), cf. .env pour régler le niveau de verbose.
    def decorator(func):
        def wrapper(*args, **kwargs):
            global current_verbosity_level
            if current_verbosity_level >= level:
                return func(*args, **kwargs)
            else:
                print(f"Fonction '{func.__name__}' ignorée verbose faible")
                return None
        return wrapper
    return decorator


def read_screen(debug = False, i = -1):
    # Lit l"écran et renvoie une frame
    # En débug, on utilise juste une frame qui traine
    if debug and i ==-1:
        return cv2.imread("test_frame.png")
    elif debug and i >= 0:
        # Lecture de la frame suivante (frame i) dans la vidéo de test
        video_path = "test_short.mov"
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None  
        return frame
    else:
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("Erreur lors de l'ouverture de la caméra")
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print("Erreur lors de la lecture de la frame")
            return None
        return frame
    
    
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

@verbose(level=2)
def enregistrer_frame(frame, path):
    # Enregistre la frame
    cv2.imwrite(path, frame)
    print(f"Frame enregistrée à {path}")

@verbose(level=3)
def enregistrer_frame_dans_video(frame, path):
    # Met al frame à la suite de la vidéo indiquée. Si la vidéo n'existe pas (frame 0), on la crée
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 30.0
    width = frame.shape[1]
    height = frame.shape[0]
    video = cv2.VideoWriter(path, fourcc, fps, (width, height))
    video.write(frame)
    video.release()
    print(f"Video màj à {path}")

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

        enregistrer_frame(cropped_frame, "debug/cropped_sondage.png") # debug

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
        x1 += int(0.05 * w) # TODO: paramétrer et tej ces constantes
        
        cropped_frame = frame[y1:y2, x1:x2]
        
        data = pytesseract.image_to_data(cropped_frame, output_type=pytesseract.Output.DICT)
        text = " ".join(data['text'][i] for i in range(len(data['text'])) if int(data['conf'][i]) > confiance)

        return text
    
def correlation_txt(texteA, texteB, seuil = 0.1):
    # Utilisation de la distance de Levenshtein pour déterminer si texteA = TexteB
    # Si distance < seuil * max(len(texteA), len(texteB)), on considère que les textes sont égaux
    if texteA is None or texteB is None:
        return False
    
    distance = levenshtein_distance(texteA, texteB)
    max_length = max(len(texteA), len(texteB))
    
    if max_length == 0:  # Eviter la division par zéro
        return True
    
    return distance < seuil * max_length

def correlation_sondage(sondageA, sondageB, seuil = 0.1):
    # Utilisation de la distance de Levenshtein pour déterminer si sondageA = sondageB
    # On compare les descriptions, auteurs et options de réponse
    if sondageA is None or sondageB is None:
        return False
    
    if not correlation_txt(sondageA.description, sondageB.description, seuil):
        return False
    
    if not correlation_txt(sondageA.auteur, sondageB.auteur, seuil):
        return False
    
    return True # On considère que deux sondages sont identiques s'ils portent le même auteur et la même description

    
def verifier_vision_sondage(composant_graph, frame, padding_minimal = 50):
    # Vérifie si le sondage est visible au complet
    # On vérifie que le composant est un sondage, et quu'il y a du padding au dessous du sondage (ou alors un nouveau sondage)
    if composant_graph.is_sondage():
        # On vérifie que le composant est un sondage
        # On vérifie qu'il y a du padding au dessous du sondage (ou alors un nouveau sondage)
        x, y, w, h = composant_graph.position
        x1, y1, x2, y2 = int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2)
        
        # Vérifier si le sondage est visible au complet
        if not (y2 < frame.shape[0] - padding_minimal):  # Si le bas du sondage est à moins de 50 pixels du bas de l'écran
            # Vérifier s'il y a un autre sondage en dessous
            for composant in composant_graph.fils:
                if composant.is_sondage():
                    x2_s, y2_s, w2_s, h2_s = composant.position
                    x1_s, y1_s, x2_s, y2_s = int(x2_s - w2_s / 2), int(y2_s - h2_s / 2), int(x2_s + w2_s / 2), int(y2_s + h2_s / 2)
                    if y1 < y1_s:
                        return False

        
        # Verification que le sondage possède un auteur et un contenu
        auteur = [fils for fils in composant_graph.fils if fils.is_auteur_sondage()]
        if not auteur:
            print("Sondage sans auteur")
            return False
        
        contenu = [fils for fils in composant_graph.fils if fils.is_option_reponse()]
        if not contenu:
            print("Sondage sans contenu")
            return False
        
        # Si on arrive ici, le sondage est complet
        return True
    return False

def scroll_down(scroll_type, goto_x=None, goto_y=None):
    """
    Scrolle vers le bas, en fonction du type de scroll.
    goto_x et goto_y sont optionnels, si fournis, on déplace la souris avant de scroller.
    """
    if goto_x is not None and goto_y is not None:
        move_mouse_to(goto_x, goto_y)

    try:
        if IS_MACOS or IS_XORG:
            if scroll_type == "small":
                pyautogui.scroll(3)
            elif scroll_type == "big":
                pyautogui.scroll(6)
            else:
                raise ValueError("TScroll inconnu")
        elif IS_WAYLAND:
            if scroll_type == "small":
                _wayland_mouse_controller.scroll(-100) # Valeurs douteuses
            elif scroll_type == "big":
                _wayland_mouse_controller.scroll(-300)
            else:
                raise ValueError("Scroll inconnu")
    except Exception as e:
        print(f"Erreur inattendue lors du scroll: {e}")


def simulate_click(x_screen, y_screen, button='left', clicks=1, interval=0.1):
    """
    Simule un clic de souris à la position donnée.
    """
    print(f"Cliquage à ({x_screen}, {y_screen}) avec le bouton {button}, {clicks} fois.")
    if IS_MACOS or IS_XORG:
        pyautogui.click(x=x_screen, y=y_screen, button=button, clicks=clicks, interval=interval)
    elif IS_WAYLAND:
        move_mouse_to(x_screen, y_screen)
        for _ in range(clicks):
            if button == 'left':
                _wayland_mouse_controller.click("left")
            elif button == 'right':
                _wayland_mouse_controller.click("right")
            elif button == 'middle':
                _wayland_mouse_controller.click("middle")
            else:
                print(f"Bouton de souris '{button}' inconnu")
                break
            if clicks > 1:
                time.sleep(interval)

def move_mouse_to(x_screen, y_screen, duration=0.5):
    """
    Déplace la souris à la position (x_screen, y_screen).
    Pas de duration pour wayland
    """
    print(f"Déplacement de la souris à ({x_screen}, {y_screen})")
    if IS_MACOS or IS_XORG:
        pyautogui.moveTo(x_screen, y_screen, duration=duration)
    elif IS_WAYLAND:
        _wayland_mouse_controller.move(x_screen, y_screen)



    
def main_loop(screen_width, screen_height):
    
    frame_index = 0
    sondages_global = []  # Ensemble des sondages qui ont été vus

    while True and frame_index < 10:  # Limite de frames pour éviter une boucle infinie
        # Analyse de l'écran
        frame = read_screen()
        frame_index += 1
        composition = analyse_frames(frame)

        print(f"\nPasse {frame_index} -- Frame lue, analyse en cours...\n")

        if frame is None:
            break  # passage à l'enregistrement des données

        # DEBUG -- enregistrement de la frame et de la composition
        if not os.path.exists("debug/analyses"):
            os.makedirs("debug/analyses")
        if not os.path.exists("debug/raw"):
            os.makedirs("debug/raw")
        enregistrer_frame(debug_exporter_composition_as_frame(composition, screen_height, screen_width), f"debug/analyses/test{frame_index}.png")
        enregistrer_frame(frame, f"debug/raw/test{frame_index}.png")
        
        
        # Le sondage est-il complet?
        sondages_graph = composition.get_racines_sondage()
        sondage_complet = None 
        for sg in sondages_graph:
            if verifier_vision_sondage(sg, frame):
                sondage_complet = sg.id
                print(f"Sondage complet trouvé: {sg.id}")
                break
            else:
                print(f"Trouvé: sondage incomplet à la passe {frame_index}")
                scroll_down("small")
                continue

        if sondage_complet is not None:
            # On clique sur le bouton "voir tout"
            bouton_voir_tout = [fils for fils in sg.fils if fils.is_bouton_voir_tout()]

            # DEBUG -- Pour le moment, pas de clic du bouton implémenté
            #if bouton_voir_tout:
                #bouton_voir_tout[0].click()
                #print("Bouton 'voir tout' cliqué")
            #else:
                #print("Aucun bouton 'voir tout' trouvé")
                #continue

            # On lit l'auteur, son texte total et ses options de réponse
            sm = sondage_m()
            sm.description = OCR(sg, frame)
            if sm.description is None or sm.description == "":
                print("Sondage sans description, ignoré")
                scroll_down("small")
                break
            auteur = [fils for fils in sg.fils if fils.is_auteur_sondage()]
            if auteur:
                sm.auteur = OCR(auteur[0], frame)
            else:
                break # Pas d'auteur, on passe au sondage suivant
            
            options = [fils for fils in sg.fils if fils.is_option_reponse()]
            for option in options:
                # Tout pourri quand le texte a 2 lignes, TODO refaire cette fonction
                om = option_m()
                om.description = OCR(option, frame)
                taux_match = re.search(r'(\d+)%', om.description)
                om.taux = int(taux_match.group(1)) if taux_match else 0
                om.description = re.sub(r'\d+%', '', om.description).strip()
                if om.description.endswith(">"):
                    om.description = om.description[:-1].strip()
                sm.ajouter_option(om)

            sondage_m_prec = None
            # On vérifie si le sondage existe déjà dans la base de données.TODO: optimiser par la suite, complexité délirante
            for sondage in sondages_global:
                if correlation_sondage(sondage, sm):
                    sondage_m_prec = sondage
                    break

            if sondage_m_prec is not None:
                # On met à jour le sondage existant
                print(f"Sondage déjà existant: {sondage_m_prec.id}, mise à jour")
                if len(sm.description) > len(sondage_m_prec.description): # TODO: raffiner la stratégie de màj
                    sondage_m_prec.description = sm.description
                if len(sm.options) > len(sondage_m_prec.options):
                    for option in sm.options:
                        # On vérifie si l'option existe déjà
                        option_existe = False
                        for option_prec in sondage_m_prec.options:
                            if correlation_txt(option.description, option_prec.description):
                                option_existe = True
                                break
                        if not option_existe:
                            sondage_m_prec.ajouter_option(option)

            else: # Le sondage n'existe pas, ajout à la liste globale
                print(f"Nouveau sondage trouvé: {sm.description}, auteur: {sm.auteur}")
                sondages_global.append(sm)

            scroll_down("big")

            
    
        else:
            scroll_down("small")

    # Exporter les sondages en JSON une fois à la fin
    data = {
        "sondages": [sondage.to_dict_smpl() for sondage in sondages_global]
    }

    write_to_json_file(data, "debug/sondages.json")
                






    


if __name__ == "__main__":

    dotenv.load_dotenv()


    # Compatibilité Wayland + Xorg
    IS_MACOS = sys.platform == 'darwin'
    IS_LINUX = sys.platform == 'linux'
    IS_XORG = False
    IS_WAYLAND = False

    if IS_LINUX:
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE')
        if xdg_session_type == 'wayland':
            IS_WAYLAND = True
            print("Environnement: Wayland")
        elif xdg_session_type == 'x11':
            IS_XORG = True
            print("Environnement: Xorg")
        else:
            print("Environnement Linux inconnu, voir XDG_SESSION_TYPE")
            print("Default à Xorg")
            IS_XORG = True # Tente PyAutoGUI par défaut sur Linux si non spécifié
    elif IS_MACOS:
        print("Environnement: macOS")
    else:
        print(f"Système inconnu {sys.platform}")
        sys.exit(1)

    if IS_MACOS or IS_XORG:
        try:
            import pyautogui
        except ImportError:
            print("Erreur import pyatogui")
            sys.exit(1)
    elif IS_WAYLAND:
        try:
            from wayland_automation.mouse_controller import Mouse
            _wayland_mouse_controller = Mouse()
        except ImportError:
            print("Erreur import wayland-automation")
            sys.exit(1)
        except Exception as e:
            print(f"Erreur init wayland-automation : {e}")
            sys.exit(1)


    current_verbosity_level = 2

    screen_width = int(os.getenv("RESOLUTION_WIDTH"))
    screen_height = int(os.getenv("RESOLUTION_HEIGHT"))

    main_loop(screen_width, screen_height)

    print("Finito")
    






