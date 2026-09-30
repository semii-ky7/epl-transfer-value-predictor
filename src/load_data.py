import pandas as pd
import os

files=["players.csv", "appearances.csv", "player_valuations.csv", "games.csv", "competitions.csv", "clubs.csv"]

for file in files:
    path="data/raw/"+file
    df=pd.read_csv(path)
    print(file)
    print(df.shape)
    print(df.columns)
    print()


appearances = pd.read_csv("data/raw/appearances.csv")
pl=appearances[appearances["competition_id"]=="GB1"]
print(appearances.shape)
print(pl.shape)
os.makedirs("data/processed", exist_ok=True)
pl.to_csv("data/processed/pl_appearances.csv", index=False)