import pandas as pd

apps=pd.read_csv("data/processed/pl_appearances.csv")
games=pd.read_csv("data/raw/games.csv")
players=pd.read_csv("data/raw/players.csv")

games=games[["game_id",  "season"]]
apps=pd.merge(apps,games,on="game_id")

#print(apps.shape)
#print(apps.head())

season_stats = apps.groupby(["player_id", "season"]).agg(
    games=("appearance_id", "count"),
    minutes=("minutes_played", "sum"),
    goals=("goals", "sum"),
    assists=("assists", "sum"),
    yellow_cards=("yellow_cards", "sum"),
    red_cards=("red_cards", "sum"),
).reset_index()

#print(season_stats.shape)
#print(season_stats.head())

players=players[["player_id", "name", "date_of_birth", "position", "sub_position", "height_in_cm", "foot"]]
table=pd.merge(season_stats,players, on="player_id")
#print(table.shape)
#print(table.head())

table["date_of_birth"] = pd.to_datetime(table["date_of_birth"])

table["season_start"] = pd.to_datetime(table["season"].astype(str) + "-09-01")

table["age"] = ((table["season_start"] - table["date_of_birth"]).dt.days / 365.25) // 1

#print(table[["name", "season", "date_of_birth", "age"]].head())

vals = pd.read_csv("data/raw/player_valuations.csv")
vals["date"] = pd.to_datetime(vals["date"])
vals["season"] = vals["date"].dt.year - (vals["date"].dt.month < 7)

vals = vals.sort_values("date")

season_values = vals.groupby(["player_id", "season"]).agg(
    market_value=("market_value_in_eur", "last"),
).reset_index()

table = pd.merge(table, season_values, on=["player_id", "season"], how="left")

#print(table.shape)
#print(table["market_value"].isna().sum())
cols = ["name", "season", "age", "games", "goals", "assists", "market_value"]

print(table[table["name"] == "Erling Haaland"][cols])
print(table[table["name"] == "Bukayo Saka"][cols])
print(table[table["name"] == "Mohamed Salah"][cols])

table.to_csv("data/processed/player_seasons.csv", index=False)