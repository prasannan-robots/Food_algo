import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web import create_app  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "assets", "sample.csv")


def test_parse_then_predict_roundtrip():
    c = create_app().test_client()
    with open(SAMPLE, "rb") as f:
        parsed = c.post("/api/parse", data={"history": (f, "sample.csv")}, content_type="multipart/form-data")
    assert parsed.status_code == 200
    rows = parsed.get_json()["rows"]
    assert len(rows) == 84
    # The sample serves chicken biryani every Sunday lunch.
    res = c.post("/api/predict", json={"history": rows, "date": "2027-01-03", "meal": "lunch"})
    body = res.get_json()
    assert res.status_code == 200, body
    assert body["predictions"][0]["food"] == "chicken biryani"
    assert body["trained_on"] == 84


def test_errors_are_json_400s():
    c = create_app().test_client()
    assert c.post("/api/parse", data={}, content_type="multipart/form-data").status_code == 400
    r = c.post("/api/predict", json={"history": [], "date": "2027-01-03", "meal": "lunch"})
    assert r.status_code == 400 and "at least" in r.get_json()["error"]
    assert c.post("/api/predict", data="garbage").status_code == 400
    assert c.get("/").status_code == 200 and c.get("/more").status_code == 200
