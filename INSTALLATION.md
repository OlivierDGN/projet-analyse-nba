# Projet d'analyse NBA — Installation et premiers pas

Ce guide vous permet de préparer votre environnement de travail, de télécharger
le jeu de données NBA utilisé pendant le projet, puis de l'explorer avec pandas.

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

## 8. Explorer les données avec pandas

Maintenant que les données sont là, prenons-en connaissance. Créez un fichier
`exploration.py` à la racine du projet, ajoutez-y les blocs de code ci-dessous
au fur et à mesure, et lancez-le avec :

```bash
python exploration.py
```

### 8.1 Se connecter à la base et lister les tables

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("data/basketball/nba.sqlite")

tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type = 'table'", con)
print(tables)
```

`pd.read_sql` exécute une requête SQL et renvoie le résultat sous forme de
**DataFrame**, le tableau de pandas.

### 8.2 Charger les matchs de saison régulière

```python
matchs = pd.read_sql("SELECT * FROM game WHERE season_type = 'Regular Season'", con)

print(matchs.shape)   # (nombre de lignes, nombre de colonnes)
print(matchs[["game_date", "team_name_home", "pts_home", "team_name_away", "pts_away", "wl_home"]].head())
```

```
(60192, 55)
             game_date           team_name_home  ...  pts_away wl_home
0  1946-11-01 00:00:00          Toronto Huskies  ...      68.0       L
1  1946-11-02 00:00:00        St. Louis Bombers  ...      51.0       W
...
```

Chaque ligne est un match. Les colonnes vont par paires : `_home` pour l'équipe
qui reçoit, `_away` pour l'équipe qui se déplace (`pts` = points, `reb` = rebonds,
`ast` = passes décisives, `fg3a` = tirs à 3 points tentés, etc.).

> La table `game` contient aussi les matchs de présaison, de playoffs et les
> All-Star Games (colonne `season_type`). On les exclut ici pour comparer ce qui
> est comparable.

### 8.3 Premier coup d'œil : types, statistiques, valeurs manquantes

```python
matchs.info(verbose=False)                      # types de colonnes, mémoire utilisée
print(matchs[["pts_home", "pts_away", "fg3a_home", "reb_home", "ast_home"]].describe().round(1))
print(matchs.isna().sum().sort_values(ascending=False).head())   # colonnes les plus incomplètes
```

```
       pts_home  pts_away  fg3a_home  reb_home  ast_home
count   60192.0   60192.0    42668.0   45388.0   45323.0
mean      104.8     101.2       17.5      43.8      24.1
...
```

**À observer :**
- `count` n'est pas le même partout : les points sont connus pour tous les matchs,
  mais les rebonds, passes ou tirs à 3 points **manquent pour les matchs anciens**
  (ces statistiques n'étaient pas encore relevées). Pensez-y avant de comparer
  des époques.
- Le `min` de `reb_home` vaut 0 : un match sans aucun rebond est impossible, c'est
  une donnée manquante codée en 0. Méfiez-vous des valeurs extrêmes.

### 8.4 L'avantage du terrain existe-t-il ?

```python
print(matchs["wl_home"].value_counts(normalize=True).round(3))
```

```
wl_home
W    0.618
L    0.382
```

Sur toute l'histoire de la NBA, l'équipe qui reçoit gagne **près de 62 %** des matchs.

### 8.5 Évolution par saison : la révolution du tir à 3 points

La colonne `season_id` encode le type de saison et l'année : `22022` signifie
saison régulière (`2`) 2022-23 (`2022`). On extrait l'année, puis on regroupe
avec `groupby` :

```python
matchs["saison"] = matchs["season_id"].str[1:].astype(int)

par_saison = matchs.groupby("saison").agg(
    nb_matchs=("game_id", "count"),
    points_dom=("pts_home", "mean"),
    tirs_3pts_dom=("fg3a_home", "mean"),
).round(1)

print(par_saison.loc[[1980, 1990, 2000, 2010, 2022]])
```

```
        nb_matchs  points_dom  tirs_3pts_dom
saison
1980          943       110.0            NaN
1990         1107       108.7            7.0
2000         1189        96.3           13.7
2010         1230       101.1           18.1
2022         1230       115.9           34.4
```

Le nombre de tirs à 3 points tentés par match a été **multiplié par 5 en 30 ans**.
(`NaN` = donnée non disponible pour cette saison.) On voit aussi que les points
marqués ont baissé entre 1990 et 2000 avant de remonter.

### 8.6 Les grosses tables : filtrer avant de charger

La table `play_by_play` compte **13,6 millions de lignes** : ne la chargez jamais
en entier avec `SELECT *`. Filtrez toujours avec `WHERE` (ou `LIMIT`).
Exemple : le match 7 des finales 2016, Warriors contre Cavaliers.

```python
finale = pd.read_sql("SELECT * FROM play_by_play WHERE game_id = '0041500407'", con)
print(finale.shape)

paniers = finale.dropna(subset=["score"])
print(paniers[["period", "pctimestring", "homedescription", "visitordescription", "score"]].tail(4))
```

```
(442, 34)
     period pctimestring                                   homedescription                        visitordescription    score
390       4         4:39  Thompson 2' Driving Layup (14 PTS) (Green 9 AST)                                       NaN  89 - 89
421       4         0:53                                               NaN  Irving 25' 3PT Pullup Jump Shot (26 PTS)  92 - 89
432       4         0:10                                               NaN          James Free Throw 2 of 2 (27 PTS)  93 - 89
...
```

On retrouve le tir à 3 points décisif de Kyrie Irving à 53 secondes de la fin.

> Le play-by-play ne couvre pas tous les matchs : il commence à la saison
> 1996-97 (environ 30 000 matchs) et ne contient pas les finales 2023.

### 8.7 Alternative : lire les fichiers CSV

Les mêmes tables existent en CSV. C'est pratique pour les petites tables :

```python
joueurs = pd.read_csv("data/basketball/csv/player.csv")
print(joueurs.shape)        # (4831, 5)
print(joueurs.head())
```

Pour les grosses tables (`play_by_play.csv` fait plus de 2 Go), préférez la base
SQLite, qui permet de filtrer **avant** de charger en mémoire.

### 8.8 Fermer la connexion

```python
con.close()
```

### À vous de jouer

Quelques questions pour continuer l'exploration :

1. Quelle équipe a le meilleur pourcentage de victoires à domicile depuis 2000 ?
2. Le nombre moyen de points par match a-t-il toujours augmenté ? Repérez les
   périodes de baisse.
3. L'avantage du terrain est-il plus fort en playoffs qu'en saison régulière ?
4. Quel est le match avec le plus grand écart de points de l'histoire ?

---

## Et ensuite ?

Le projet proprement dit est décrit dans [SCENARIO.md](SCENARIO.md) :
téléchargement des statistiques individuelles avec `nba_api`, puis construction
et comparaison de trois modèles de performance offensive.

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
