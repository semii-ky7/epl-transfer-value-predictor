import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split

table = pd.read_csv("data/processed/player_seasons_clean.csv")

features = ["age", "season", "games", "minutes", "goals", "assists", "height_in_cm", "position"]

X = table[features]
y = table["market_value"]

X = pd.get_dummies(X, columns=["position"], drop_first=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# print(X_train.shape, X_test.shape)
# print(y_train.shape, y_test.shape)

# print(X.shape)
# print(y.shape)
# print(X.head())

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