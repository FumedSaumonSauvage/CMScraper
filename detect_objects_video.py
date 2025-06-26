# Infère sur une vidéo afin de tester les capacités du modèle.

import sys

import cv2
from ultralytics import YOLO


def selecteurCouleur(classe):
    match classe:
        case "auteur_sondage":
            return (255, 255, 0)
        case "bouton_fermer_reponse":
            return (255, 0, 0) 
        case "bouton_voir_tout":
            return (0, 255, 0)
        case "option_reponse":
            return (0, 0, 255)
        case "personne_sondee":
            return (255, 0, 255)
        case "reponse_dev":
            return (0, 255, 255) 
        case "sondage":
            return (128, 0, 128)
        case "voir_reponses_option":
            return (128, 128, 0)
        case _:
            return (255, 255, 255)

def inference(model_str, cap_str, out_str):
    model = YOLO(model_str)
    cap = cv2.VideoCapture(cap_str)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_str, fourcc, 30.0, (1920, 1080))

    print("Modèle: ", model_str)
    print("Vidéo: ", cap_str)
    print("Sortie: ", out)

    print("Noms des classes: ", model.names)

    if not cap.isOpened():
        print("Erreur ouverture fichier")

    # cap.set(cv2.CAP_PROP_POS_FRAMES, 3) #debug du pauvre, tej ce truc
    ret, frame = cap.read()

    if not ret:
        print("Erreur lecture frame")


    framenumber = 0
    totalframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while True and framenumber < 500:
        framenumber += 1

        print("Frame ", framenumber, "/", totalframes)
        cap.set(cv2.CAP_PROP_POS_FRAMES, framenumber)
        ret, frame = cap.read()

        # Quittage
        if not ret:
            break

        results = model(frame)

        for item in results:
            if len(item.boxes) == 0:
                print("Break because no results")
                break

            for box in item.boxes:
                x_min, y_min, x_max, y_max = box.xyxy[
                    0
                ]  # OSQ le seul truc important est le premier
                #print(x_min, y_min, x_max, y_max)
                confidence = box.conf[0]
                class_id = box.cls[0]
                class_name = model.names[int(class_id)]

                cv2.rectangle(
                    frame,
                    (int(x_min), int(y_min)),
                    (int(x_max), int(y_max)),
                    selecteurCouleur(class_name),
                    2,
                )
                text = f"{class_name} ({confidence:.2f})"
                cv2.putText(
                    frame,
                    text,
                    (int(x_min), int(y_min) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    selecteurCouleur(class_name),
                    2,
                )

        out.write(frame)

    cap.release()
    out.release()


    print("OK")

if __name__ == "__main__":
    try:
        model = sys.argv[1]
        cap = sys.argv[2]
        out = sys.argv[3]
    except IndexError:
        print("Utilisation: python detect_objects_video.py <model> <video> <output>")
        sys.exit(1)

    inference(model, cap, out)
