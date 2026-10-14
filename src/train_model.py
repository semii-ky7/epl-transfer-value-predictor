import os

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

table = pd.read_csv("data/processed/player_seasons_clean.csv")

features = ["age", "season", "games", "minutes", "goals", "assists", "height_in_cm", "position"]

X = table[features]
y = table["market_value"]

X = pd.get_dummies(X, columns=["position"], drop_first=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

pd.set_option("display.float_format", "{:,.0f}".format)

weights = pd.Series(model.coef_, index=X.columns)
print(weights)
print("Starting number (intercept):", f"{model.intercept_:,.0f}")

predictions = model.predict(X_test)

results = table.loc[X_test.index, ["name", "season", "age", "goals"]]
results["actual"] = y_test
results["predicted"] = predictions
results["gap"] = results["predicted"] - results["actual"]

print(results.head(10))
print("Negative predictions:", (predictions < 0).sum())
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)
train_r2 = model.score(X_train, y_train)

print("--- baseline model ---")
print(f"MAE: €{mae:,.0f}")
print(f"Test R²: {r2:.3f}")
print(f"Train R²: {train_r2:.3f}")

y_train_log = np.log(y_train)

model_log = LinearRegression()
model_log.fit(X_train, y_train_log)

predictions_log = model_log.predict(X_test)
print("--- log model ---")
print(predictions_log[:5])

predictions_back = np.exp(predictions_log)

mae_log = mean_absolute_error(y_test, predictions_back)
r2_log = r2_score(y_test, predictions_back)

print(f"MAE: €{mae_log:,.0f}")
print(f"Test R²: {r2_log:.3f}")
print("Negative predictions:", (predictions_back < 0).sum())

comparison = table.loc[X_test.index, ["name", "season", "age"]]
comparison["actual"] = y_test
comparison["baseline"] = predictions
comparison["log_model"] = predictions_back

print("--- 10 typical test players ---")
print(comparison.head(10))

print("--- 5 most valuable test players ---")
print(comparison.sort_values("actual", ascending=False).head(5))

median_err_base = (comparison["baseline"] - comparison["actual"]).abs().median()
median_err_log = (comparison["log_model"] - comparison["actual"]).abs().median()
print(f"Median error - baseline: €{median_err_base:,.0f}")
print(f"Median error - log model: €{median_err_log:,.0f}")

weights_log = pd.Series(model_log.coef_, index=X.columns)
percent_change = (np.exp(weights_log) - 1) * 100

print("--- log model: % change in value per +1 of each feature ---")
print(percent_change.round(1))

os.makedirs("models", exist_ok=True)
joblib.dump(model_log, "models/value_model.joblib")
print("Saved model to models/value_model.joblib")