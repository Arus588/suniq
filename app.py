import csv
import math
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request
from prediction import predict_next_power


DATA_DIR = Path(__file__).parent / "data" / "measurements"


def load_measurements():
    data_files = sorted(DATA_DIR.glob("solar-readings-*.csv"))
    if not data_files:
        return []
    with data_files[-1].open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def load_ina219_sessions():
    def valid(row):
        try:
            return (int(row["timestamp_ms"]) >= 0 and
                    all(math.isfinite(float(row[field])) for field in
                        ("bus_voltage_v", "current_ma", "power_mw")))
        except (KeyError, TypeError, ValueError):
            return False

    sessions = []
    legacy = [DATA_DIR / name for name in (
        "ina219-sun-2026-10-04.csv", "ina219-hand-shade-2026-10-04.csv"
    )]
    capture_files = sorted(DATA_DIR.glob("ina219-capture-*.csv"))
    for path in [*legacy, *capture_files]:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            rows = [row for row in csv.DictReader(csv_file) if valid(row)]
        if not rows:
            continue
        label = ("Sun facing" if path == legacy[0] else
                 "Covered by hand" if path == legacy[1] else
                 rows[0].get("scenario", "New capture").replace("-", " ").title())
        power_values = [float(row["power_mw"]) for row in rows]
        sessions.append({
            "label": label,
            "filename": path.name,
            "captured_at": rows[0].get("captured_at", ""),
            "last_captured_at": rows[-1].get("captured_at", ""),
            "count": len(rows),
            "voltage": sum(float(row["bus_voltage_v"]) for row in rows) / len(rows),
            "current": sum(float(row["current_ma"]) for row in rows) / len(rows),
            "power": sum(power_values) / len(rows),
            "prediction": predict_next_power(power_values),
            "rows": rows,
        })
    return sessions


def plot_data_for_range(sessions, lookback="all", start="", end=""):
    """Return plot rows in a selected clock-time range and the last capture time."""
    dated_rows = []
    for session in sessions:
        for row in session["rows"]:
            try:
                dated_rows.append(datetime.fromisoformat(row["captured_at"]))
            except (KeyError, TypeError, ValueError):
                pass
    latest = max(dated_rows) if dated_rows else None

    lower = upper = None
    if lookback in {"5m", "15m", "1h"} and latest:
        lower = latest - {"5m": timedelta(minutes=5),
                          "15m": timedelta(minutes=15),
                          "1h": timedelta(hours=1)}[lookback]
        upper = latest
    elif lookback == "custom":
        try:
            lower = datetime.fromisoformat(start).astimezone() if start else None
            upper = datetime.fromisoformat(end).astimezone() if end else None
        except ValueError:
            lower = upper = None

    plot_sessions = []
    for session in sessions:
        history = session["prediction"]["history_mw"] if session["prediction"] else []
        rows = []
        for index, row in enumerate(session["rows"]):
            if lookback != "all":
                try:
                    captured = datetime.fromisoformat(row["captured_at"])
                except (KeyError, TypeError, ValueError):
                    continue
                if (lower and captured < lower) or (upper and captured > upper):
                    continue
            rows.append({"power_mw": row["power_mw"],
                         "captured_at": row.get("captured_at", ""),
                         "predicted_mw": history[index] if history else None})
        if rows:
            plot_sessions.append({"label": session["label"], "filename": session["filename"],
                                  "rows": rows})
    return plot_sessions, latest



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
        sessions = load_ina219_sessions()
        lookback = request.args.get("lookback", "all")
        if lookback not in {"all", "5m", "15m", "1h", "custom"}:
            lookback = "all"
        start, end = request.args.get("start", ""), request.args.get("end", "")
        plot_sessions, latest_capture = plot_data_for_range(sessions, lookback, start, end)
        return render_template("index.html", measurements=load_measurements(),
                               ina219_sessions=sessions, plot_sessions=plot_sessions,
                               latest_capture=latest_capture, lookback=lookback,
                               range_start=start, range_end=end,
                               auto_refresh=request.args.get("live") == "1",
                               simulation=simulate(request.args))

    @app.get("/data")
    def data_page():
        return render_template("data.html", measurements=load_measurements(),
                               ina219_sessions=load_ina219_sessions())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
