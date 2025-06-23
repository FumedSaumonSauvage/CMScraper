import argparse
import os
import shutil
import subprocess
from ultralytics import YOLO


def prelabel(model_path, folder, class_names_file, confidence_threshold, destination_LS_root):

    # Vérification des paramètres
    if not os.path.exists(model_path):
        print(f"[Prelabeller] [ERR] '{model_path}' introuvable")
        return
    if not os.path.isdir(folder):
        print(f"[Prelabeller] [ERR] '{folder}' introuvable")
        return
    if not os.path.exists(class_names_file):
        print(f"[Prelabeller] [ERR] '{class_names_file}' introuvable")
        return

    # Lecture des classes
    try:
        with open(class_names_file, 'r', encoding='utf-8') as f:
            class_names = [line.strip() for line in f if line.strip()]
        if not class_names:
            print("[Prelabeller] [ERR] Le fichier de classes est vide")
            return
        print(f"[Prelabeller] [DEBUG] Noms de classes: {class_names}")
    except Exception as e:
        print(f"[Prelabeller] [ERR] Erreur lors de la lecture de '{class_names_file}' : {e}")
        return

    images_folder_input = os.path.join(folder, "images")
    if not os.path.isdir(images_folder_input):
        print(f"[Prelabeller] [ERR] '{images_folder_input}' introuvable")
        return

    # Stockage temporaire YOLO
    yolo_temp_run_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolo_temp_run")
    os.makedirs(yolo_temp_run_dir, exist_ok=True)
    print(f"[Prelabeller] [DEBUG] temp YOLO: {yolo_temp_run_dir}")

    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"[Prelabeller] [ERR] Erreur chargement YOLO : {e}")
        return

    print(f"[Prelabeller] [INF] Inférence sur images dans '{images_folder_input}'...")
    results = model(images_folder_input, save_txt=True, conf=confidence_threshold, project=yolo_temp_run_dir, name="inference_output")

    output_run_dir = None
    for result in results:
        if hasattr(result, 'save_dir') and result.save_dir:
            output_run_dir = result.save_dir
            break

    if not output_run_dir or not os.path.isdir(output_run_dir):
        print(f"[Prelabeller] [ERR] Sortie de YOLO pas trouvée: {output_run_dir}")
        return

    source_labels_dir = os.path.join(output_run_dir, 'labels')
    print(f"[Prelabeller] [DEBUG] Labels YOLO: {source_labels_dir}")

    # Préparation des fichiers pour Label Studio
    final_destination_LS_folder = os.path.join(destination_LS_root, "prelabels")
    print(f"[Prelabeller] [INF] Préparation des fichiers pour Label Studio à '{final_destination_LS_folder}'...")

    if os.path.exists(final_destination_LS_folder):
        print(f"[Prelabeller] [WARN] Suppression de l'ancienne destination: {final_destination_LS_folder}")
        shutil.rmtree(final_destination_LS_folder)
    os.makedirs(final_destination_LS_folder, exist_ok=True)

    shutil.copytree(images_folder_input, os.path.join(final_destination_LS_folder, "images"))
    print(f"[Prelabeller] [INF] Images copiées")
    shutil.copy(class_names_file, os.path.join(final_destination_LS_folder, "classes.txt"))

    if os.path.isdir(source_labels_dir):
        shutil.copytree(source_labels_dir, os.path.join(final_destination_LS_folder, "labels"))
        print(f"[Prelabeller] [INF] Labels copiés")
    else:
        print(f"[Prelabeller] [WARN] Pas de labels trouvés à '{source_labels_dir}'")

    # Conversion YOLO -> Label Studio
    label_studio_json_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_json", "predictions.json")
    os.makedirs(os.path.dirname(label_studio_json_output_path), exist_ok=True)

    print(f"[Prelabeller] [INF] Conversion YOLO -> Label Studio...")
    command = [
        "label-studio-converter", "import", "yolo",
        "-i", final_destination_LS_folder,
        "-o", label_studio_json_output_path,
        "--image-ext", ".jpg",
        "--image-root-url", f"/data/local-files/?d={destination_LS_root}"
    ]

    print(f"Exec cmd: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("[Prelabeller] [INF] Sortie label-studio-converter :")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[Prelabeller] [ERR] Erreur label-studio-converter: {e}")
        print(f"[Prelabeller] [ERR] Stderr: {e.stderr}")
    except FileNotFoundError:
        print("[Prelabeller] [ERR] label-studio-converter pas trouvé")

    # Remplacement "annotations" -> "predictions" dans le JSON
    print(f"[Prelabeller] [INF] Remplacement Annotation -> prediction dans le JSON...")
    try:
        with open(label_studio_json_output_path, 'r', encoding='utf-8') as f:
            json_content = f.read()

        modified_json_content = json_content.replace('"annotations":', '"predictions":')

        with open(label_studio_json_output_path, 'w', encoding='utf-8') as f:
            f.write(modified_json_content)
        print(f"[Prelabeller] [INF] Remplacement terminé, fichier {label_studio_json_output_path} mis à jour")
    except FileNotFoundError:
        print(f"[Prelabeller] [ERR] {label_studio_json_output_path} introuvable")
    except Exception as e:
        print(f"[Prelabeller] [ERR] {e}")

    # Nettoyage temporaire
    try:
        if os.path.exists(yolo_temp_run_dir):
            shutil.rmtree(yolo_temp_run_dir)
            print(f"[Prelabeller] [INF] '{yolo_temp_run_dir}' supprimé.")
    except Exception as e:
        print(f"[Prelabeller] [ERR] Erreur suppression '{yolo_temp_run_dir}': {e}")

    print("[Prelabeller] [INF] Préannotation terminée")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Génère des préannotations YOLO et Label Studio à partir d'un modèle YOLO et d'un dataset images")
    parser.add_argument("--model", type=str, required=True, help="Chemin vers le fichier du modèle YOLO (.pt)")
    parser.add_argument("--folder", type=str, required=True, help="Chemin vers le dossier contenant les images")
    parser.add_argument("--classes", type=str, required=True, help="Chemin vers le fichier texte contenant les noms de classes, un par ligne")
    parser.add_argument("--confidence-threshold", type=float, default=0.25, help="Seuil de confiance pour les détections")
    parser.add_argument("--destination", type=str, required=True, help="Chemin vers le dossier de destination pour Label Studio")

    args = parser.parse_args()

    prelabel(args.model, args.folder, args.classes, args.confidence_threshold, args.destination)
