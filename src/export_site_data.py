import json
import os

import numpy as np
from sklearn.model_selection import train_test_split

from predict import build_features, load_model, load_table

OUTPUT_PATH = "docs/data/players.json"
POSITIONS = {"Attack": "Forward", "Midfield": "Midfielder", "Defender": "Defender"}

table = load_table()
model = load_model()

# Predict every player-season with the saved model
X = build_features(table, model)
table["predicted"] = np.exp(model.predict(X))

# Same split as train_model.py, so the site can say which seasons the model never saw
X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
table["is_test"] = table.index.isin(X_test.index)

test = table[table["is_test"]]
errors = (test["predicted"] - test["market_value"]).abs()
metrics = {
    "player_seasons": len(table),
    "players": int(table["player_id"].nunique()),
    "test_seasons": len(test),
    "median_error": round(float(errors.median())),
    "mean_error": round(float(errors.mean())),
    "first_season": int(table["season"].min()),
    "last_season": int(table["season"].max()),
}

# % change in value for +1 of each feature (minutes shown per 90)
effects = {}
for name, weight in zip(model.feature_names_in_, model.coef_):
    step = 90 if name == "minutes" else 1
    effects[name] = round(float((np.exp(weight * step) - 1) * 100), 1)

players = []
for player_id, rows in table.sort_values("season").groupby("player_id"):
    players.append({
        "id": int(player_id),
        "name": rows["name"].iloc[0],
        "position": POSITIONS[rows["position"].iloc[-1]],
        # One list per season, kept short to keep the file small
        "seasons": [
            [int(r.season), int(r.age), int(r.games), int(r.minutes), int(r.goals), int(r.assists),
             int(r.market_value), int(round(r.predicted, -4)), bool(r.is_test)]
            for r in rows.itertuples()
        ],
    })

site_data = {
    "metrics": metrics,
    "effects": effects,
    "season_fields": ["season", "age", "games", "minutes", "goals", "assists",
                      "market_value", "predicted", "is_test"],
    "players": players,
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(site_data, f, ensure_ascii=False, separators=(",", ":"))

print(f"Wrote {len(players)} players, {len(table)} seasons to {OUTPUT_PATH}")
print(metrics)
