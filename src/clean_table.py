import pandas as pd

table=pd.read_csv("data/processed/player_seasons.csv")
print(table.shape)
print(table.isna().sum())


table=table[table["position"] != "Goalkeeper"]
print(table.shape)
# Keep players with 900+ minutes (10 full games) - fewer gives noisy stats
table=table[table["minutes"] >= 900]
print(table.shape)
print(table.isna().sum())
# market_value: drop - it's the target, never invent answers
# market_value: drop - it's the target, never invent answers
# age: drop - it's a key driver of value and only 3 rows are missing
# foot: drop - can't average left/right, and guessing would often be wrong
table = table.dropna(subset=["market_value", "age", "foot"])

# height_in_cm: fill with median - barely affects value, keeps 15 real seasons
table["height_in_cm"] = table["height_in_cm"].fillna(table["height_in_cm"].median())

print(table.shape)
print(table.isna().sum())

cols = ["name", "season", "age", "position", "goals", "market_value"]

print("--- top 10 ---")
print(table.sort_values("market_value", ascending=False).head(10)[cols])

print("--- bottom 10 ---")
print(table.sort_values("market_value").head(10)[cols])

table.to_csv("data/processed/player_seasons_clean.csv", index=False)