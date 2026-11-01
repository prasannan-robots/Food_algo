"""FoodAlgo: predict your next meal from your meal history.

Stateless JSON API: the browser keeps the history and sends it with each
prediction, so nothing is stored on the server.
"""

from flask import Blueprint, jsonify, render_template, request

from .predictor import MIN_ROWS, DataError, meals_from_json, normalize_meal, parse_date, parse_table, predict

view = Blueprint("view", __name__)


@view.get("/")
def home():
    return render_template("home.html", min_rows=MIN_ROWS)


@view.get("/more")
def more():
    return render_template("more.html", min_rows=MIN_ROWS)


@view.post("/api/parse")
def parse():
    upload = request.files.get("history")
    if not upload or not upload.filename:
        return jsonify(error="Choose a .csv or .xlsx file."), 400
    try:
        meals = parse_table(upload.read(), upload.filename)
    except DataError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(rows=[m.as_json() for m in meals])


@view.post("/api/predict")
def predict_meal():
    body = request.get_json(silent=True) or {}
    try:
        history = meals_from_json(body.get("history"))
        predictions = predict(history, parse_date(body.get("date")), normalize_meal(body.get("meal", "")))
    except DataError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(
        predictions=[{"food": food, "probability": p} for food, p in predictions],
        trained_on=len(history),
    )


@view.app_errorhandler(413)
def too_large(_error):
    return jsonify(error="That file is too large (max 5 MB)."), 413
