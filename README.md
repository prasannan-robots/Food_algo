# FoodAlgo 🍽️

Predict your next meal from your meal history. FoodAlgo trains a random-forest model on what
was served for each weekday and meal (breakfast / lunch / dinner) and shows the most likely
foods for any upcoming date, with confidence.

- Add meals by hand, upload a `.csv` / `.xlsx` (`Day, Month, Year, Time, Food` or
  `Date, Time, Food`), or try the bundled sample.
- Your history stays in your browser (localStorage); the server is stateless.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py              # http://127.0.0.1:5000
pip install pytest && pytest
```

Production: `gunicorn app:app` (see `Procfile`). Set `SECRET_KEY` in the environment.
