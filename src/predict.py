import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "models/value_model.joblib"
TABLE_PATH = "data/processed/player_seasons_clean.csv"

# Must match the features used in train_model.py
FEATURES = ["age", "season", "games", "minutes", "goals", "assists", "height_in_cm", "position"]


def load_model(path=MODEL_PATH):
    """Load the trained log model saved by train_model.py."""
    return joblib.load(path)


def load_table(path=TABLE_PATH):
    """Load the clean player-season table."""
    return pd.read_csv(path)


def find_player(name, table):
    """Return every season for the player with this exact name."""
    return table[table["name"] == name]


def predict_values(rows, model):
    """Add the model's predicted value and the gap to each season in rows."""
    X = pd.get_dummies(rows[FEATURES], columns=["position"])
    # A single player has one position, so get_dummies only makes that one column.
    # reindex adds any missing position columns (as False) in the order the model expects.
    X = X.reindex(columns=model.feature_names_in_, fill_value=False)

    result = rows[["name", "season", "age", "goals", "assists", "market_value"]].copy()
    result["predicted"] = np.exp(model.predict(X))
    result["gap"] = result["predicted"] - result["market_value"]
    return result.sort_values("season")


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:,.0f}".format)
    model = load_model()
    table = load_table()
    print(predict_values(find_player("Bukayo Saka", table), model))
