import difflib

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
    """Return every season for the best match for name, or None if nothing matches.

    Tries, in order: the exact name ignoring case ("bukayo saka"), names that
    contain the text ("saka"), then the closest spelling ("Bukayo Sakaa").
    """
    query = name.strip().lower()
    if not query:
        return None
    lower_names = table["name"].str.lower()

    exact = table[lower_names == query]
    if not exact.empty:
        return exact

    partial = table[lower_names.str.contains(query, regex=False)]
    if partial["name"].nunique() == 1:
        return partial
    if partial["name"].nunique() > 1:
        options = ", ".join(sorted(partial["name"].unique())[:5])
        print(f"'{name}' matches several players: {options}")
        return None

    # cutoff=0.8 means the spelling must be at least 80% similar
    close = difflib.get_close_matches(query, lower_names.unique(), n=1, cutoff=0.8)
    if close:
        match = table[lower_names == close[0]]
        print(f"No exact match for '{name}', showing {match['name'].iloc[0]}")
        return match
    return None


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


def euros(value):
    """Format a euro amount in millions, e.g. 56923216 -> '€56.9m'."""
    return f"€{value / 1_000_000:,.1f}m"


def show_player(result):
    """Print every season, then a one-line verdict on the latest one."""
    print(f"\n{result['name'].iloc[0]}")
    for _, row in result.iterrows():
        print(f"  {row['season']}  age {row['age']:.0f}  {row['goals']:>2} goals  "
              f"actual {euros(row['market_value']):>8}  predicted {euros(row['predicted']):>8}")

    latest = result.iloc[-1]
    if latest["gap"] < 0:
        verdict = f"under-valued by the model by {euros(-latest['gap'])}"
    else:
        verdict = f"over-valued by the model by {euros(latest['gap'])}"
    print(f"Latest season ({latest['season']}): {verdict}")


def main():
    model = load_model()
    table = load_table()
    print("Type a player's name, or q to quit.")

    while True:
        name = input("\nEnter a player: ")
        if name.strip().lower() == "q":
            break
        rows = find_player(name, table)
        if rows is not None:
            show_player(predict_values(rows, model))


if __name__ == "__main__":
    main()
