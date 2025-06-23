# Scripts utiles

Dossier contenant des scripts, à l'utilité variable.

## Frame separator

Script qui aide dans la création de données prêtes à être annotées: prend en entrée une capture d'écran vidéo de votre meilleur scroll sur CMS, et la sépare en images.

Exemple d'utilisation: `python frame_separator.py `

## Prélabellisation:
Utilise un modèle déjà entrainé pour prélabelliser des images, et accélérer la labellisation sur Label Studio.

Exemple d'utilisation: `python prelabeller.py --model ../weight_douteux.pt --folder ./framesep_out --classes classes.txt --confidence-threshold 0.25 --destination CMScraper_data`

Pour aider un peu avec l'arborescence, voici ce que je conseille. Ne tenez pas compte des dossiers générés, qui n'ont pas besoin d'être placés à la main.
```
scripts_utiles/
├── CMScraper_data/prelabels/ # Généré
│   ├── images/
│   ├── labels/
│   └── classes.txt
├── framesep_out/images
│   ├── img1.jpg
│   └── ...
├── out_json/ # Généré
│   ├── predictions.json
│   ├── predictions.label_config.xml
├── classes.txt
├── prelabeller.py
└── README.md
```

## Dataset maker

Dans les versions récentes de Label Studio, les images ne sont plus téléchargeables à l'export. Ce script fabrique un dataset YOLO à partir d'une banque dimage, et d'un paquets de labels YOLO.