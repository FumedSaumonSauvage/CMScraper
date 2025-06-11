 
import cv2
import os
import random
import argparse

def extract_frames(video_path, output_dir, nb_frames=50, name = 0):

  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  cap = cv2.VideoCapture(video_path)

  total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

  if not cap.isOpened():
    print("Error opening video file")
    return

  frame_indices = random.sample(range(total_frames), nb_frames)
  frame_count = 0
  nom_frame = name


  while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break

    if frame_count in frame_indices:
        frame_name = f"frame_{nom_frame}.jpg"
        nom_frame += 1
        output_path = os.path.join(output_dir, frame_name)
        cv2.imwrite(output_path, frame)
        print(f"Saved {output_path}")
    frame_count += 1

  cap.release()
  print("Extraction finito")
  return nom_frame

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Sépare une vidéo en frames pour annotation.")
  parser.add_argument("--video", type=str, default="train.mov", help="Chemin vers vidéo")
  parser.add_argument("--out_dir", type=str, default="framesep_out", help="Chemin dossier de sortie")
  parser.add_argument("--image_count", type=int, default="300", help="Nombre d'images à sélectionner")
  args = parser.parse_args()

  extract_frames(args.video, args.out_dir, args.image_count)
