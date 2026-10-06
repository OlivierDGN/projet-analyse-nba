# Projet d'analyse NBA — Installation et téléchargement des données

Ce guide vous permet de préparer votre environnement de travail et de télécharger
le jeu de données NBA utilisé pendant le projet.

Comptez environ 15 minutes, et prévoyez **au moins 6 Go d'espace disque libre**
(archive de 700 Mo + 4,3 Go une fois décompressée).

---

## 1. Prérequis

- **Python 3** installé (le projet a été testé avec Python 3.14).
  Vérifiez dans un terminal :

  ```bash
  python3 --version
  ```

  > Sous Windows, la commande est souvent `python` ou `py` au lieu de `python3`.

- **Git** pour récupérer le projet.
- Un **compte Kaggle** (gratuit) : <https://www.kaggle.com>.

---

## 2. Récupérer le projet

```bash
git clone https://github.com/OlivierDGN/projet-analyse-nba.git
cd projet-analyse-nba
```

Toutes les commandes suivantes se lancent **depuis le dossier du projet**.

---

## 3. Créer l'environnement Python

Un environnement virtuel (`.venv`) isole les bibliothèques du projet de celles
de votre ordinateur.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Une fois l'environnement activé, `(.venv)` apparaît au début de la ligne du
terminal. **Pensez à le réactiver à chaque nouvelle session** avec la commande
`source` (ou `Activate.ps1`).

Le fichier `requirements.txt` installe :

| Bibliothèque | Rôle |
|---|---|
| `kaggle` | télécharger les données depuis Kaggle |
| `pandas` | manipuler et analyser les données |
| `nba_api` | interroger les statistiques officielles NBA (saisons récentes) |

---

## 4. Configurer l'accès à Kaggle

Kaggle demande une clé personnelle (un *token*) pour autoriser les téléchargements.

1. Connectez-vous sur <https://www.kaggle.com>.
2. Allez dans **Settings** (cliquez sur votre avatar, puis *Settings*).
3. Dans la section **API**, créez un nouveau token et copiez-le.
   Il ressemble à `KGAT_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
4. Enregistrez-le dans le fichier `~/.kaggle/access_token` :

**macOS / Linux**

```bash
mkdir -p ~/.kaggle
echo VOTRE_TOKEN > ~/.kaggle/access_token
chmod 600 ~/.kaggle/access_token
```

**Windows (PowerShell)**

```powershell
mkdir $HOME\.kaggle -Force
Set-Content -Path $HOME\.kaggle\access_token -Value "VOTRE_TOKEN" -NoNewline
```

Remplacez `VOTRE_TOKEN` par votre propre token.

> ⚠️ **Ce token est personnel, comme un mot de passe.** Ne le partagez pas,
> ne le mettez pas dans le code et ne le commitez jamais dans git.
> Si vous l'avez divulgué par erreur, supprimez-le sur Kaggle et créez-en un nouveau.

**Vérification :** cette commande doit afficher une liste de jeux de données NBA.

```bash
kaggle datasets list -s nba
```

---

## 5. Télécharger les données

Nous utilisons le jeu de données
[**NBA Database** de wyattowalsh](https://www.kaggle.com/datasets/wyattowalsh/basketball).

```bash
mkdir -p data/basketball
kaggle datasets download wyattowalsh/basketball -p data/basketball --unzip
```

Le téléchargement prend une à quelques minutes selon votre connexion.

> Le dossier `data/` est exclu de git (voir `.gitignore`) : les données ne doivent
> **pas** être commitées, elles sont trop volumineuses.

---

## 6. Ce que vous venez de télécharger

```
data/basketball/
├── nba.sqlite      ← base de données principale (2,2 Go) — à utiliser en priorité
├── nba.duckdb      ← quasiment vide, à ignorer
└── csv/            ← les mêmes tables au format CSV (2,2 Go)
```

Tables principales :

| Table | Lignes | Contenu |
|---|---|---|
| `game` | 65 698 | un match par ligne, avec les statistiques des deux équipes |
| `play_by_play` | 13,6 millions | toutes les actions de chaque match |
| `game_summary`, `line_score`, `game_info` | ~58 000 | détails des matchs, scores par quart-temps, affluence |
| `inactive_players` | 110 191 | joueurs absents par match |
| `officials` | 70 971 | arbitres par match |
| `player`, `common_player_info` | 4 815 / 3 632 | informations sur les joueurs |
| `draft_history`, `draft_combine_stats` | 8 257 / 1 633 | draft et tests physiques |
| `team`, `team_details`, `team_history` | 30 / 27 / 50 | informations sur les équipes |

> **Période couverte : de novembre 1946 à juin 2023.** Les saisons postérieures à
> 2022-23 ne sont pas incluses. Pour les données récentes, on utilisera `nba_api`.

---

## 7. Vérifier que tout fonctionne

Avec l'environnement activé, lancez :

```bash
python -c "
import sqlite3, pandas as pd
con = sqlite3.connect('data/basketball/nba.sqlite')
print(pd.read_sql('SELECT COUNT(*) AS nb_matchs, MIN(game_date) AS debut, MAX(game_date) AS fin FROM game', con))
"
```

Résultat attendu :

```
   nb_matchs                debut                  fin
0      65698  1946-11-01 00:00:00  2023-06-12 00:00:00
```

Si vous obtenez ce résultat, vous êtes prêts pour la suite ! 🏀

---

## En cas de problème

| Symptôme | Solution |
|---|---|
| `command not found: kaggle` | L'environnement n'est pas activé : relancez `source .venv/bin/activate` (ou `.venv\Scripts\Activate.ps1`). |
| Erreur d'authentification Kaggle (`401`, `Unauthorized`, message sur `access_token`) | Vérifiez que le fichier `~/.kaggle/access_token` existe et contient uniquement votre token, sans espace ni guillemets. |
| `403 Forbidden` au téléchargement | Ouvrez la page du jeu de données sur Kaggle en étant connecté, puis réessayez. |
| Windows : `Activate.ps1` bloqué (« l'exécution de scripts est désactivée ») | Lancez une fois `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, puis réessayez. |
| `no such table: game` | Le chemin est incorrect : lancez la commande depuis le dossier du projet. |
| Disque plein pendant la décompression | Libérez au moins 6 Go et relancez le téléchargement. |
