# SunIQ

SunIQ is a smart solar-energy system with a Flask web dashboard and Arduino firmware. It will use solar-panel measurements and simple predictions to help small off-grid systems decide when to run a load, conserve power, or charge a battery.

## Project goal

SunIQ helps small off-grid solar systems use energy wisely by extending useful battery operating time. It does this by measuring solar power, tracking historical readings, and recommending when to run or conserve energy-consuming loads.

## Project structure

```text
app.py                 Flask application
prediction.py          Short-term power prediction and error calculation
capture_ina219.py       Save Arduino serial readings as new CSV sessions
templates/             Dashboard HTML templates
static/                Dashboard styles and future JavaScript
firmware/              Arduino sketch and wiring instructions
data/                  Recorded solar measurements
```

## Run locally

SunIQ requires Python 3.9 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Capture new INA219 readings

After uploading the Arduino sketch, close Arduino IDE's Serial Monitor. In a separate terminal, find the Uno port with `python -m serial.tools.list_ports`, then run a capture (replace `COM3` with your port):

```powershell
python capture_ina219.py --port COM3 --scenario sun --orientation "fixed facing sun" --max-readings 20
```

The program saves each valid reading to a new CSV in `data/measurements/`. Use a different scenario such as `"hand shade"` for another condition. Omit `--max-readings` to keep recording until Ctrl+C. Open `http://127.0.0.1:5000/?live=1` to refresh the dashboard every ten seconds. The next-reading prediction is calculated from each saved session after at least three readings. The capture program and Arduino Serial Monitor cannot use the same port at the same time.

The dashboard shows the last `captured_at` computer clock time. Its plot can show all readings, the last 5 or 15 minutes, the last hour, or a custom From/To time. Recent ranges are measured back from the latest saved reading. The older hand-pasted INA219 sessions have Arduino `timestamp_ms` values but no clock timestamps, so they appear only with All sessions.
