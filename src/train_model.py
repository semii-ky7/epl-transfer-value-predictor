import pandas as pd
from sklearn.model_selection import train_test_split

table = pd.read_csv("data/processed/player_seasons_clean.csv")

features = ["age", "season", "games", "minutes", "goals", "assists", "height_in_cm", "position"]

X = table[features]
y = table["market_value"]

X = pd.get_dummies(X, columns=["position"], drop_first=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(X_train.shape, X_test.shape)
print(y_train.shape, y_test.shape)

print(X.shape)
print(y.shape)
print(X.head())