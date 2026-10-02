import pandas as pd


pd.set_option("display.float_format", "{:,.0f}".format)

table=pd.read_csv("data/processed/player_seasons_clean.csv")

cols = ["age", "games", "minutes", "goals", "assists", "height_in_cm", "market_value"]

print(table[cols].describe())