import os
import shutil
import random
import argparse
from ultralytics import YOLO

def train_yolo_model(yaml_path, epochs, model_path):
    model = YOLO(model_path)
    model.train(data=yaml_path, epochs=epochs, imgsz=1080, batch=2, device="cpu", workers=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entraine un modèle YOLO (fine tuning).")
    parser.add_argument("--yaml", type=str, default="data.yaml", help="Fichier de configuration YAML pour le modèle YOLO.")
    parser.add_argument("--epochs", type=int, default=50, help="Nombre d'époques pour l'entraînement.")
    parser.add_argument("--model", type=str, default="yolo11m.pt", help="Chemin vers le modèle YOLO pré-entraîné.")
    args = parser.parse_args()

    train_yolo_model(args.yaml, args.epochs, args.model)
