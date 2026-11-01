"""Next-meal prediction from a meal history.

The model learns which food tends to be served for a given weekday and meal
(breakfast / lunch / dinner). The old version used day, month and *year* as
features, which can't generalise to future dates.
"""

import datetime as dt
import io
from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

MEALS = ("breakfast", "lunch", "dinner")
MIN_ROWS = 10
MAX_ROWS = 20000


class DataError(ValueError):
    """Bad input; the message is safe to show to the user."""


@dataclass(frozen=True)
class Meal:
    date: dt.date
    meal: str
    food: str

    def as_json(self) -> dict:
        return {"date": self.date.isoformat(), "meal": self.meal, "food": self.food}


def normalize_meal(value) -> str:
    text = str(value).strip().lower()
    for meal in MEALS:
        if text and meal.startswith(text[:3]):  # "break", "Lunch", "din" ...
            return meal
    raise DataError(f"Unknown meal '{value}'. Use breakfast, lunch or dinner.")


def parse_date(value) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value).strip()[:10])
    except ValueError as exc:
        raise DataError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc


def parse_table(data: bytes, filename: str) -> list[Meal]:
    """Reads a .csv/.xlsx with columns Day, Month, Year, Time, Food
    (or Date, Time, Food)."""
    name = (filename or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(data))
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(data))
        else:
            raise DataError("Upload a .csv or .xlsx file.")
    except DataError:
        raise
    except Exception as exc:
        raise DataError("Couldn't read that file. Is it a valid spreadsheet?") from exc

    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.dropna(how="all")
    if len(df) > MAX_ROWS:
        raise DataError(f"Too many rows (max {MAX_ROWS}).")
    if not {"time", "food"} <= set(df.columns):
        raise DataError("The file needs Time and Food columns (see the help page).")

    meals = []
    for i, row in enumerate(df.to_dict("records"), start=2):
        try:
            if "date" in row and pd.notna(row["date"]):
                date = parse_date(row["date"])
            else:
                date = dt.date(int(row["year"]), int(row["month"]), int(row["day"]))
            meals.append(Meal(date, normalize_meal(row["time"]), str(row["food"]).strip()))
        except (KeyError, ValueError, TypeError) as exc:
            raise DataError(f"Row {i}: needs a valid date (Day/Month/Year or Date), meal and food.") from exc
    return meals


def meals_from_json(items) -> list[Meal]:
    if not isinstance(items, list) or len(items) > MAX_ROWS:
        raise DataError("Invalid history.")
    meals = []
    for item in items:
        if not isinstance(item, dict) or not str(item.get("food", "")).strip():
            raise DataError("Every history row needs a food.")
        meals.append(Meal(parse_date(item.get("date")), normalize_meal(item.get("meal")),
                          str(item["food"]).strip()[:100]))
    return meals


def features(date: dt.date, meal: str) -> list[int]:
    return [date.weekday(), MEALS.index(meal)]


def predict(history: list[Meal], date: dt.date, meal: str, top: int = 3) -> list[tuple[str, float]]:
    """Most likely foods for `meal` on `date`, with probabilities."""
    if len(history) < MIN_ROWS:
        raise DataError(f"Add at least {MIN_ROWS} meals to your history (you have {len(history)}).")
    foods = [m.food for m in history]
    if len(set(foods)) == 1:
        return [(foods[0], 1.0)]
    model = RandomForestClassifier(n_estimators=200, random_state=0)
    model.fit([features(m.date, m.meal) for m in history], foods)
    probabilities = model.predict_proba([features(date, meal)])[0]
    ranked = sorted(zip(model.classes_, probabilities), key=lambda pair: -pair[1])
    return [(str(food), round(float(p), 3)) for food, p in ranked[:top] if p > 0]
