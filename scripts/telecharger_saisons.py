"""Télécharge depuis nba_api les données individuelles de plusieurs saisons.

Pour chaque saison régulière, deux fichiers sont créés dans data/nba_api/ :
- player_gamelog_<saison>.csv : une ligne par joueur et par match (minutes, points, tirs...)
- rosters_<saison>.csv        : les effectifs des 30 équipes, avec le poste de chaque joueur

Les fichiers déjà présents ne sont pas retéléchargés : en cas d'erreur réseau,
il suffit de relancer le script.

Utilisation (depuis le dossier du projet, environnement activé) :
    python scripts/telecharger_saisons.py               # 2013-14 à 2022-23
    python scripts/telecharger_saisons.py 2018 2022     # 2018-19 à 2022-23
"""

import sys
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import commonteamroster, leaguegamelog
from nba_api.stats.static import teams

DOSSIER = Path("data/nba_api")
PREMIERE_SAISON = 2013
DERNIERE_SAISON = 2022
PAUSE = 0.6        # secondes entre deux requêtes, pour ne pas surcharger le serveur NBA
ESSAIS = 3         # nombre de tentatives par requête


def nom_saison(annee):
    """2022 -> '2022-23'"""
    return f"{annee}-{str(annee + 1)[-2:]}"


def avec_essais(requete):
    """Exécute une requête nba_api, en réessayant si le serveur ne répond pas."""
    for essai in range(1, ESSAIS + 1):
        try:
            return requete()
        except Exception as erreur:
            if essai == ESSAIS:
                raise
            print(f"    échec ({erreur.__class__.__name__}), nouvel essai dans {5 * essai} s")
            time.sleep(5 * essai)


def telecharger_gamelog(saison):
    """Feuilles de match individuelles de toute la saison régulière (une seule requête)."""
    return avec_essais(lambda: leaguegamelog.LeagueGameLog(
        season=saison,
        season_type_all_star="Regular Season",
        player_or_team_abbreviation="P",
        timeout=60,
    ).get_data_frames()[0])


def telecharger_effectifs(saison):
    """Effectifs des 30 équipes (une requête par équipe), avec le poste de chaque joueur."""
    effectifs = []
    for equipe in teams.get_teams():
        effectif = avec_essais(lambda: commonteamroster.CommonTeamRoster(
            team_id=equipe["id"], season=saison, timeout=60,
        ).get_data_frames()[0])
        effectifs.append(effectif)
        time.sleep(PAUSE)
    return pd.concat(effectifs, ignore_index=True)


def main():
    premiere = int(sys.argv[1]) if len(sys.argv) > 1 else PREMIERE_SAISON
    derniere = int(sys.argv[2]) if len(sys.argv) > 2 else DERNIERE_SAISON
    DOSSIER.mkdir(parents=True, exist_ok=True)

    for annee in range(premiere, derniere + 1):
        saison = nom_saison(annee)
        print(f"Saison {saison}")

        fichier = DOSSIER / f"player_gamelog_{saison}.csv"
        if fichier.exists():
            print(f"  {fichier.name} existe déjà")
        else:
            gamelog = telecharger_gamelog(saison)
            gamelog.to_csv(fichier, index=False)
            print(f"  {fichier.name} : {len(gamelog)} lignes")
            time.sleep(PAUSE)

        fichier = DOSSIER / f"rosters_{saison}.csv"
        if fichier.exists():
            print(f"  {fichier.name} existe déjà")
        else:
            effectifs = telecharger_effectifs(saison)
            effectifs.to_csv(fichier, index=False)
            print(f"  {fichier.name} : {len(effectifs)} joueurs")


if __name__ == "__main__":
    main()
