import os
import shutil
import random
import argparse
from ultralytics import YOLO

def prepare_yolo_dataset(data_dir, val_ratio=0.1):
    """
    Prépare un dataset pour l'entraînement YOLO en divisant les images et les labels
    en ensembles d'entraînement et de validation.

    Args:
        data_dir (str): Le chemin vers le dossier principal du dataset (ex: cms180).
        val_ratio (float): Le ratio de données à utiliser pour l'ensemble de validation (entre 0 et 1).
    """
    images_dir = os.path.join(data_dir, 'images')
    labels_dir = os.path.join(data_dir, 'labels')
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')
    train_images_dir = os.path.join(train_dir, 'images')
    train_labels_dir = os.path.join(train_dir, 'labels')
    val_images_dir = os.path.join(val_dir, 'images')
    val_labels_dir = os.path.join(val_dir, 'labels')

    # Créer les dossiers train et val s'ils n'existent pas
    os.makedirs(train_images_dir, exist_ok=True)
    os.makedirs(train_labels_dir, exist_ok=True)
    os.makedirs(val_images_dir, exist_ok=True)
    os.makedirs(val_labels_dir, exist_ok=True)

    # Récupérer la liste des noms de fichiers d'images (sans extension)
    image_files = [f.split('.')[0] for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
    random.shuffle(image_files)

    # Calculer le nombre d'images pour l'ensemble de validation
    num_val = int(len(image_files) * val_ratio)
    val_files = image_files[:num_val]
    train_files = image_files[num_val:]

    print(f"Nombre total d'images: {len(image_files)}")
    print(f"Nombre d'images pour l'entraînement: {len(train_files)}")
    print(f"Nombre d'images pour la validation: {len(val_files)}")

    # Déplacer les fichiers d'entraînement
    for file_prefix in train_files:
        image_src = os.path.join(images_dir, f"{file_prefix}.jpg")  # Assurez-vous de l'extension correcte
        label_src = os.path.join(labels_dir, f"{file_prefix}.txt")
        image_dst = os.path.join(train_images_dir, f"{file_prefix}.jpg")
        label_dst = os.path.join(train_labels_dir, f"{file_prefix}.txt")

        if os.path.exists(image_src):
            shutil.copy(image_src, image_dst)
        if os.path.exists(label_src):
            shutil.copy(label_src, label_dst)

    print("Fichiers d'entraînement déplacés.")

    # Déplacer les fichiers de validation
    for file_prefix in val_files:
        image_src = os.path.join(images_dir, f"{file_prefix}.jpg")  # Assurez-vous de l'extension correcte
        label_src = os.path.join(labels_dir, f"{file_prefix}.txt")
        image_dst = os.path.join(val_images_dir, f"{file_prefix}.jpg")
        label_dst = os.path.join(val_labels_dir, f"{file_prefix}.txt")

        if os.path.exists(image_src):
            shutil.copy(image_src, image_dst)
        if os.path.exists(label_src):
            shutil.copy(label_src, label_dst)

    print("Fichiers de validation déplacés.")
    print("Préparation du dataset terminée.")

def train_yolo_model(yaml_path):
    model = YOLO("yolo11m.pt")
    model.train(data=yaml_path, epochs=100, imgsz=1080, batch=2, device="cpu", workers=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prépare un dataset YOLO pour l'entraînement.")
    parser.add_argument("--data_dir", type=str, default="data.yaml", help="Le chemin vers le dossier principal du dataset (ex: cms180).")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="Le ratio de données à utiliser pour l'ensemble de validation (entre 0 et 1).")
    parser.add_argument("mode", type=str, choices = ["prepare", "train"], default="prepare", help="Mode d'exécution")
    parser.add_argument("--yaml", type=str, default="data.yaml", help="Fichier de configuration YAML pour le modèle YOLO.")
    args = parser.parse_args()

    if args.mode == "train":
        train_yolo_model(args.yaml)
    elif args.mode == "prepare":
        prepare_yolo_dataset(args.data_dir, args.val_ratio)