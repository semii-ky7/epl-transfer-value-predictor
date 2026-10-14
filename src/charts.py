import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from sklearn.model_selection import train_test_split

from predict import build_features, load_model, load_table

# Shows axis ticks as €1m, €10m, €100m instead of 10^6, 10^7, 10^8
millions = FuncFormatter(lambda value, _: f"€{value / 1_000_000:g}m")

table = load_table()
model = load_model()

# Same split as train_model.py, so these are the 847 players the model never saw
X = build_features(table, model)
y = table["market_value"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

test = table.loc[X_test.index, ["name", "season", "age", "goals"]]
test["actual"] = y_test
test["predicted"] = np.exp(model.predict(X_test))

os.makedirs("charts", exist_ok=True)

# Predicted vs actual: dots on the diagonal are perfect predictions.
# Both axes are logarithmic so €1m and €100m players are equally readable.
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(test["actual"], test["predicted"], alpha=0.35, s=14)
low, high = 3e5, 3e8
ax.plot([low, high], [low, high], color="black", linestyle="--", linewidth=1, label="Perfect prediction")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(low, high)
ax.set_ylim(low, high)
ax.xaxis.set_major_formatter(millions)
ax.yaxis.set_major_formatter(millions)
ax.set_xlabel("Actual market value (€, log scale)")
ax.set_ylabel("Predicted market value (€, log scale)")
ax.set_title("Predicted vs actual value — 847 test player-seasons")
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("charts/predicted_vs_actual.png", dpi=150)
plt.close(fig)

# Residuals: actual ÷ predicted for each player.
# 1× means spot on, above 1× the model under-valued him, below 1× it over-valued him.
test["ratio"] = test["actual"] / test["predicted"]

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(test["actual"], test["ratio"], alpha=0.35, s=14)
ax.axhline(1, color="black", linestyle="--", linewidth=1, label="Spot on")
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_formatter(millions)
ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}×"))
ax.set_xlabel("Actual market value (€, log scale)")
ax.set_ylabel("Actual ÷ predicted (log scale)")
ax.set_title("Residuals — the model over-values cheap players and under-values stars")
ax.text(0.02, 0.95, "Above the line: model under-valued", transform=ax.transAxes, va="top")
ax.text(0.02, 0.05, "Below the line: model over-valued", transform=ax.transAxes, va="bottom")
fig.tight_layout()
fig.savefig("charts/residuals.png", dpi=150)
plt.close(fig)
