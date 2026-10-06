# Projet d'analyse NBA

**Qui est le meilleur joueur offensif de la NBA… et par rapport à qui ?**

Dans ce projet, vous construisez et comparez trois modèles de performance
offensive individuelle sur les saisons 2013-14 à 2022-23 :

1. un modèle basé sur les **percentiles** ;
2. un modèle basé sur les **z-scores** ;
3. un modèle qui compare chaque joueur aux joueurs du **même poste**, de la
   **même saison**, à **domicile** ou à l'**extérieur**.

## Par où commencer

| Étape | Document | Contenu |
|---|---|---|
| 1 | [INSTALLATION.md](INSTALLATION.md) | préparer l'environnement Python, télécharger la base Kaggle, premiers pas avec pandas |
| 2 | [SCENARIO.md](SCENARIO.md) | le projet pas à pas : données individuelles, vérification, les trois modèles, leur comparaison et les livrables |

## Contenu du dépôt

```
projet-analyse-nba/
├── README.md                     ← vous êtes ici
├── INSTALLATION.md               ← étape 1
├── SCENARIO.md                   ← étape 2
├── requirements.txt              ← bibliothèques Python à installer
├── .gitignore                    ← fichiers que git ignore (environnement, données)
└── scripts/
    └── telecharger_saisons.py    ← téléchargement des statistiques individuelles (nba_api)
```

Les données ne sont pas dans le dépôt : chacun les télécharge en suivant les
guides, dans un dossier `data/` créé sur son ordinateur.

## Sources des données

- [NBA Database](https://www.kaggle.com/datasets/wyattowalsh/basketball) (Kaggle) :
  matchs, équipes et actions de jeu, de 1946 à 2023.
- [`nba_api`](https://github.com/swar/nba_api) : statistiques officielles de la NBA,
  pour les feuilles de match individuelles et les postes des joueurs.
