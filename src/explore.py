import pandas as pd
import matplotlib.pyplot as plt
import os

pd.set_option("display.float_format", "{:,.0f}".format)

table=pd.read_csv("data/processed/player_seasons_clean.csv")

cols = ["age", "games", "minutes", "goals", "assists", "height_in_cm", "market_value"]

print(table[cols].describe())

os.makedirs("charts", exist_ok=True)

plt.hist(table["market_value"], bins=50)
plt.title("Distribution of market value")
plt.xlabel("Market value (€)")
plt.ylabel("Number of player-seasons")
plt.savefig("charts/market_value_hist.png")
plt.close()

plt.scatter(table["goals"], table["market_value"], alpha=0.3)
plt.title("Goals vs market value")
plt.xlabel("Goals in season")
plt.ylabel("Market value (€)")
plt.savefig("charts/goals_vs_value.png")
plt.close()