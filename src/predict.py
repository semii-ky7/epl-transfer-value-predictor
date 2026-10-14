import joblib
import pandas as pd

MODEL_PATH = "models/value_model.joblib"
TABLE_PATH = "data/processed/player_seasons_clean.csv"


def load_model(path=MODEL_PATH):
    """Load the trained log model saved by train_model.py."""
    return joblib.load(path)


def load_table(path=TABLE_PATH):
    """Load the clean player-season table."""
    return pd.read_csv(path)


def find_player(name, table):
    """Return every season for the player with this exact name."""
    return table[table["name"] == name]


if __name__ == "__main__":
    model = load_model()
    table = load_table()
    print(find_player("Bukayo Saka", table)[["name", "season", "goals", "market_value"]])
