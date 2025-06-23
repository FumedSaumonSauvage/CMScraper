import os
import shutil
import argparse

def populate_label_studio_images(dataset_path, source_images_path):
    """
    Copies images from a source directory to a Label Studio dataset's 'images' folder
    if a corresponding label file (YOLO .txt) exists.

    Args:
        dataset_path (str): Path to the Label Studio dataset folder
                            (e.g., 'XXX/', containing 'labels/' and 'images/').
        source_images_path (str): Path to the directory containing all source images.
    """
    labels_folder = os.path.join(dataset_path, 'labels')
    images_target_folder = os.path.join(dataset_path, 'images')

    # Create target images folder if it doesn't exist
    os.makedirs(images_target_folder, exist_ok=True)

    if not os.path.isdir(labels_folder):
        print(f"Error: Labels folder not found at '{labels_folder}'. Please check your dataset path.")
        return
    if not os.path.isdir(source_images_path):
        print(f"Error: Source images folder not found at '{source_images_path}'. Please check your source path.")
        return

    # Look for .txt files for YOLO labels
    label_files = [f for f in os.listdir(labels_folder) if f.endswith('.txt')]
    copied_count = 0

    print(f"Scanning for YOLO label files (.txt) in: {labels_folder}")
    print(f"Looking for images in: {source_images_path}")
    print(f"Copying matching images to: {images_target_folder}\n")

    for label_file in label_files:
        base_name = os.path.splitext(label_file)[0]

        found_image = False
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            image_name = base_name + ext
            source_image_path = os.path.join(source_images_path, image_name)

            if os.path.exists(source_image_path):
                target_image_path = os.path.join(images_target_folder, image_name)
                if not os.path.exists(target_image_path):
                    try:
                        shutil.copy2(source_image_path, target_image_path)
                        print(f"Copied: {image_name}")
                        copied_count += 1
                        found_image = True
                        break
                    except Exception as e:
                        print(f"Error copying {image_name}: {e}")
                else:
                    found_image = True 
                    break
        
        if not found_image:
            print(f"Warning: No matching image found for label '{label_file}' in source directory.")

    print(f"\n--- Script Finished ---")
    print(f"Total images copied: {copied_count}")
    print(f"Images are now in: {images_target_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Copies images to a Label Studio dataset's 'images' folder based on existing label files."
    )
    parser.add_argument(
        "--dataset_path",
        help="Path to your Label Studio dataset folder, YOLO format. Should contain XXX/labels and XXX/images subfolders.",
        default="./dataset"
        
    )
    parser.add_argument(
        "--source_images_path",
        help="Path to the directory containing all your source images. Generally the Label Studio source storage folder.",
        default="/mnt/seagate/label_studio_storage/CMScraper_data"
    )
    
    args = parser.parse_args()

    populate_label_studio_images(args.dataset_path, args.source_images_path)