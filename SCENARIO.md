# Scénario du projet — Comparer la performance offensive individuelle en NBA

> **Prérequis :** avoir suivi [INSTALLATION.md](INSTALLATION.md) (environnement Python,
> accès Kaggle, base `nba.sqlite`).

---

## 0. La question de départ

> **Qui est le meilleur joueur offensif de la NBA ?**

La question paraît simple. Pourtant, pour y répondre, il faut d'abord répondre
à une autre question : **meilleur par rapport à qui ?**

- Un joueur qui marque 25 points en 38 minutes est-il meilleur qu'un remplaçant
  qui en marque 12 en 15 minutes ?
- Marquer 20 points en 2014 vaut-il la même chose qu'en 2023, alors que le jeu
  s'est accéléré et que le tir à 3 points a explosé ?
- Peut-on comparer un pivot, dont le rôle est de finir près du panier, à un
  meneur, dont le rôle est de créer pour les autres ?
- Un joueur est-il aussi performant à l'extérieur qu'à domicile ?

Dans ce projet, nous allons construire **trois modèles** qui répondent chacun
différemment à la question « par rapport à qui ? », puis les **comparer**.

| Modèle | Méthode | Population de référence |
|---|---|---|
| 1 | **Percentile** : « mieux que X % des joueurs » | tous les joueurs de la même saison |
| 2 | **Z-score** : « X écarts-types au-dessus de la moyenne » | tous les joueurs de la même saison |
| 3 | Percentile (3a) et z-score (3b) | joueurs du **même poste**, de la **même saison**, dans le **même lieu** (domicile ou extérieur) |

Les modèles 1 et 2 diffèrent par la **méthode de calcul**. Le modèle 3 change la
**population de référence**. On peut donc lire le projet comme un tableau 2 × 2 :

|  | Référence : toute la saison | Référence : poste × saison × lieu |
|---|---|---|
| **Percentile** | modèle 1 | modèle 3a |
| **Z-score** | modèle 2 | modèle 3b |

---

## 1. Trouver les bonnes données

### 1.1 Ce que la base Kaggle ne permet pas de faire

La base `nba.sqlite` installée à l'étape précédente est très riche, mais elle a
trois limites pour notre question :

| Besoin | Ce que contient la base Kaggle | Problème |
|---|---|---|
| Statistiques **par joueur** et par match | La table `game` est au niveau des **équipes** | Impossible de savoir qui a marqué |
| **Minutes jouées** | Le `play_by_play` liste les actions des joueurs depuis 1996 | Reconstituer les minutes à partir des remplacements est long et risqué |
| **Poste** de chaque joueur | `common_player_info` donne un seul poste par joueur | Il manque le poste de 120 joueurs sur 539 en 2022-23, dont **LeBron James** et **Joel Embiid**, et le poste ne change pas d'une saison à l'autre |

> **À retenir :** un jeu de données réputé « complet » ne l'est jamais pour
> toutes les questions. Il faut d'abord vérifier qu'il contient ce dont **votre**
> question a besoin.

### 1.2 La solution : l'API officielle de la NBA (`nba_api`)

La bibliothèque `nba_api` interroge le site de statistiques officiel de la NBA.
Nous utilisons deux sources :

| Source | Contenu | Coût |
|---|---|---|
| `LeagueGameLog` | une ligne **par joueur et par match** : minutes, points, tirs, passes, balles perdues, adversaire, lieu… | 1 requête par saison |
| `CommonTeamRoster` | l'effectif de chaque équipe avec le **poste de chaque joueur pour cette saison** | 30 requêtes par saison (une par équipe) |

**Période retenue : de 2013-14 à 2022-23 (10 saisons).**

- 10 saisons, c'est assez pour étudier l'évolution du jeu et la stabilité des
  modèles d'une année sur l'autre.
- Cette période est couverte **aussi** par la base Kaggle, ce qui permet de
  **vérifier** les données (section 2).

### 1.3 Télécharger les données

Depuis le dossier du projet, environnement activé :

```bash
python scripts/telecharger_saisons.py
```

Le script met **environ 5 minutes** et crée 20 fichiers dans `data/nba_api/` :

```
data/nba_api/
├── player_gamelog_2013-14.csv   ← feuilles de match individuelles
├── rosters_2013-14.csv          ← effectifs et postes
├── ...
├── player_gamelog_2022-23.csv
└── rosters_2022-23.csv
```

Si le téléchargement s'interrompt (coupure réseau, serveur NBA qui ne répond pas),
**relancez simplement le script** : les fichiers déjà téléchargés sont conservés.

Ouvrez le script `scripts/telecharger_saisons.py` et lisez-le : il est commenté et
court. Vous devez comprendre ce qu'il fait avant d'utiliser ses résultats.

---

## 2. Vérifier les données avant de les utiliser

**Pourquoi ?** Une donnée fausse produit une conclusion fausse, sans aucun
message d'erreur. Avant toute analyse, on confronte la nouvelle source à une
source indépendante.

**Le test :** pour chaque match, la somme des points des joueurs d'une équipe
doit être égale au score de cette équipe dans la base Kaggle.

Créez un fichier `analyse.py` et commencez par :

```python
import sqlite3
from pathlib import Path

import pandas as pd

DOSSIER = Path("data/nba_api")
SAISONS = [f"{a}-{str(a + 1)[-2:]}" for a in range(2013, 2023)]   # "2013-14", ..., "2022-23"

con = sqlite3.connect("data/basketball/nba.sqlite")

for annee, saison in zip(range(2013, 2023), SAISONS):
    logs = pd.read_csv(DOSSIER / f"player_gamelog_{saison}.csv", dtype={"GAME_ID": str})
    logs["domicile"] = logs["MATCHUP"].str.contains(" vs. ")
    points = logs.groupby(["GAME_ID", "domicile"])["PTS"].sum().unstack()

    ref = pd.read_sql(
        f"SELECT game_id, pts_home, pts_away FROM game WHERE season_id = '2{annee}'", con
    ).set_index("game_id")
    comparaison = ref.join(points, how="inner")
    ecarts = ((comparaison["pts_home"] != comparaison[True])
              | (comparaison["pts_away"] != comparaison[False])).sum()
    print(f"{saison} : {len(comparaison)} matchs comparés, {ecarts} écart(s)")
```

Résultat attendu : **0 écart** pour chaque saison.

```
2013-14 : 1230 matchs comparés, 0 écart(s)
...
2019-20 : 1059 matchs comparés, 0 écart(s)
2020-21 : 1080 matchs comparés, 0 écart(s)
...
```

> **Question :** pourquoi 2019-20 et 2020-21 comptent-elles moins de matchs que les
> autres saisons ? (Indice : mars 2020.) Quelles conséquences pour la suite ?

---

## 3. Préparer les données

À partir de cette section, mettez de côté le code de vérification et repartez
d'un fichier propre (`modeles.py`) qui reprend les imports et constantes de la
section 2.

### 3.1 Charger les 10 saisons

```python
logs = []
for saison in SAISONS:
    df = pd.read_csv(DOSSIER / f"player_gamelog_{saison}.csv")
    df["saison"] = saison
    logs.append(df)
logs = pd.concat(logs, ignore_index=True)

postes = []
for saison in SAISONS:
    df = pd.read_csv(DOSSIER / f"rosters_{saison}.csv")
    df["saison"] = saison
    postes.append(df[["saison", "PLAYER_ID", "POSITION"]])
postes = pd.concat(postes).drop_duplicates(["saison", "PLAYER_ID"])

print(len(logs))   # 253404
```

### 3.2 Nettoyer et enrichir

```python
# 1. Retirer les lignes à 0 minute : le joueur était sur la feuille de match mais n'a pas joué.
logs = logs[logs["MIN"] > 0]

# 2. Déduire le lieu de la colonne MATCHUP : "BOS vs. PHI" = domicile, "BOS @ PHI" = extérieur.
logs["lieu"] = logs["MATCHUP"].str.contains(" vs. ").map({True: "domicile", False: "exterieur"})

# 3. Regrouper les postes en 3 catégories, d'après la première lettre.
postes["poste"] = postes["POSITION"].str[0].map({"G": "Arrière", "F": "Ailier", "C": "Pivot"})
```

**Pourquoi 3 postes ?** La NBA utilise des postes hybrides (`G-F`, `F-C`, `C-F`…).
Les garder tous créerait des groupes trop petits pour le modèle 3. On retient la
**première lettre**, qui correspond au poste principal : `F-C` devient Ailier,
`C-F` devient Pivot. C'est une **convention** : elle est discutable, mais elle
doit être annoncée.

### 3.3 Choisir les indicateurs offensifs

« Performance offensive » ne veut pas dire « points marqués ». Nous retenons
quatre indicateurs :

| Indicateur | Formule | Ce qu'il mesure | Sens |
|---|---|---|---|
| `pts_36` | points / minutes × 36 | volume de points | plus = mieux |
| `ts_pct` | points / (2 × (tirs tentés + 0,44 × lancers francs tentés)) | **efficacité** au tir (*true shooting*), qui tient compte des 3 points et des lancers francs | plus = mieux |
| `ast_36` | passes décisives / minutes × 36 | création pour les coéquipiers | plus = mieux |
| `tov_36` | balles perdues / minutes × 36 | possessions gâchées | **moins = mieux** |

**Pourquoi ramener à 36 minutes ?** Sans cela, on mesure surtout le **temps de
jeu**. Un titulaire qui joue 36 minutes marquera presque toujours plus qu'un
remplaçant qui en joue 15, même s'il est moins efficace. 36 minutes est la
convention habituelle (l'équivalent d'un match d'un titulaire).

**Pourquoi 0,44 dans le *true shooting* ?** Toutes les séries de lancers francs ne
consomment pas une possession (lancers francs « bonus » après un panier, fautes
techniques…). Le coefficient 0,44 est l'estimation empirique couramment utilisée.

```python
STATS = ["MIN", "PTS", "FGA", "FTA", "AST", "TOV"]
INDICATEURS = ["pts_36", "ts_pct", "ast_36", "tov_36"]
SENS = {"pts_36": 1, "ts_pct": 1, "ast_36": 1, "tov_36": -1}   # -1 : plus petit = meilleur


def calculer_indicateurs(df):
    df = df.copy()
    df["pts_36"] = df["PTS"] / df["MIN"] * 36
    df["ast_36"] = df["AST"] / df["MIN"] * 36
    df["tov_36"] = df["TOV"] / df["MIN"] * 36
    df["ts_pct"] = df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"]))
    return df
```

### 3.4 Choisir l'unité d'analyse et le seuil

**Unité :** on additionne les statistiques de chaque joueur **sur toute la
saison**, puis on calcule les indicateurs. On obtient une ligne par
**joueur × saison**. Un joueur transféré en cours de saison garde une seule
ligne, toutes équipes confondues.

**Seuil : au moins 500 minutes dans la saison.** Sans seuil, un joueur qui a joué
2 matchs et marqué 30 points se retrouve tout en haut du classement. Avec
**un petit échantillon, les valeurs extrêmes sont dues au hasard**, pas au talent.
500 minutes, c'est environ 6 matchs complets, ou une demi-saison d'un remplaçant
régulier.

```python
par_saison = logs.groupby(["saison", "PLAYER_ID", "PLAYER_NAME"])[STATS].sum().reset_index()
par_saison = calculer_indicateurs(par_saison)
par_saison = par_saison.merge(postes[["saison", "PLAYER_ID", "poste"]],
                              on=["saison", "PLAYER_ID"], how="left")
par_saison = par_saison[(par_saison["MIN"] >= 500) & par_saison["poste"].notna()]

print(len(par_saison))   # 3530 joueurs-saisons
```

> **Questions :**
> - Combien de joueurs-saisons sont exclus parce que leur poste est inconnu ?
>   Qui sont-ils ? Pourquoi n'apparaissent-ils dans aucun effectif ?
> - Un seuil fixe de 500 minutes est-il juste pour les saisons 2019-20 et 2020-21,
>   plus courtes ? Proposez une alternative.

---

## 4. Modèle 1 — Le percentile

### Principe

Le percentile d'un joueur, c'est **la proportion de joueurs qu'il dépasse**. Un
percentile de 0,90 sur les points par 36 minutes signifie : « il marque plus que
90 % des joueurs de la saison ».

On calcule le percentile de chaque indicateur **au sein de la saison**, puis on
fait la **moyenne des quatre percentiles** pour obtenir un score sur 100. Pour les
balles perdues, on inverse le classement : perdre peu de ballons donne un
percentile élevé.

### Code

```python
def score_percentile(df, groupes):
    percentiles = pd.DataFrame(index=df.index)
    for indicateur in INDICATEURS:
        percentiles[indicateur] = df.groupby(groupes)[indicateur].rank(
            pct=True, ascending=(SENS[indicateur] == 1)
        )
    return percentiles.mean(axis=1) * 100


par_saison["m1_percentile"] = score_percentile(par_saison, ["saison"])
```

### Pourquoi cette méthode

- **Facile à comprendre**, même pour un non-statisticien.
- **Robuste** : une valeur extrême ne déforme pas l'échelle. Que le meilleur
  marqueur marque 30 ou 40 points, il reste au 100e percentile.
- Fonctionne quelle que soit la **forme de la distribution**.

### Ses limites

- Il **écrase les écarts** : le 1er et le 2e sont séparés de la même distance que
  le 150e et le 151e, même si l'écart réel entre les deux premiers est énorme.
- Faire la moyenne de percentiles **resserre les scores** : en 2022-23, le meilleur
  score est d'environ 81 sur 100, pas 100. Il est très difficile d'être premier
  sur les quatre indicateurs à la fois.

---

## 5. Modèle 2 — Le z-score

### Principe

Le z-score mesure **à combien d'écarts-types de la moyenne** se trouve un joueur :

> z = (valeur du joueur − moyenne de la saison) / écart-type de la saison

Un z-score de +2 signifie « nettement au-dessus de la moyenne », 0 « dans la
moyenne », −1 « en dessous ». On multiplie par −1 le z-score des balles perdues,
puis on fait la **moyenne des quatre z-scores**.

### Code

```python
def score_z(df, groupes):
    z = pd.DataFrame(index=df.index)
    for indicateur in INDICATEURS:
        groupe = df.groupby(groupes)[indicateur]
        z[indicateur] = ((df[indicateur] - groupe.transform("mean"))
                         / groupe.transform("std") * SENS[indicateur])
    return z.mean(axis=1)


par_saison["m2_zscore"] = score_z(par_saison, ["saison"])
```

`transform` renvoie, pour **chaque ligne**, la moyenne (ou l'écart-type) de son
groupe. C'est ce qui permet de soustraire la moyenne de la saison à chaque joueur.

### Pourquoi cette méthode

- Elle **conserve les écarts** : un joueur exceptionnel obtient un z-score
  nettement plus élevé que le deuxième, ce qui n'est pas le cas avec un percentile.
- Les z-scores ont tous **la même échelle**, ce qui permet d'additionner des
  indicateurs aux unités différentes (des points, un pourcentage, des passes).

### Ses limites

- Le z-score suppose implicitement une distribution **à peu près symétrique**.
  Or les points par 36 minutes ont une distribution **asymétrique** (beaucoup de
  joueurs moyens, quelques stars très au-dessus) : l'asymétrie vaut environ 0,8.
  Les meilleurs marqueurs obtiennent donc des z-scores très élevés, qui peuvent
  dominer le score composite.
- La moyenne et l'écart-type sont **sensibles aux valeurs extrêmes**.

> **Pour aller plus loin :** le *z-score robuste* remplace la moyenne par la
> médiane et l'écart-type par l'écart absolu médian (MAD). Essayez-le.

---

## 6. Modèle 3 — Une référence au poste, par saison et par lieu

### Principe

Les modèles 1 et 2 comparent chaque joueur à **toute la saison**. Or un pivot et
un meneur n'ont pas le même rôle : le pivot tire près du panier (meilleure
efficacité au tir) mais fait peu de passes ; le meneur fait l'inverse. Les
comparer directement revient à pénaliser chacun sur ce qui n'est pas son rôle.

Le modèle 3 compare chaque joueur **aux joueurs du même poste, de la même saison,
dans le même lieu** (à domicile ou à l'extérieur). Les méthodes de calcul ne
changent pas : on réutilise `score_percentile` (3a) et `score_z` (3b), seuls les
**groupes** changent.

### Code

On construit d'abord une table **joueur × saison × lieu**, restreinte aux
joueurs retenus à la section 3.4 (pour comparer les modèles sur la même
population) :

```python
par_lieu = logs.groupby(["saison", "PLAYER_ID", "PLAYER_NAME", "lieu"])[STATS].sum().reset_index()
par_lieu = calculer_indicateurs(par_lieu)
par_lieu = par_lieu.merge(par_saison[["saison", "PLAYER_ID", "poste"]], on=["saison", "PLAYER_ID"])

GROUPES = ["saison", "poste", "lieu"]
print(par_lieu.groupby(GROUPES).size().describe())   # taille des groupes de référence

par_lieu["m3a_percentile"] = score_percentile(par_lieu, GROUPES)
par_lieu["m3b_zscore"] = score_z(par_lieu, GROUPES)
```

Chaque joueur a maintenant **deux** scores par saison (domicile et extérieur). Pour
le comparer aux modèles 1 et 2, on fait la moyenne des deux :

```python
m3 = par_lieu.groupby(["saison", "PLAYER_ID"])[["m3a_percentile", "m3b_zscore"]].mean().reset_index()
resultats = par_saison.merge(m3, on=["saison", "PLAYER_ID"])
```

### Pourquoi cette méthode

- **Poste :** on évalue chaque joueur par rapport à son rôle.
- **Saison :** on neutralise l'évolution du jeu (rythme, tirs à 3 points).
- **Lieu :** sur la période, l'équipe qui reçoit gagne environ 57 % des matchs. Si les joueurs
  sont aussi plus efficaces à domicile, un joueur qui a joué plus de matchs à
  domicile serait avantagé.

### Ses limites

- **Des groupes plus petits.** 10 saisons × 3 postes × 2 lieux = 60 groupes. Le
  plus petit (des pivots) ne compte qu'environ 40 joueurs, contre plus de 300 pour
  une saison entière. Plus le groupe est petit, moins la moyenne et l'écart-type
  de référence sont fiables.
- **Le poste est une étiquette simplifiée** (section 3.2) : Nikola Jokić est
  classé Pivot alors qu'il fait autant de passes qu'un meneur.
- **Des échantillons divisés par deux** : avec le découpage domicile/extérieur,
  certains joueurs n'ont qu'environ 170 minutes dans un lieu.

> **Questions :**
> - Comparez la médiane de `pts_36` et de `ts_pct` à domicile et à l'extérieur.
>   L'avantage du terrain existe-t-il au niveau **individuel** ? Est-il assez fort
>   pour justifier le découpage par lieu ?
> - Quel poste profite le plus du modèle 3 par rapport au modèle 1 ? Pourquoi ?

---

## 7. Comparer les modèles

Construire des modèles ne suffit pas : il faut savoir **ce qu'ils changent** et
**lequel est le plus pertinent**. Voici trois façons de les évaluer.

### 7.1 Les modèles classent-ils les joueurs de la même façon ?

On calcule la **corrélation de Spearman** entre les scores, c'est-à-dire la
corrélation entre les **rangs** (1 = classements identiques, 0 = aucun lien) :

```python
SCORES = ["m1_percentile", "m2_zscore", "m3a_percentile", "m3b_zscore"]
print(resultats[SCORES].corr(method="spearman").round(2))
```

Vous devriez trouver des corrélations **très élevées, autour de 0,95**. Les
modèles sont d'accord sur l'ensemble des 3 530 joueurs-saisons.

> **Question :** si les corrélations globales sont si élevées, les modèles
> sont-ils équivalents ? Regardez le **haut** du classement d'une saison :
> c'est là que les différences comptent.

```python
saison = resultats[resultats["saison"] == "2022-23"]
for score in SCORES:
    print(score, saison.nlargest(5, score)["PLAYER_NAME"].tolist())
```

### 7.2 Les modèles sont-ils stables d'une saison à l'autre ?

Le talent d'un joueur change peu d'une année à l'autre. Un bon modèle devrait
donc donner des scores **proches** pour un même joueur sur deux saisons
consécutives. Sinon, il mesure surtout du bruit.

```python
resultats["annee"] = resultats["saison"].str[:4].astype(int)
suivante = resultats[["PLAYER_ID", "annee"] + SCORES].copy()
suivante["annee"] -= 1
paires = resultats.merge(suivante, on=["PLAYER_ID", "annee"], suffixes=("", "_suivante"))

for score in SCORES:
    stabilite = paires[score].rank().corr(paires[f"{score}_suivante"].rank())
    print(f"{score} : {stabilite:.2f}")
```

Les quatre modèles ont une stabilité proche (environ 0,6).

### 7.3 Les modèles retrouvent-ils les meilleurs joueurs reconnus ?

Le **MVP** (meilleur joueur de la saison) est élu par des journalistes. Ce n'est
pas une vérité absolue, et ce n'est pas une récompense purement offensive, mais
c'est une **référence externe** utile pour vérifier que les modèles ont du sens.

```python
MVP = {
    "2013-14": "Kevin Durant", "2014-15": "Stephen Curry", "2015-16": "Stephen Curry",
    "2016-17": "Russell Westbrook", "2017-18": "James Harden",
    "2018-19": "Giannis Antetokounmpo", "2019-20": "Giannis Antetokounmpo",
    "2020-21": "Nikola Jokić", "2021-22": "Nikola Jokić", "2022-23": "Joel Embiid",
}

for score in SCORES:
    resultats[f"rang_{score}"] = resultats.groupby("saison")[score].rank(ascending=False)

mvp = resultats[resultats["PLAYER_NAME"] == resultats["saison"].map(MVP)]
print(mvp[["saison", "PLAYER_NAME"] + [f"rang_{s}" for s in SCORES]].to_string(index=False))
```

Vous devriez constater que :
- les modèles basés sur le **z-score** (2 et 3b) classent souvent le MVP dans
  le top 5, et même 1er à plusieurs reprises ;
- les modèles basés sur le **percentile** (1 et 3a) le classent plus bas ;
- **Russell Westbrook (2016-17)** et **Joel Embiid (2022-23)** sont mal classés
  par tous les modèles.

> **Questions :**
> - Pourquoi le z-score fait-il mieux que le percentile pour retrouver les MVP ?
>   (Relisez les limites de chaque méthode.)
> - Westbrook a réussi un triple-double de moyenne en 2016-17. Pourquoi nos
>   modèles le classent-ils si bas ? Regardez ses indicateurs un par un.
> - Embiid marque plus de 34 points par 36 minutes en 2022-23, l'un des deux
>   meilleurs totaux de la saison. Pourquoi n'est-il pas en tête ?
> - Nos quatre indicateurs ont le **même poids**. Est-ce raisonnable ? Que
>   se passe-t-il si on donne plus de poids aux points ?

---

## 8. Ce que vous devez rendre

1. **Le code** (`analyse.py`, `modeles.py` ou un notebook) : il doit tourner du
   début à la fin sans erreur.
2. **Un rapport** qui répond aux questions de ce scénario et présente :
   - vos choix (indicateurs, seuil, regroupement des postes) et **pourquoi** ;
   - le top 10 de chaque modèle pour au moins une saison ;
   - la comparaison des modèles (section 7) ;
   - **votre recommandation** : quel modèle utiliser, et pour quel usage ?
3. **Au moins une amélioration** de votre choix, par exemple :
   - un seuil de minutes proportionnel à la durée de la saison ;
   - un z-score robuste (médiane et MAD) ;
   - des pondérations différentes pour les indicateurs ;
   - d'autres indicateurs (tirs à 3 points, rebonds offensifs…) ;
   - une autre définition des postes.

> Il n'y a pas de « bon » modèle dans l'absolu. Un bon travail est un travail
> où **chaque choix est justifié** et où **les limites sont connues**.
