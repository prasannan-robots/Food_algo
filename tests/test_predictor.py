import datetime as dt
import io
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.predictor import DataError, Meal, meals_from_json, normalize_meal, parse_table, predict  # noqa: E402


def weekly_history(weeks=4):
    # Every Monday lunch is biryani, every other lunch is rice; dinners are idly.
    start = dt.date(2026, 1, 5)  # a Monday
    rows = []
    for d in range(weeks * 7):
        day = start + dt.timedelta(days=d)
        rows.append(Meal(day, "lunch", "biryani" if day.weekday() == 0 else "rice"))
        rows.append(Meal(day, "dinner", "idly"))
    return rows


def test_learns_weekday_patterns_for_future_dates():
    history = weekly_history()
    next_monday = dt.date(2027, 3, 1)  # a Monday in a year never seen in training
    assert predict(history, next_monday, "lunch")[0][0] == "biryani"
    assert predict(history, next_monday + dt.timedelta(days=1), "lunch")[0][0] == "rice"
    food, probability = predict(history, next_monday, "dinner")[0]
    assert food == "idly" and probability > 0.9


def test_requires_minimum_history():
    try:
        predict(weekly_history()[:5], dt.date.today(), "lunch")
    except DataError as exc:
        assert "at least 10" in str(exc)
    else:
        raise AssertionError("accepted tiny history")


def test_parse_xlsx_day_month_year_format():
    buf = io.BytesIO()
    pd.DataFrame({"Day": [17, 17], "Month": [4, 4], "Year": [2019, 2019],
                  "Time": ["breakfast", "Lunch"], "Food": ["dosa", "rice"]}).to_excel(buf, index=False)
    meals = parse_table(buf.getvalue(), "history.xlsx")  # .xlsx used to always fail
    assert meals == [Meal(dt.date(2019, 4, 17), "breakfast", "dosa"), Meal(dt.date(2019, 4, 17), "lunch", "rice")]


def test_parse_csv_with_date_column_and_bad_rows():
    meals = parse_table(b"Date,Time,Food\n2026-01-05,din,idly\n", "h.csv")
    assert meals[0].meal == "dinner"
    for bad in [b"Food\nrice\n", b"Date,Time,Food\nnope,lunch,rice\n"]:
        try:
            parse_table(bad, "h.csv")
        except DataError:
            continue
        raise AssertionError(bad)


def test_json_validation_and_meal_names():
    assert meals_from_json([{"date": "2026-01-05", "meal": "Break", "food": "dosa"}])[0].meal == "breakfast"
    assert normalize_meal("LUNCH") == "lunch"
    for bad in [{"date": "x", "meal": "lunch", "food": "a"}, {"date": "2026-01-05", "meal": "snack", "food": "a"},
                {"date": "2026-01-05", "meal": "lunch", "food": ""}]:
        try:
            meals_from_json([bad])
        except DataError:
            continue
        raise AssertionError(bad)
