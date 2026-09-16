"""Train an occupancy classifier from historical smart-home telemetry.

CSV columns: temperature,motion,light,sound,hour,occupied
"""
import argparse
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

FEATURES = ["temperature", "motion", "light", "sound", "hour"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="Training CSV")
    parser.add_argument("--output", default="occupancy_model.joblib")
    args = parser.parse_args()

    df = pd.read_csv(args.csv).dropna(subset=FEATURES + ["occupied"])
    X, y = df[FEATURES], df["occupied"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    print(classification_report(y_test, model.predict(X_test)))
    joblib.dump(model, args.output)
    print(f"Saved model to {args.output}")


if __name__ == "__main__":
    main()
