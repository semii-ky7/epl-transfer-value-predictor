import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv

URL = "https://api.football-data.org/v4/competitions/PL/teams"
OUTPUT_PATH = "data/raw/pl_squads_current.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class SquadFetchError(Exception):
    """Raised when the squads can't be fetched from football-data.org."""


def get_api_key():
    """Read the API key from .env (or the environment)."""
    load_dotenv()
    key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not key or key == "your-key-here":
        raise SquadFetchError(
            "No API key found. Copy .env.example to .env and add your football-data.org key."
        )
    return key


def fetch_teams(key):
    """Download every current Premier League team, including squads, as a list of dicts."""
    try:
        response = requests.get(URL, headers={"X-Auth-Token": key}, timeout=10)
    except requests.RequestException as err:
        raise SquadFetchError(f"Couldn't reach football-data.org: {err}") from err

    if response.status_code == 429:
        raise SquadFetchError("Rate limit hit (10 requests a minute on the free tier). Wait a minute.")
    if response.status_code != 200:
        # The API explains most errors, e.g. an invalid token, in a "message" field
        try:
            message = response.json().get("message", response.reason)
        except ValueError:
            message = response.reason
        raise SquadFetchError(f"football-data.org returned {response.status_code}: {message}")

    return response.json()["teams"]


def squads_to_table(teams):
    """Flatten the nested JSON into one row per player."""
    rows = []
    for team in teams:
        for player in team.get("squad", []):
            rows.append({
                "team": team["name"],
                "name": player["name"],
                "position": player.get("position"),
                "date_of_birth": player.get("dateOfBirth"),
                "nationality": player.get("nationality"),
            })
    return pd.DataFrame(rows)


def main():
    try:
        teams = fetch_teams(get_api_key())
    except SquadFetchError as err:
        logger.error(err)
        return

    squads = squads_to_table(teams)
    os.makedirs("data/raw", exist_ok=True)
    squads.to_csv(OUTPUT_PATH, index=False)
    logger.info("Saved %d players from %d teams to %s", len(squads), len(teams), OUTPUT_PATH)

    # How many of today's PL players does the model already know?
    known = set(pd.read_csv("data/processed/player_seasons_clean.csv")["name"])
    matched = squads["name"].isin(known).sum()
    logger.info("%d of %d current squad players are in the model's data", matched, len(squads))


if __name__ == "__main__":
    main()
