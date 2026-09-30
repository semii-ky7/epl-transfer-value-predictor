import pandas as pd

players = pd.read_csv("practice/players.csv")
stats = pd.read_csv("practice/stats.csv")

print("--- players ---")
print(players)
print("--- stats ---")
print(stats)
print("--- task 2 ---")
print(stats.shape)
print(stats.dtypes)

print("--- task 3 ---")
goals = stats["goals"]
print(goals)
print(type(goals))

print("--- task 4 ---")
print(players[players["age"] > 24])

print("--- task 5 ---")
print(players[players["name"] == "Haaland"][["name", "age"]])

print("--- task 6 ---")
goals = stats["goals"]
assists = stats["assists"]
stats["contributions"] = goals + assists
print(stats)

print("--- task 7 ---")
total_goals = stats.groupby("player_id")["goals"].sum()
print(total_goals)

print("--- task 8 ---")
merged = pd.merge(stats, players, on="player_id")
print(merged)
print(merged.shape)

print("--- task 9 ---")
totals= merged.groupby("name")["contributions"].sum()
print(totals)
sorted_totals = totals.sort_values(ascending=False)
print(sorted_totals)