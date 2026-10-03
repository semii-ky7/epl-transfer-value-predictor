import pandas as pd

table = pd.read_csv("data/processed/player_seasons_clean.csv")

features = ["age", "season", "games", "minutes", "goals", "assists", "height_in_cm", "position"]

X = table[features]
y = table["market_value"]

print(X.shape)
print(y.shape)
print(X.head())