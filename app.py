import csv
from pathlib import Path

from flask import Flask, render_template, request


DATA_DIR = Path(__file__).parent / "data" / "measurements"


def load_measurements():
    data_files = sorted(DATA_DIR.glob("solar-readings-*.csv"))
    if not data_files:
        return []
    with data_files[-1].open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))



def simulate(args):
    """Illustrative constant-power model, independent of measured CSV data."""
    import math

    def bounded(name, default, minimum, maximum):
        try:
            value = float(args.get(name, default))
        except (ValueError, TypeError):
            return default
        return max(minimum, min(maximum, value)) if math.isfinite(value) else default

    sunlight = bounded('sunlight', 80, 0, 100)
    battery = bounded('battery', 60, 0, 100)
    hours = bounded('hours', 2, 0, 24)
    trend = args.get('trend', 'steady')
    if trend not in ('steady', 'falling'):
        trend = 'steady'
    # Illustrative 6 V source and 5 mA maximum current, not a panel rating.
    voltage = 6.0
    current = 0.005 * sunlight / 100
    power = voltage * current
    if battery < 20:
        action, reason = 'Conserve energy', 'Battery is below 20%; prioritize restoring its reserve.'
    elif trend == 'falling':
        action, reason = 'Conserve energy', 'Sunlight is falling; reduce demand before generation drops.'
    elif sunlight < 30:
        action, reason = 'Conserve energy', 'Sunlight is below 30%; available generation is low.'
    elif sunlight >= 70 and battery >= 50:
        action, reason = 'Run load', 'Sunlight is at least 70% and battery is at least 50%.'
    elif battery < 90:
        action, reason = 'Charge battery', 'Some sunlight is available; prioritize charging before optional loads.'
    else:
        action, reason = 'Conserve energy', 'Battery is well charged, but sunlight is below the run-load threshold.'
    return dict(sunlight=sunlight, battery=battery, hours=hours, trend=trend,
                voltage=voltage, current=current, power=power, energy=power*hours,
                action=action, reason=reason)


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        return render_template("index.html", measurements=load_measurements(), simulation=simulate(request.args))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
