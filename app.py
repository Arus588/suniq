import csv
from pathlib import Path

from flask import Flask, render_template


DATA_DIR = Path(__file__).parent / "data" / "measurements"


def load_measurements():
    data_files = sorted(DATA_DIR.glob("solar-readings-*.csv"))
    if not data_files:
        return []
    with data_files[-1].open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        return render_template("index.html", measurements=load_measurements())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
